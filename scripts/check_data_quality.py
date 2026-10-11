"""
JanSahayak — Data Quality Check
------------------------------------
Yeh chhota script saare processed JSON documents check karta hai —
kahin kisi document ka full_text khaali ya missing to nahi reh gaya.
Isse pipeline me koi silent data-loss turant pakda ja sakta hai.
"""

import os
import json

JURISDICTIONS = ["central", "mp", "rajasthan"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "..", "data", "processed")


def main():
    problems = []
    total = 0

    for jurisdiction in JURISDICTIONS:
        folder = os.path.join(PROCESSED_DIR, jurisdiction)
        if not os.path.isdir(folder):
            continue

        json_files = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        print(f"\n=== {jurisdiction.upper()} ===")

        for json_file in json_files:
            total += 1
            path = os.path.join(folder, json_file)
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)

            full_text = record.get("full_text", "")
            text_len = len(full_text)
            has_entities = "entities" in record
            lang_note = record.get("entities", {}).get("language_note", "N/A")

            status = "OK" if text_len > 50 else "PROBLEM (empty/too short!)"
            print(f"  {json_file}: full_text={text_len} chars | entities={has_entities} | lang_note={lang_note} | {status}")

            if text_len <= 50:
                problems.append(f"{jurisdiction}/{json_file}")

    print(f"\n\nTotal documents checked: {total}")
    if problems:
        print(f"PROBLEMS FOUND in {len(problems)} document(s):")
        for p in problems:
            print(f"  - {p}")
    else:
        print("Sab documents theek hain! Koi khaali full_text nahi mila.")


if __name__ == "__main__":
    main()
