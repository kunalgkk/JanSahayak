import os
import json
import re
import spacy

JURISDICTIONS = ["central", "mp", "rajasthan"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "..", "data", "processed")

# spaCy ka max text length default 1,000,000 chars hai — bade documents ke liye
# safe rakhne ke liye thoda aur badha dete hain
MAX_TEXT_LENGTH = 2_000_000

# Regex patterns — yeh language-agnostic hain (Hindi/English dono documents me kaam karenge)
MONEY_PATTERN = re.compile(
    r"(?:₹|Rs\.?|रु\.?)\s?[\d,]+(?:\.\d+)?(?:\s?(?:lakh|crore|लाख|करोड़))?"   # currency pehle: ₹500, Rs. 500
    r"|[\d,]{3,}(?:\.\d+)?\s?/?[-–—]?\s?(?:रुपये|रुपए|रू\.?|रु\.?)"           # number pehle: 500 रुपये, 20,000/- रुपये
    r"|[\d,]{3,}\s?/[-–—]",                                                    # sirf "20,000/-" jaisa format (currency word ke bina)
    re.IGNORECASE,
)
PERCENT_PATTERN = re.compile(r"\d{1,3}(?:\.\d+)?\s?%|\d{1,3}(?:\.\d+)?\s?प्रतिशत")

DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")


def is_hindi_dominant(text, threshold=0.15):
    """Check karta hai ki document mostly Hindi (Devanagari script) me hai ya nahi.
    Agar Hindi-dominant hai, to spaCy ka English NER (PERSON/ORG/DATE) skip karenge,
    kyunki woh un documents pe reliable nahi hota — sirf noise generate karta hai."""
    if not text:
        return False
    devanagari_count = len(DEVANAGARI_RANGE.findall(text))
    return (devanagari_count / max(len(text), 1)) > threshold


def extract_regex_entities(text):
    """Money amounts aur percentages nikalta hai — language-agnostic tareeke se."""
    money_matches = list(set(MONEY_PATTERN.findall(text)))
    percent_matches = list(set(PERCENT_PATTERN.findall(text)))
    return {
        "money_amounts": money_matches[:30],   # top 30 tak limit, taaki output saaf rahe
        "percentages": percent_matches[:30],
    }


def extract_spacy_entities(text, nlp):
    """spaCy se PERSON, ORG, DATE, GPE entities nikalta hai (English text ke liye best)."""
    # Bohot bade text ko chunks me todte hain (spaCy ki performance ke liye)
    chunk_size = 100_000
    entities = {"PERSON": set(), "ORG": set(), "DATE": set(), "GPE": set()}

    for start in range(0, min(len(text), MAX_TEXT_LENGTH), chunk_size):
        chunk = text[start:start + chunk_size]
        doc = nlp(chunk)
        for ent in doc.ents:
            if ent.label_ in entities:
                cleaned = ent.text.strip()
                if len(cleaned) > 1:
                    entities[ent.label_].add(cleaned)

    # Set ko list me convert karo (JSON me set save nahi hota), aur limit lagao
    return {k: list(v)[:30] for k, v in entities.items()}


def process_document(record, nlp):
    full_text = record.get("full_text", "")

    regex_entities = extract_regex_entities(full_text)
    hindi_dominant = is_hindi_dominant(full_text)

    if hindi_dominant:
        # Hindi-dominant documents ke liye spaCy ka English NER skip karte hain
        # (PERSON/ORG/DATE), kyunki woh sirf galat/noise results deta hai.
        # Sirf language-agnostic regex-based extraction (money/percent) use karte hain.
        spacy_entities = {"PERSON": [], "ORG": [], "DATE": [], "GPE": []}
    else:
        spacy_entities = extract_spacy_entities(full_text, nlp)

    entities = {
        "language_note": "hindi_dominant_spacy_skipped" if hindi_dominant else "english_ner_applied",
        "people": spacy_entities["PERSON"],
        "organizations": spacy_entities["ORG"],
        "dates": spacy_entities["DATE"],
        "locations": spacy_entities["GPE"],
        "money_amounts": regex_entities["money_amounts"],
        "percentages": regex_entities["percentages"],
    }
    return entities


def main():
    print("spaCy English model load ho raha hai...")
    nlp = spacy.load("en_core_web_sm")

    for jurisdiction in JURISDICTIONS:
        folder = os.path.join(PROCESSED_DIR, jurisdiction)
        if not os.path.isdir(folder):
            print(f"[SKIP] Folder not found: {folder}")
            continue

        json_files = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        print(f"\n=== {jurisdiction.upper()} ({len(json_files)} documents) ===")

        for json_file in json_files:
            path = os.path.join(folder, json_file)
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)

            print(f"  Processing: {json_file}")
            entities = process_document(record, nlp)
            record["entities"] = entities

            with open(path, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)

            print(f"    -> [{entities['language_note']}] Found: {len(entities['people'])} people, "
                  f"{len(entities['organizations'])} orgs, "
                  f"{len(entities['dates'])} dates, "
                  f"{len(entities['money_amounts'])} amounts, "
                  f"{len(entities['percentages'])} percentages")

    print("\nDone! Saare documents me 'entities' field add ho gaya hai.")


if __name__ == "__main__":
    main()
