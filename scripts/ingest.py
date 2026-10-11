"""
JanSahayak — Document Ingestion + OCR Script
----------------------------------------------
Yeh script data/raw/{central, mp, rajasthan} ke saare PDFs padhta hai,
text extract karta hai, aur agar PDF scanned/image-based hai to
automatically OCR (Tesseract) use karta hai.

Output: data/processed/{jurisdiction}/<filename>.json
Har JSON file me: filename, jurisdiction, full text, per-page text,
aur extraction_method (kaunsa tareeka use hua — "text" ya "ocr").
"""

import os
import json
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

# ============================================================
# CONFIG — apne system ke hisaab se yeh 2 paths change karo
# ============================================================
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Users\HP\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# Kitne characters se kam text mile to hum maan lenge ki yeh scanned PDF hai
MIN_TEXT_LENGTH_PER_PAGE = 20

# Jurisdictions jo hum process karenge (folder names in data/raw/)
JURISDICTIONS = ["central", "mp", "rajasthan"]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")


def extract_text_native(pdf_path):
    """PDF se seedha text nikalne ki koshish karta hai (fast, clean PDFs ke liye)."""
    pages_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text.strip())
    except Exception as e:
        print(f"    [WARN] pdfplumber failed: {e}")
        return []
    return pages_text


def extract_text_ocr(pdf_path):
    """Scanned/image PDFs ke liye OCR se text nikalta hai."""
    pages_text = []
    try:
        images = convert_from_path(pdf_path, poppler_path=POPPLER_PATH, dpi=300)
        for i, image in enumerate(images):
            print(f"    OCR running on page {i + 1}...")
            text = pytesseract.image_to_string(image, lang="hin+eng")
            pages_text.append(text.strip())
    except Exception as e:
        print(f"    [ERROR] OCR failed: {e}")
        return []
    return pages_text


def needs_ocr(pages_text):
    """Checks whether the extracted text is insufficient for native extraction."""
    if not pages_text:
        return True
    total_chars = sum(len(p) for p in pages_text)
    avg_chars_per_page = total_chars / max(len(pages_text), 1)
    return avg_chars_per_page < MIN_TEXT_LENGTH_PER_PAGE


def process_pdf(pdf_path, jurisdiction):
    filename = os.path.basename(pdf_path)
    print(f"  Processing: {filename}")

    # Step 1: pehle native text extraction try karo
    pages_text = extract_text_native(pdf_path)
    method = "text"

    # Step 2: agar text bohot kam/khaali hai, to OCR pe switch karo
    if needs_ocr(pages_text):
        print(f"printing through native text ocr didnt worked well")
        pages_text = extract_text_ocr(pdf_path)
        method = "ocr"
    else:
        print(f"    -> Native text extraction se ho gaya (OCR ki zaroorat nahi)")

    full_text = "\n\n".join(pages_text)

    record = {
        "filename": filename,
        "jurisdiction": jurisdiction,
        "extraction_method": method,
        "num_pages": len(pages_text),
        "full_text": full_text,
        "pages": pages_text,
    }
    return record


def main():
    for jurisdiction in JURISDICTIONS:
        raw_folder = os.path.join(RAW_DIR, jurisdiction)
        processed_folder = os.path.join(PROCESSED_DIR, jurisdiction)
        os.makedirs(processed_folder, exist_ok=True)

        if not os.path.isdir(raw_folder):
            print(f"[SKIP] Folder not found: {raw_folder}")
            continue

        pdf_files = [f for f in os.listdir(raw_folder) if f.lower().endswith(".pdf")]
        print(f"\n=== Jurisdiction: {jurisdiction.upper()} ({len(pdf_files)} PDFs) ===")

        for pdf_file in pdf_files:
            pdf_path = os.path.join(raw_folder, pdf_file)
            try:
                record = process_pdf(pdf_path, jurisdiction)

                output_filename = os.path.splitext(pdf_file)[0] + ".json"
                output_path = os.path.join(processed_folder, output_filename)

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(record, f, ensure_ascii=False, indent=2)

                print(f"    Saved -> {output_path}")
            except Exception as e:
                print(f"    [ERROR] Failed to process {pdf_file}: {e}")

    print("\nDone! Saare PDFs process ho gaye. Check karo data/processed/ folder.")


if __name__ == "__main__":
    main()
