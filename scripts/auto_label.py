
import os
import json
import csv

JURISDICTIONS = ["central", "mp", "rajasthan"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "..", "data", "processed")
LABELS_CSV = os.path.join(BASE_DIR, "..", "data", "labels.csv")

# Keywords jo har category ko suggest karte hain
POLICY_KEYWORDS = [
    "institutional structure", "project approval board", "national mission authority",
    "grants to strengthen", "meru", "accreditation", "naac", "component", "short-listing criteria",
    "output-outcome framework", "mou with state", "rusa", "pm-usha",
]
CIRCULAR_KEYWORDS = [
    "portal reopen", "office order", "notice", "extension of date", "reminder",
    "forwarded", "circular no", "corrigendum",
]
# Baaki sab (scholarship, eligibility, amount, application process) -> "scheme"


def guess_label(text):
    text_lower = text.lower()

    policy_score = sum(1 for kw in POLICY_KEYWORDS if kw in text_lower)
    circular_score = sum(1 for kw in CIRCULAR_KEYWORDS if kw in text_lower)

    if circular_score >= 1 and circular_score >= policy_score:
        return "circular"
    elif policy_score >= 2:
        return "policy"
    else:
        return "scheme"


def main():
    rows = []

    for jurisdiction in JURISDICTIONS:
        folder = os.path.join(PROCESSED_DIR, jurisdiction)
        if not os.path.isdir(folder):
            continue

        json_files = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        for json_file in json_files:
            path = os.path.join(folder, json_file)
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)

            full_text = record.get("full_text", "")
            predicted = guess_label(full_text)

            rows.append({
                "jurisdiction": jurisdiction,
                "filename": json_file,
                "predicted_label": predicted,
                "preview": full_text[:150].replace("\n", " "),
            })

    os.makedirs(os.path.dirname(LABELS_CSV), exist_ok=True)
    with open(LABELS_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["jurisdiction", "filename", "predicted_label", "preview"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Done! {len(rows)} documents ke liye guess labels bana diye.")
    print(f"CSV file yahan hai: {LABELS_CSV}")
    print("\nAB YEH KARO:")
    print("1. data/labels.csv ko Excel ya Notepad me kholo")
    print("2. 'predicted_label' column check karo har row ke liye")
    print("   (values sirf yeh ho sakti hain: scheme, policy, circular)")
    print("3. Agar galat lage to sahi label type kar do")
    print("4. Save karke band karo")
    print("5. Phir 'python scripts/train_classifier.py' chalao")


if __name__ == "__main__":
    main()
