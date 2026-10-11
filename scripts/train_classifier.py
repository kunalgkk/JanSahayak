
import os
import csv
import json
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "..", "data", "processed")
LABELS_CSV = os.path.join(BASE_DIR, "..", "data", "labels.csv")
MODEL_PATH = os.path.join(BASE_DIR, "..", "data", "classifier_model.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "..", "data", "classifier_vectorizer.pkl")


def load_labels_and_text():
    """labels.csv padhta hai, aur har document ka full_text uske JSON se leta hai."""
    texts = []
    labels = []
    file_refs = []  # (jurisdiction, filename) taaki baad me JSON update kar sakein

    with open(LABELS_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            jurisdiction = row["jurisdiction"]
            filename = row["filename"]
            label = row["predicted_label"].strip().lower()

            json_path = os.path.join(PROCESSED_DIR, jurisdiction, filename)
            with open(json_path, "r", encoding="utf-8") as jf:
                record = json.load(jf)

            full_text = record.get("full_text", "")
            texts.append(full_text)
            labels.append(label)
            file_refs.append((jurisdiction, filename))

    return texts, labels, file_refs


def main():
    print("Labels aur documents load ho rahe hain...")
    texts, labels, file_refs = load_labels_and_text()
    print(f"Total documents: {len(texts)}")

    label_counts = {}
    for l in labels:
        label_counts[l] = label_counts.get(l, 0) + 1
    print(f"Label distribution: {label_counts}\n")

    # TF-IDF vectorizer — text ko numbers me convert karta hai
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)

    # Chhota dataset hai, isliye poore data pe train karte hain,
    # lekin ek chhota train/test split bhi dikhate hain accuracy ka andaza dene ke liye
    if len(set(labels)) > 1 and len(texts) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=0.2, random_state=42, stratify=None
        )
        temp_model = LogisticRegression(max_iter=1000)
        temp_model.fit(X_train, y_train)
        y_pred = temp_model.predict(X_test)
        print("=== Test set par evaluation (chhota hold-out sample) ===")
        print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
        print(classification_report(y_test, y_pred, zero_division=0))

    # Final model — POORE data pe train karte hain (taaki har document ka use ho)
    print("Final model poore data pe train ho raha hai...")
    model = LogisticRegression(max_iter=1000)
    model.fit(X, labels)

    # Model aur vectorizer save karo (baad me naye documents classify karne ke liye)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    with open(VECTORIZER_PATH, "wb") as f:
        pickle.dump(vectorizer, f)
    print(f"Model saved: {MODEL_PATH}")

    # Ab saare documents pe prediction lagate hain aur JSON me "category" add karte hain
    print("\nSaare documents me 'category' field add ho raha hai...")
    predictions = model.predict(X)

    for (jurisdiction, filename), predicted_category in zip(file_refs, predictions):
        json_path = os.path.join(PROCESSED_DIR, jurisdiction, filename)
        with open(json_path, "r", encoding="utf-8") as f:
            record = json.load(f)

        record["category"] = predicted_category

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

    print("Done! Saare documents me 'category' field add ho gaya hai.")


if __name__ == "__main__":
    main()
