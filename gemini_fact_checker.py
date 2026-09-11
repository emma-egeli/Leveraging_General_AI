import os
import sys
import time
import logging
import warnings

# Suppress SDK warnings and internal logger notices
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.ERROR)
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

from google import genai
from google.genai import types
from google.genai import errors

# 1. Initialize Gemini Client
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    # Use preconfigured key or fallback
    api_key = "AQ.Ab8RN6JJXEGKU-mAv9cuNfVBNqF2HJquhFpANmBFxhS9GPEhpw"

client = genai.Client(api_key=api_key)

# Global flag: tracks if search grounding is supported by the current key's quota
_search_grounding_available = True


def get_multiline_input() -> str:
    """Allows the user to paste or type multi-line text into the console."""
    print("\n" + "=" * 60)
    print("Paste or type the claim/information you want to verify.")
    print("When finished, type 'DONE' on a new line and press Enter:")
    print("=" * 60)

    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == "DONE":
                break
            lines.append(line)
        except EOFError:
            break

    return "\n".join(lines).strip()


def call_with_retry(model: str, contents: str, config: types.GenerateContentConfig, max_retries: int = 3):
    """Executes a generate_content call with automatic retry on transient errors (503, 500, etc.)."""
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except errors.APIError as err:
            err_str = str(err)
            # If temporary service unavailable or internal error, retry with backoff
            if err.code in [500, 502, 503, 504] or "UNAVAILABLE" in err_str:
                wait_time = 2 * (attempt + 1)
                if attempt < max_retries - 1:
                    print(f"[Notice] Service temporarily unavailable. Retrying in {wait_time}s ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
            raise
        except Exception as e:
            if "UNAVAILABLE" in str(e) or "503" in str(e):
                wait_time = 2 * (attempt + 1)
                if attempt < max_retries - 1:
                    print(f"[Notice] Temporary glitch. Retrying in {wait_time}s ({attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
            raise


def verify_claim(text_to_verify: str):
    global _search_grounding_available

    system_instruction = """
YOUR ROLE:
You are an objective, professional fact-checking analyst.
YOUR TASKS:
1. Analyze the contents of the text provided by the user. This user-inputted text will be a fact or statement of some sort that needs verification from you. 
2. Determine if the information is:
   - VERIFIED / TRUE
   - FALSE / DEBUNKED
   - PARTIALLY TRUE / MISLEADING
   - UNVERIFIABLE
3. Provide a concise explanation detailing why, highlighting key facts.
4. Reference the sources where you received your conclusion and explanation from.
ADDITIONAL REQUIREMENTS:
1. Pay attention to the context of the sources you come across. Prioritize using sources that are known to be reliable such as peer-reviewed scholarly journals, government websites, educational websites, and reputable news outlets before resorting to other sources. For quick facts, Wikipedia is acceptable. Do NOT use any social media websites as a source. 
2. Pay close attention to any potential AI hallucinations that may be present in the statement. If you think a statement might be an AI hallucination, say so.
3. Do not make predictions relating to the information in the user-inputted statement, only make statements that are explicitly stated in your sources. 
4. Limit the number of sources you pull information from when returning your response to the user. Do not use more than three sources. 
"""
    prompt = f'Please fact-check and verify the following claim or statement:\n\n"""\n{text_to_verify}\n"""'

    used_search = False
    response = None

    # Step 1: If search grounding hasn't already exceeded quota, attempt with Search Grounding
    if _search_grounding_available:
        print("\nSearching the web and verifying claim...")
        try:
            response = call_with_retry(
                model="gemini-3.6-flash",
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
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print("\n[Notice] Real-time Google Search Grounding is not active on this free-tier API key.")
                print("Switching to verification via Gemini's built-in factual knowledge base...")
                _search_grounding_available = False
            else:
                print(f"[Notice] Web search unavailable ({e}). Continuing with knowledge-base verification...")

    # Step 2: Fallback or direct knowledge base verification
    if response is None:
        if not _search_grounding_available:
            print("\nVerifying claim using Gemini's knowledge base...")
        try:
            response = call_with_retry(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.1,
                ),
            )
        except Exception as e:
            print(f"\n[!] Unable to complete verification: {e}")
            return

    # Step 3: Display results
    print("\n" + "=" * 60)
    print("VERIFICATION RESULT")
    print("=" * 60)
    print(response.text)

    # Step 4: Display cited grounding sources if real-time web search was used
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
    while True:
        claim = get_multiline_input()
        if not claim:
            print("No text entered.")
        else:
            verify_claim(claim)

        cont = input("\nWould you like to verify another statement? (y/n): ").strip().lower()
        if cont != "y":
            print("Exiting.")
            break


if __name__ == "__main__":
    main()
