"""
JanSahayak — Document Summarization
----------------------------------------
Yeh script har processed document ka ek chhota, readable summary
banata hai (Gemini LLM se) aur JSON me "summary" field add kar deta hai.

Chalane se pehle: .env file me GEMINI_API_KEY set ho.
"""


import os
import json
import time
from dotenv import load_dotenv
import google.generativeai as genai

JURISDICTIONS = ["central", "mp", "rajasthan"]

# Flash-Lite models ka free-tier daily quota (RPD) regular Flash se 25x zyada hai
# (500/day vs 20/day) — isliye yeh use kar rahe hain, na ki gemini-3.5-flash.
GEMINI_MODEL_NAMES = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]

# Bohot bade documents ke liye text truncate karte hain (taaki prompt zyada bada na ho)
MAX_CHARS_FOR_SUMMARY = 30000

# Har API call ke beech thoda ruko, taaki free-tier rate limit na lage
SLEEP_BETWEEN_CALLS = 5

# Agar rate-limit (429) error aaye, kitni baar aur kitna ruk ke retry karein
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 30

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "..", "data", "processed")

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY .env file me nahi mili!")

genai.configure(api_key=api_key)
gemini_models = [genai.GenerativeModel(name) for name in GEMINI_MODEL_NAMES]
_model_index = 0


def get_next_model():
    """Har call par model alternate karta hai, taaki dono models ka alag RPD quota use ho."""
    global _model_index
    model = gemini_models[_model_index % len(gemini_models)]
    _model_index += 1
    return model


def build_summary_prompt(text):
    truncated = text[:MAX_CHARS_FOR_SUMMARY]
    prompt = f"""Neeche ek government scheme/policy document ka text diya gaya hai. Iska ek chhota, saaf summary likho.

NIYAM:
1. Summary 3-5 sentences ka ho, na zyada lamba na zyada chhota.
2. Sirf sabse important cheezein cover karo: scheme/document ka naam, uska objective, aur (agar applicable ho) eligibility ya key benefit.
3. Document jis language me hai (Hindi ya English), usi language me summary likho.
4. Sirf summary likho, koi extra preamble ya "Here is the summary" jaisa mat likhna.

DOCUMENT TEXT:
{truncated}

SUMMARY:"""
    return prompt


def summarize_document(text):
    if not text or len(text.strip()) < 50:
        return "Document ka text bohot chhota/khaali hai, summary nahi ban saki."

    prompt = build_summary_prompt(text)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            model = get_next_model()
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            error_str = str(e)
            if "429" in error_str and attempt < MAX_RETRIES:
                print(f"    [Rate limit hit, {RETRY_WAIT_SECONDS}s ruk ke retry kar rahe hain... attempt {attempt}/{MAX_RETRIES}]")
                time.sleep(RETRY_WAIT_SECONDS)
                continue
            return f"[ERROR] Summary generate nahi ho paya: {e}"


class QuotaExhaustedError(Exception):
    pass


def main():
    quota_exhausted = False

    for jurisdiction in JURISDICTIONS:
        if quota_exhausted:
            break
        folder = os.path.join(PROCESSED_DIR, jurisdiction)
        if not os.path.isdir(folder):
            continue

        json_files = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        print(f"\n=== {jurisdiction.upper()} ({len(json_files)} documents) ===")

        for json_file in json_files:
            path = os.path.join(folder, json_file)
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)

            print(f"  Summarizing: {json_file}...")
            full_text = record.get("full_text", "")

            # Agar pehle se hi valid summary hai (error nahi), to skip karo — quota bachao
            existing_summary = record.get("summary", "")
            if existing_summary and not existing_summary.startswith("[ERROR]") and len(existing_summary) > 20:
                print(f"    -> Already summarized, skip kar rahe hain.")
                continue

            summary = summarize_document(full_text)

            # Agar quota genuinely khatam ho chuka hai, to poora script yahin rok do
            # (baaki documents try karna sirf time waste karega)
            if summary.startswith("[ERROR]") and "429" in summary:
                print("\n[STOPPING] Daily/rate quota khatam lag raha hai.")
                print("Jo abhi tak ho chuka hai woh save ho chuka hai. Thodi der baad (ya kal) dobara")
                print("'python scripts/summarize.py' chalana — already-done documents skip ho jaayenge.\n")
                quota_exhausted = True
                break

            record["summary"] = summary

            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

            print(f"    -> {summary[:100]}...")
            time.sleep(SLEEP_BETWEEN_CALLS)

    print("\nDone! Saare documents me 'summary' field add ho gaya hai.")


if __name__ == "__main__":
    main()
