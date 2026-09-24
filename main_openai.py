"""
=============================================================================
main_openai.py  –  ARC VT LLM Chat with Document/URL Grounding
=============================================================================
Allows the user to:
  1. Upload one or more local files (PDF, TXT, DOCX, MD, HTML…)
     OR paste a public URL (web page or remote PDF)
  2. All content is extracted and cached locally in openai_doc_cache.json
  3. An interactive Q&A chat loop gives the LLM full access to the cached
     content via the system prompt (closed-source grounding)

API:  ARC VT OpenAI-compatible endpoint  https://llm-api.arc.vt.edu/api/v1/
Key:  ARC_API_KEY in .env  (falls back to OPENAI_API_KEY)
=============================================================================
"""
import os
import re
import sys
import json
import io
import hashlib
import time
from html import unescape
from datetime import datetime

# ---------------------------------------------------------------------------
# Reconfigure stdout for clean UTF-8 on Windows
# ---------------------------------------------------------------------------
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE  = os.path.join(BASE_DIR, "openai_doc_cache.json")
STATE_FILE  = os.path.join(BASE_DIR, "openai_session.json")

# ---------------------------------------------------------------------------
# Load .env  (ARC_API_KEY or OPENAI_API_KEY)
# ---------------------------------------------------------------------------
_env_path = os.path.join(BASE_DIR, ".env")
if not os.path.exists(_env_path):
    _env_path = os.path.join(BASE_DIR, "env")   # fallback: no-dot variant
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and "=" in _line and not _line.startswith("#"):
                _k, _, _v = _line.partition("=")
                _v = _v.strip().strip('"').strip("'")
                os.environ.setdefault(_k.strip(), _v)
                os.environ.setdefault(_k.strip().replace("-", "_"), _v)

API_KEY  = (os.environ.get("ARC_API_KEY")
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or "")
API_BASE = "https://llm-api.arc.vt.edu/api/v1"
MODEL    = os.environ.get("ARC_MODEL", "gpt-oss-120b")

# ---------------------------------------------------------------------------
# Optional dependencies
# ---------------------------------------------------------------------------
try:
    import requests as _req
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    import urllib.request as _urllib_req

# PDF support: prefer pypdf, fall back to PyPDF2
HAS_PYPDF = False
try:
    import pypdf
    HAS_PYPDF = True
    _PDF_LIB = f"pypdf {getattr(pypdf, '__version__', '')}".strip()
except ImportError:
    try:
        import PyPDF2 as pypdf          # type: ignore
        HAS_PYPDF = True
        _PDF_LIB = f"PyPDF2 {getattr(pypdf, '__version__', '')}".strip()
    except ImportError:
        _PDF_LIB = "none"

# DOCX support
HAS_DOCX = False
try:
    import docx as _docx
    HAS_DOCX = True
except ImportError:
    pass

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

MAX_CHARS = 40_000   # per-document context cap


def _http_get(url: str, timeout: int = 15):
    if HAS_REQUESTS:
        try:
            return _req.get(url, headers=_HEADERS, timeout=(4.0, timeout))
        except Exception as e:
            print(f"    [!] HTTP error: {e}")
            return None
    else:
        try:
            req = _urllib_req.Request(url, headers=_HEADERS)
            with _urllib_req.urlopen(req, timeout=timeout) as r:
                class _Resp:
                    status_code = r.status
                    content = r.read()
                    headers = dict(r.headers)
                return _Resp()
        except Exception as e:
            print(f"    [!] HTTP error: {e}")
            return None


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _extract_pdf_bytes(data: bytes) -> str:
    if not HAS_PYPDF:
        return ""
    try:
        reader = pypdf.PdfReader(io.BytesIO(data))
        pages = []
        for i in range(min(len(reader.pages), 50)):
            t = reader.pages[i].extract_text() or ""
            c = re.sub(r"[ \t]+", " ", t).strip()
            if c:
                pages.append(c)
        return "\n\n".join(pages)
    except Exception:
        return ""


def _extract_pdf_file(path: str) -> str:
    if not HAS_PYPDF:
        return ""
    try:
        reader = pypdf.PdfReader(path)
        pages = []
        for i in range(min(len(reader.pages), 50)):
            t = reader.pages[i].extract_text() or ""
            c = re.sub(r"[ \t]+", " ", t).strip()
            if c:
                pages.append(c)
        return "\n\n".join(pages)
    except Exception:
        return ""


def _extract_docx_file(path: str) -> str:
    if not HAS_DOCX:
        return ""
    try:
        doc = _docx.Document(path)
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return ""


def _clean_html(html: str) -> str:
    """Strip HTML tags and return readable plain text."""
    html = re.sub(
        r"<(script|style|svg|noscript|nav|footer|header|aside).*?</\1>",
        "", html, flags=re.DOTALL | re.IGNORECASE,
    )
    elements = re.findall(
        r"<(p|li|h[1-6]|td|th)[^>]*>(.*?)</\1>",
        html, flags=re.DOTALL | re.IGNORECASE,
    )
    parts = []
    for _, inner in elements:
        c = re.sub(r"<[^>]+>", " ", inner)
        c = re.sub(r"\s+", " ", unescape(c)).strip()
        if len(c) > 25:
            parts.append(c)
    if not parts:
        raw = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", unescape(raw)).strip()[:MAX_CHARS]
    return "\n\n".join(parts)[:MAX_CHARS]


# ---------------------------------------------------------------------------
# Main extraction dispatcher
# ---------------------------------------------------------------------------

def extract_from_file(path: str) -> str:
    """Extract text from a local file path."""
    if not os.path.isfile(path):
        print(f"  [!] File not found: {path}")
        return ""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        if not HAS_PYPDF:
            print("  [!] PDF parsing unavailable – install pypdf:  pip install pypdf")
            return ""
        text = _extract_pdf_file(path)
        if not text:
            print("  [!] Could not extract text from PDF.")
        return text[:MAX_CHARS]
    if ext == ".docx":
        if not HAS_DOCX:
            print("  [!] DOCX parsing unavailable – install python-docx:  pip install python-docx")
            return ""
        return _extract_docx_file(path)[:MAX_CHARS]
    if ext in (".html", ".htm"):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return _clean_html(f.read())
    # Plain text (txt, md, csv, json, py, etc.)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()[:MAX_CHARS]
    except Exception as e:
        print(f"  [!] Could not read file: {e}")
        return ""


def extract_from_url(url: str) -> str:
    """Download and extract text from a URL (web page or remote PDF)."""
    print(f"  Fetching: {url}")
    resp = _http_get(url)
    if resp is None:
        return ""
    if resp.status_code != 200:
        print(f"  [!] HTTP {resp.status_code}")
        return ""

    ct = ""
    if hasattr(resp, "headers"):
        h = resp.headers
        ct = (h.get("Content-Type") or h.get("content-type") or "").lower()

    raw_bytes = getattr(resp, "content", b"")
    is_pdf = (
        "application/pdf" in ct
        or url.lower().split("?")[0].endswith(".pdf")
        or (isinstance(raw_bytes, bytes) and raw_bytes.startswith(b"%PDF"))
    )
    if is_pdf:
        if not HAS_PYPDF:
            print("  [!] PDF parsing unavailable – install pypdf:  pip install pypdf")
            return ""
        text = _extract_pdf_bytes(raw_bytes)
        return text[:MAX_CHARS]

    # HTML / plain text
    html = raw_bytes.decode("utf-8", errors="replace") if isinstance(raw_bytes, bytes) else getattr(resp, "text", "")
    return _clean_html(html)


# ---------------------------------------------------------------------------
# Cache management
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def _load_state() -> list:
    """Return the persisted list of active cache keys, or [] if none saved."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_docs", [])
        except Exception:
            pass
    return []


def _save_state(active_docs: list):
    """Persist the current active_docs list to disk."""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"active_docs": active_docs}, f, indent=2)


def _cache_key(source: str) -> str:
    """Stable key: label + short MD5 hash of the source path/URL."""
    h = hashlib.md5(source.encode()).hexdigest()[:8]
    label = os.path.basename(source.rstrip("/"))[:40]
    return f"{label}__{h}"


def add_source(source: str, cache: dict) -> tuple:
    """
    Add a file path or URL to the cache.
    Returns (cache_key, text, already_cached: bool).
    """
    key = _cache_key(source)
    if key in cache:
        entry = cache[key]
        print(f"  [Cache HIT] '{entry['label']}' already cached "
              f"({len(entry['text']):,} chars, added {entry.get('added', '?')})")
        return key, entry["text"], True

    # Fresh extraction
    if source.startswith("http://") or source.startswith("https://"):
        text = extract_from_url(source)
    else:
        text = extract_from_file(source)

    if not text:
        return key, "", False

    cache[key] = {
        "label":  os.path.basename(source.rstrip("/")) or source,
        "source": source,
        "text":   text,
        "chars":  len(text),
        "added":  datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    _save_cache(cache)
    print(f"  [Cached] '{cache[key]['label']}' – {len(text):,} characters")
    return key, text, False


def list_cache(cache: dict):
    if not cache:
        print("  (cache is empty)")
        return
    print(f"\n  {'#':<4} {'Label':<40} {'Chars':>8}  Added")
    print("  " + "-" * 70)
    for i, (k, v) in enumerate(cache.items(), 1):
        print(f"  {i:<4} {v['label']:<40} {v['chars']:>8,}  {v.get('added','?')}")


# ---------------------------------------------------------------------------
# LLM call via ARC VT OpenAI-compatible API
# ---------------------------------------------------------------------------

def build_system_prompt(active_docs: list, cache: dict) -> str:
    docs_text = ""
    for key in active_docs:
        entry = cache.get(key)
        if not entry:
            continue
        docs_text += f"\n\n--- DOCUMENT: {entry['label']} ---\n"
        docs_text += entry["text"]

    return (
        "You are a document-grounding assistant. "
        "You MUST answer ONLY using information explicitly stated in the documents below.\n"
        "STRICT RULES – you must follow ALL of these without exception:\n"
        "  1. Do NOT use any knowledge from your training data or the internet.\n"
        "  2. Do NOT infer, guess, or extrapolate beyond what the documents state.\n"
        "  3. If the documents do not contain the answer, respond ONLY with: "
           "'The provided documents do not contain information about this topic.'\n"
        "  4. Always cite which document (by name) your answer comes from.\n"
        "  5. Partial answers are allowed only if explicitly supported by the documents.\n\n"
        "=== PROVIDED DOCUMENTS ===\n"
        + docs_text.strip()
        + "\n\n=== END OF DOCUMENTS ===\n"
        "Remember: your ONLY source of truth is the text above. "
        "Do not supplement with outside knowledge under any circumstances."
    )


def build_verify_prompt(active_docs: list, cache: dict) -> str:
    """System prompt for content verification mode."""
    docs_text = ""
    for key in active_docs:
        entry = cache.get(key)
        if not entry:
            continue
        docs_text += f"\n\n--- DOCUMENT: {entry['label']} ---\n"
        docs_text += entry["text"]

    return (
        "You are a strict content verification assistant.\n"
        "The user will provide a statement. Your ONLY job is to determine whether "
        "that statement is supported, contradicted, or not addressed by the documents below.\n\n"
        "RULES:\n"
        "  1. Base your verdict SOLELY on text found in the provided documents.\n"
        "  2. Do NOT use any external knowledge or training data.\n"
        "  3. You MUST respond using EXACTLY this format – no exceptions:\n\n"
        "     VERDICT: <VERIFIED | CONTRADICTED | UNVERIFIABLE>\n"
        "     CONFIDENCE: <HIGH | MEDIUM | LOW>\n"
        "     SOURCE: <document name(s) used>\n"
        "     EVIDENCE: <exact quote or close paraphrase from the document that supports the verdict>\n"
        "     EXPLANATION: <one or two sentences explaining the verdict>\n\n"
        "  Verdict definitions:\n"
        "    VERIFIED      – The document(s) explicitly support the statement.\n"
        "    CONTRADICTED  – The document(s) explicitly contradict the statement.\n"
        "    UNVERIFIABLE  – The document(s) do not contain enough information to judge.\n\n"
        "=== PROVIDED DOCUMENTS ===\n"
        + docs_text.strip()
        + "\n\n=== END OF DOCUMENTS ===\n"
        "Now await the user's statement and apply the format above precisely."
    )


def chat_completion(messages: list, system_prompt: str) -> str:
    if not API_KEY:
        return (
            "[Error] No API key found. "
            "Add ARC_API_KEY=<your_key> to your .env file."
        )

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": 0.2,
        "max_tokens": 2048,
        "stream": False,
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        if HAS_REQUESTS:
            resp = _req.post(
                f"{API_BASE}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            if resp.status_code != 200:
                return f"[API Error {resp.status_code}] {resp.text[:400]}"
            data = resp.json()
        else:
            body = json.dumps(payload).encode()
            req = _urllib_req.Request(
                f"{API_BASE}/chat/completions",
                data=body, headers=headers, method="POST",
            )
            with _urllib_req.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        return f"[Request failed] {e}"


# ---------------------------------------------------------------------------
# Interactive CLI
# ---------------------------------------------------------------------------
_HELP = """
Commands:
  add <path|url>   Add a local file or URL to the cache and activate it
  list             List all cached documents
  use <number>     Toggle a cached doc in/out of active context (by # from list)
  clear            Clear active documents + conversation history (cache kept on disk)
  purge            Delete ALL cached documents from disk and memory
  info             Show which documents are currently active in context
  verifymode       Toggle Content Verification Mode on/off
  verify <stmt>    Verify a single statement against active documents (one-shot)
  help / ?         Show this help
  quit / exit      Exit

  <anything else>  In Q&A mode: ask the LLM a question
                   In Verify mode: treat input as a statement to verify
"""


def _hr(char="=", n=62):
    print(char * n)


def main():
    _hr()
    print("  ARC VT LLM  -  Document-Grounded Q&A")
    print(f"  Model : {MODEL}")
    print(f"  API   : {API_BASE}")
    print(f"  PDF   : {_PDF_LIB}  |  DOCX: {'yes' if HAS_DOCX else 'no'}")
    if not API_KEY:
        print("  [!] WARNING: ARC_API_KEY not set – add it to .env")
    _hr()
    print("  Type 'help' for commands, or 'add <file/url>' to load a document.")
    _hr()

    cache: dict       = _load_cache()
    history: list     = []   # conversation history (list of role/content dicts)
    verify_mode: bool = False  # Content Verification Mode toggle

    # Restore previously active documents (filter out any that were purged)
    _saved_keys = _load_state()
    active_docs: list = [k for k in _saved_keys if k in cache]

    if cache:
        print(f"\n  [Cache] Found {len(cache)} previously cached document(s).")
        if active_docs:
            labels = [cache[k]["label"] for k in active_docs]
            print(f"  [Session] Restored {len(active_docs)} active document(s): {', '.join(labels)}")
        else:
            print("  Use 'list' to see them, 'use <#>' to activate one.")
        print()

    def _prompt_prefix() -> str:
        return "  [VERIFY] You" if verify_mode else " You"

    while True:
        try:
            raw = input(f"\n{_prompt_prefix()}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nExiting.")
            break

        if not raw:
            continue

        cmd = raw.lower()

        # ---- help ----
        if cmd in ("help", "?", "h"):
            print(_HELP)
            continue

        # ---- quit ----
        if cmd in ("quit", "exit", "q"):
            print("Bye!")
            break

        # ---- add ----
        if cmd.startswith("add ") or cmd.startswith("add\t"):
            source = raw[4:].strip().strip('"').strip("'")
            if not source:
                print("  Usage:  add <file_path_or_url>")
                continue
            print(f"\n  Loading: {source}")
            key, text, was_cached = add_source(source, cache)
            if text:
                if key not in active_docs:
                    active_docs.append(key)
                _save_state(active_docs)
                status = "already cached, now active" if was_cached else "cached and activated"
                print(f"  [{status}]  –  context now has {len(active_docs)} document(s)")
            else:
                print("  [!] No content could be extracted – check the path/URL.")
            continue

        # ---- list ----
        if cmd in ("list", "ls", "docs"):
            list_cache(cache)
            if active_docs:
                labels = [cache[k]["label"] for k in active_docs if k in cache]
                print(f"\n  Active: {', '.join(labels)}")
            continue

        # ---- use <number> ----
        if cmd.startswith("use ") or cmd.startswith("use\t"):
            arg = raw[4:].strip()
            try:
                idx = int(arg) - 1
                key = list(cache.keys())[idx]
            except (ValueError, IndexError):
                print("  [!] Invalid number. Use 'list' to see available documents.")
                continue
            if key in active_docs:
                active_docs.remove(key)
                print(f"  Deactivated: {cache[key]['label']}")
            else:
                active_docs.append(key)
                print(f"  Activated: {cache[key]['label']}")
            _save_state(active_docs)
            continue

        # ---- info ----
        if cmd in ("info", "status", "active"):
            if not active_docs:
                print("  No documents active. Use 'add <file|url>' or 'use <#>'.")
            else:
                total = sum(len(cache[k]["text"]) for k in active_docs if k in cache)
                print(f"  Active documents ({len(active_docs)}, {total:,} chars in LLM context):")
                for k in active_docs:
                    e = cache.get(k, {})
                    print(f"    - {e.get('label','?')}  ({e.get('chars',0):,} chars)")
            continue

        # ---- clear ----
        if cmd in ("clear", "reset"):
            active_docs.clear()
            history.clear()
            _save_state(active_docs)
            print("  Active documents and conversation history cleared (cache kept).")
            continue

        # ---- purge ----
        if cmd in ("purge",):
            confirm = input("  Delete ALL cached documents? (yes/no): ").strip().lower()
            if confirm == "yes":
                cache.clear()
                active_docs.clear()
                history.clear()
                if os.path.exists(CACHE_FILE):
                    os.remove(CACHE_FILE)
                if os.path.exists(STATE_FILE):
                    os.remove(STATE_FILE)
                print("  Cache purged.")
            else:
                print("  Cancelled.")
            continue

        # ---- verifymode toggle ----
        if cmd == "verifymode":
            verify_mode = not verify_mode
            if verify_mode:
                print(
                    "\n  [Content Verification Mode: ON]\n"
                    "  Enter any statement and the LLM will verdict it against your active documents.\n"
                    "  Type 'verifymode' again to return to Q&A mode."
                )
            else:
                history.clear()   # clear verify history when switching back
                print("  [Content Verification Mode: OFF]  Back to Q&A mode.")
            continue

        # ---- verify <statement>  (one-shot, doesn't change mode) ----
        if cmd.startswith("verify ") or cmd.startswith("verify\t"):
            statement = raw[7:].strip()
            if not statement:
                print("  Usage:  verify <statement to check>")
                continue
            if not API_KEY:
                print(
                    "\n  [Error] No API key set.\n"
                    "  Add  ARC_API_KEY=<your_key>  to your .env file and restart."
                )
                continue
            if not active_docs:
                print(
                    "\n  [Blocked] No documents are active.\n"
                    "  Load a document first with 'add <file|url>' or 'use <#>'."
                )
                continue
            print("\n  [Verifying...]")
            t0 = time.time()
            verdict = chat_completion(
                [{"role": "user", "content": statement}],
                build_verify_prompt(active_docs, cache),
            )
            elapsed = time.time() - t0
            _hr("-")
            print(f"  Verification Result ({elapsed:.1f}s):\n")
            print(verdict)
            _hr("-")
            continue

        # ---- LLM Q&A ----
        if not API_KEY:
            print(
                "\n  [Error] No API key set.\n"
                "  Add  ARC_API_KEY=<your_key>  to your .env file and restart."
            )
            continue

        # Block queries when no documents are loaded
        if not active_docs:
            print(
                "\n  [Blocked] No documents are active.\n"
                "  This assistant is restricted to document content only.\n"
                "  Use 'add <file|url>' to load a document, or 'use <#>' to activate a cached one."
            )
            continue

        # ---- Route to verify or Q&A ----
        if verify_mode:
            # In verification mode: treat every input as a statement to verdict
            print("\n  [Verifying...]")
            t0 = time.time()
            reply = chat_completion(
                [{"role": "user", "content": raw}],
                build_verify_prompt(active_docs, cache),
            )
            elapsed = time.time() - t0
            _hr("-")
            print(f"  Verification Result ({elapsed:.1f}s):\n")
            print(reply)
            _hr("-")
            # Note: history is intentionally NOT updated in verify mode;
            # each statement is evaluated independently against the documents.
        else:
            # Normal Q&A mode
            sys_prompt = build_system_prompt(active_docs, cache)
            history.append({"role": "user", "content": raw})

            print("\n  [Thinking...]")
            t0 = time.time()
            reply = chat_completion(history, sys_prompt)
            elapsed = time.time() - t0

            history.append({"role": "assistant", "content": reply})

            _hr("-")
            print(f" Assistant ({elapsed:.1f}s):\n")
            print(reply)
            _hr("-")

            # Trim history to last 20 turns (40 messages) to avoid token overflow
            if len(history) > 40:
                history = history[-40:]

if __name__ == "__main__":
    main()
