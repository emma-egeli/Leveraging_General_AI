import os
import sys
import time
import json
import re
import logging
import warnings
from html import unescape
import requests

# Suppress SDK warnings and internal logger notices
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

from google import genai
from google.genai import types
from google.genai import errors

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(BASE_DIR, "trusted_sources.json")
CACHE_FILE = os.path.join(BASE_DIR, "sources_cache.json")

# Model Configurations
AVAILABLE_MODELS = ["gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.5-flash", "gemini-3.6-flash"]

# Initialize Gemini Client with fast failover retry configuration (prevents 60s internal SDK hangs)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = "YOUR_API_KEY"

client = genai.Client(
    api_key=api_key,
    http_options=types.HttpOptions(
        retry_options=types.HttpRetryOptions(attempts=1),
        timeout=12000,
    ),
)

_search_grounding_available = True

def fetch_clean_url_text(url: str, timeout: int = 10) -> str:
    """Visits a URL and extracts clean article text (paragraphs, headings, lists)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=(3.0, 5.0))
        if resp.status_code != 200:
            return ""
        html = resp.text
        # Remove scripts, styles, and non-content elements
        html = re.sub(r"<(script|style|svg|noscript|nav|footer|header|aside).*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Extract meaningful blocks: paragraphs, headings, list items
        elements = re.findall(r"<(p|li|h[1-6])[^>]*>(.*?)</\1>", html, flags=re.DOTALL | re.IGNORECASE)
        body_parts = []
        for tag, inner in elements:
            clean = re.sub(r"<[^>]+>", " ", inner)
            clean = re.sub(r"\s+", " ", unescape(clean)).strip()
            if len(clean) > 25:
                body_parts.append(clean)

        if not body_parts:
            clean = re.sub(r"<[^>]+>", " ", html)
            return re.sub(r"\s+", " ", unescape(clean)).strip()[:18000]

        return "\n\n".join(body_parts)[:20000]
    except Exception:
        return ""

# Loading accepted sources from JSON file
def load_trusted_sources(force_refresh: bool = False):
    """Loads trusted sources and enriches them with full live/cached web content."""
    if not os.path.exists(SOURCES_FILE):
        return []

    try:
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            sources = json.load(f)
            if not isinstance(sources, list):
                return []
    except Exception as e:
        print(f"[Notice] Could not load trusted_sources.json: {e}")
        return []

    # Load local cache of extracted text
    cache = {}
    if os.path.exists(CACHE_FILE) and not force_refresh:
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except Exception:
            cache = {}

    updated_cache = False
    for s in sources:
        sid = s.get("id") or s.get("url")
        if sid in cache and not force_refresh:
            s["full_content"] = cache[sid]
        else:
            url = s.get("url")
            if url:
                print(f"[Content Sync] Fetching full article content for: {s.get('title', sid)[:45]}...")
                content = fetch_clean_url_text(url)
                if content:
                    s["full_content"] = content
                    cache[sid] = content
                    updated_cache = True
                else:
                    # Fall back to verified summary and cache it to avoid repeated slow network retries
                    s["full_content"] = s.get("summary", "")
                    cache[sid] = s.get("summary", "")
                    updated_cache = True
            else:
                s["full_content"] = s.get("summary", "")
                cache[sid] = s.get("summary", "")
                updated_cache = True

    if updated_cache:
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
            print("[Content Sync] Successfully cached external source contents.")
        except Exception as e:
            print(f"[Notice] Could not save sources_cache.json: {e}")

    return sources


def call_with_retry(contents: str, config: types.GenerateContentConfig, preferred_model: str = "gemini-3.5-flash-lite", max_retries: int = 1):
    """Executes generate_content with automatic failover across models to prevent 503 delays."""
    models_to_try = [preferred_model] + [m for m in AVAILABLE_MODELS if m != preferred_model]

    for model in models_to_try:
        for attempt in range(max_retries):
            try:
                return client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
            except errors.APIError as err:
                err_str = str(err)
                if err.code in [500, 502, 503, 504] or "UNAVAILABLE" in err_str:
                    print(f"[Notice] Model {model} is experiencing high demand (503). Trying alternative model...")
                    break
                raise
            except Exception as e:
                err_str = str(e)
                if "UNAVAILABLE" in err_str or "503" in err_str:
                    print(f"[Notice] Model {model} busy (503). Trying alternative model...")
                    break
                raise

    raise errors.APIError(503, "All Gemini models are temporarily experiencing high demand.")


def offline_keyword_check(claim: str, sources: list):
    """Zero-token fallback: performs local keyword and semantic matching on cached source content."""
    print("\n" + "=" * 60)
    print("VERIFICATION RESULT (OFFLINE ZERO-TOKEN MODE)")
    print("=" * 60)

    if not sources:
        print("**VERDICT**: UNVERIFIABLE")
        print("\n**EXPLANATION**: No local sources found in trusted_sources.json.")
        print("\n**SOURCES CITED**: None")
        return

    STOPWORDS = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "to", "at", "in", "on",
        "for", "of", "with", "about", "by", "as", "that", "this", "it",
        "and", "or", "but", "not", "so", "from", "you", "your", "they",
        "their", "we", "our", "i", "can", "will", "would", "should", "all",
        "any", "if", "there", "what", "which", "who", "when", "where", "how",
        "more", "than", "most", "also", "into", "over", "after", "make", "made",
        "says", "said", "claim", "claims", "statement", "check", "like", "just"
    }

    words = [w.lower() for w in re.findall(r"\b[a-zA-Z0-9\.\-]{2,}\b", claim)]
    keywords = [w for w in words if w not in STOPWORDS]

    if not keywords:
        print("**VERDICT**: UNVERIFIABLE")
        print("\n**EXPLANATION**: Claim did not contain sufficient distinct keywords for evaluation.")
        print("\n**SOURCES CITED**: None")
        return

    matches = []
    for source in sources:
        full_text = f"{source.get('title', '')} {source.get('full_content', '')} {source.get('summary', '')}".lower()
        matched = [kw for kw in keywords if kw in full_text]
        if matched:
            matches.append((len(matched), matched, source))

    matches.sort(key=lambda x: x[0], reverse=True)

    min_required = 2 if len(keywords) >= 3 else 1

    if not matches or matches[0][0] < min_required:
        matched_str = f" (Weak overlap: {', '.join(matches[0][1])})" if matches else ""
        print("**VERDICT**: UNVERIFIABLE (No significant match in approved sources)")
        print(f"\n**EXPLANATION**: No approved source contained sufficient evidence for keywords: {', '.join(keywords[:5])}.{matched_str}")
        print("\n**SOURCES CITED**: None - Not present in approved sources.")
        return

    best_score, best_keywords, best_source = matches[0]
    content = best_source.get("full_content") or best_source.get("summary", "")
    
    # Extract matching excerpt around the first found keyword
    excerpt = content[:350]
    for kw in best_keywords:
        idx = content.lower().find(kw)
        if idx != -1:
            start = max(0, idx - 80)
            end = min(len(content), idx + 250)
            excerpt = content[start:end].strip()
            break

    print("**VERDICT**: POTENTIALLY VERIFIED (Local Source Match)")
    print(f"\n**KEY EVIDENCE FOUND**:")
    print(f"- Matched Keywords: {', '.join(best_keywords)}")
    print(f"- Source Excerpt: \"...{excerpt}...\"")
    print("\n**SOURCES CITED**:")
    print(f"- [{best_source.get('id', 'N/A')}] {best_source.get('title', 'N/A')}: {best_source.get('url', 'N/A')}")
    print("\n[Zero-Token Notice] Verified locally using cached text indexing without consuming Gemini API tokens.")


def get_multiline_input() -> tuple:
    """Allows the user to enter text in the console.
    Returns (claim_text, mode_flag)."""
    print("\n" + "=" * 60)
    print("Paste or type the claim/information you want to verify.")
    print("Type 'DONE' to verify with Gemini AI.")
    print("Type 'OFFLINE' to verify locally with 0 API tokens.")
    print("Type 'SYNC' to re-fetch/update live web content from URLs.")
    print("=" * 60)

    lines = []
    mode = "AI"
    while True:
        try:
            line = input()
            val = line.strip().upper()
            if val == "DONE":
                break
            if val == "OFFLINE":
                mode = "OFFLINE"
                break
            if val == "SYNC":
                mode = "SYNC"
                break
            lines.append(line)
        except EOFError:
            break

    return "\n".join(lines).strip(), mode


def verify_claim(text_to_verify: str, force_offline: bool = False):
    global _search_grounding_available

    trusted_sources = load_trusted_sources()

    if force_offline:
        offline_keyword_check(text_to_verify, trusted_sources)
        return

    if trusted_sources:
        # Build rich grounding package with the full article content
        grounding_data = []
        for s in trusted_sources:
            content = s.get("full_content") or s.get("summary", "")
            grounding_data.append({
                "id": s.get("id"),
                "title": s.get("title"),
                "url": s.get("url"),
                "domain": s.get("domain"),
                "category": s.get("category"),
                "content": content[:14000]  # Full article text with numbers, dates & facts
            })

        system_instruction = f"""
YOUR ROLE:
You are an objective, strict fact-checking analyst operating under STRICT CLOSED-SOURCE GROUNDING.

YOUR PRIMARY DIRECTIVE:
You must verify the user-provided statement EXCLUSIVELY using the APPROVED EXTERNAL SOURCES list provided below, which contains the full verified content from each source.

APPROVED EXTERNAL SOURCES (WITH VERIFIED ARTICLE CONTENT):
{json.dumps(grounding_data, indent=2)}

CRITICAL VERIFICATION & CITATION RULES:
1. CLOSED-SOURCE BOUNDARY: You are strictly forbidden from relying on outside memory, unverified knowledge, or assumptions. Every factual assertion you make must be directly backed by the APPROVED EXTERNAL SOURCES above.
2. VERDICT REQUIREMENTS:
   - VERIFIED / TRUE: The statement is directly supported and confirmed by the approved sources' content.
   - FALSE / DEBUNKED: The statement is directly contradicted by the approved sources' content.
   - PARTIALLY TRUE / MISLEADING: Part of the statement is supported, but key parts are unsupported or contradicted by the approved sources' content.
   - UNVERIFIABLE: If the statement is NOT directly covered or addressed in the approved sources' content, you MUST classify it as UNVERIFIABLE. State clearly: "This claim is not covered in the provided trusted source list." Do NOT attempt to guess, extrapolate, or verify using outside knowledge.
3. ANTI-HALLUCINATION RULES:
   - NEVER invent, extrapolate, or fabricate any citation, author, journal, or URL.
   - When citing evidence, you must ONLY cite the exact "id", "title", and "url" from the APPROVED EXTERNAL SOURCES above.
   - Quote or reference the specific facts, figures, and data from the "content" field.
4. OUTPUT STRUCTURE:
   - **VERDICT**: [VERIFIED / TRUE | FALSE / DEBUNKED | PARTIALLY TRUE / MISLEADING | UNVERIFIABLE]
   - **EXPLANATION**: Concise explanation quoting or citing the exact figures, dates, and evidence from the source content.
   - **SOURCES CITED**: List exact ID, Title, and URL from the approved list (or "None - Not present in approved sources").
"""
    else:
        system_instruction = """
YOUR ROLE:
You are an objective, professional fact-checking analyst.
YOUR TASKS:
1. Analyze the contents of the text provided by the user.
2. Determine if the information is:
   - VERIFIED / TRUE
   - FALSE / DEBUNKED
   - PARTIALLY TRUE / MISLEADING
   - UNVERIFIABLE
3. Provide a concise explanation detailing why, highlighting key facts.
4. Reference the sources where you received your conclusion and explanation from.
ADDITIONAL REQUIREMENTS:
1. Prioritize peer-reviewed journals, government (.gov), and educational (.edu) sources.
2. Strictly avoid hallucinating citations or citing unverified social media.
3. If information cannot be verified with certainty, state UNVERIFIABLE.
"""

    prompt = f'Please fact-check and verify the following claim or statement:\n\n"""\n{text_to_verify}\n"""'

    used_search = False
    response = None

    # Step 1: Closed-source verification using full content
    if trusted_sources:
        print("\nVerifying claim against approved external sources (Strict Closed-Source Grounding)...")
        try:
            response = call_with_retry(
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.0,
                ),
            )
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower() or "503" in err_str:
                print("\n[Notice] Gemini API unavailable or quota exhausted. Switching to ZERO-TOKEN OFFLINE SEARCH...")
                offline_keyword_check(text_to_verify, trusted_sources)
                return
            print(f"\n[!] Unable to complete verification: {e}")
            return

    # Step 2: Open search grounding if no local sources
    if response is None and _search_grounding_available:
        print("\nSearching the web and verifying claim...")
        try:
            response = call_with_retry(
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                    tools=[{"google_search": {}}, {"url_context": {}}],
                ),
            )
            used_search = True
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                print("\n[Notice] Real-time Google Search Grounding is not active on this free-tier API key.")
                print("Switching to verification via Gemini's built-in factual knowledge base...")
                _search_grounding_available = False
            else:
                print(f"[Notice] Web search unavailable ({e}). Continuing with knowledge-base verification...")

    # Step 3: Knowledge base fallback
    if response is None:
        if not _search_grounding_available:
            print("\nVerifying claim using Gemini's knowledge base...")
        try:
            response = call_with_retry(
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                ),
            )
        except Exception as e:
            err_str = str(e)
            if ("429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower() or "503" in err_str) and trusted_sources:
                print("\n[Notice] Gemini API unavailable. Switching to ZERO-TOKEN OFFLINE SEARCH...")
                offline_keyword_check(text_to_verify, trusted_sources)
                return
            print(f"\n[!] Unable to complete verification: {e}")
            return

    # Step 4: Display results
    print("\n" + "=" * 60)
    print("VERIFICATION RESULT")
    print("=" * 60)
    print(response.text)

    # Step 5: Display cited grounding sources if web search was used
    if used_search and response.candidates:
        grounding = getattr(response.candidates[0], "grounding_metadata", None)
        if grounding:
            sources = []
            chunks = getattr(grounding, "grounding_chunks", None)
            if chunks:
                for chunk in chunks:
                    if chunk.web:
                        sources.append((chunk.web.title, chunk.web.uri))

            if sources:
                print("\n" + "-" * 60)
                print("WEB SOURCES USED:")
                print("-" * 60)
                seen_urls = set()
                for title, url in sources:
                    if url not in seen_urls:
                        print(f"- {title or 'Source'}: {url}")
                        seen_urls.add(url)

            queries = getattr(grounding, "web_search_queries", None)
            if queries:
                print(f"\nSearch queries used: {', '.join(queries)}")


def main():
    print("=" * 60)
    print("       GEMINI FACT-CHECKING ASSISTANT")
    print("=" * 60)
    
    sources = load_trusted_sources()
    if sources:
        cached_count = sum(1 for s in sources if s.get("full_content") and len(s.get("full_content")) > 300)
        print(f"[Grounding Active] Loaded {len(sources)} verified external sources from trusted_sources.json.")
        print(f"[Content Sync] {cached_count}/{len(sources)} sources have full web article content cached.")
        print("[Offline Ready] Zero-token fallback available whenever API quota is exhausted.")
    else:
        print("[Notice] No trusted_sources.json found. Operating in standard mode.")

    while True:
        claim, mode = get_multiline_input()
        
        if mode == "SYNC":
            print("\n[Content Sync] Refreshing full article content for all URLs from the web...")
            sources = load_trusted_sources(force_refresh=True)
            cached_count = sum(1 for s in sources if s.get("full_content") and len(s.get("full_content")) > 300)
            print(f"[Content Sync] Done! {cached_count}/{len(sources)} sources synchronized.")
            continue

        if not claim:
            print("No text entered.")
        else:
            verify_claim(claim, force_offline=(mode == "OFFLINE"))

        cont = input("\nWould you like to verify another statement? (y/n): ").strip().lower()
        if cont != "y":
            print("Exiting.")
            break

if __name__ == "__main__":
    main()
