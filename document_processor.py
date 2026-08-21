import os
import fitz


DOCUMENT_FOLDER = "documents"


def read_text_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def read_pdf(path):
    text = ""

    pdf = fitz.open(path)

    for page_number, page in enumerate(pdf):
        page_text = page.get_text()

        text += f"\n[Page {page_number + 1}]\n"
        text += page_text

    pdf.close()

    return text


def load_documents():
    documents = []

    if not os.path.exists(DOCUMENT_FOLDER):
        os.makedirs(DOCUMENT_FOLDER)

    for filename in os.listdir(DOCUMENT_FOLDER):

        path = os.path.join(DOCUMENT_FOLDER, filename)

        if filename.endswith(".txt"):
            text = read_text_file(path)

        elif filename.endswith(".pdf"):
            text = read_pdf(path)

        else:
            continue

        documents.append({
            "filename": filename,
            "text": text
        })

    return documents


def create_chunks(text, chunk_size=500):

    words = text.split()

    chunks = []

    for i in range(0, len(words), chunk_size):

        chunk = " ".join(words[i:i + chunk_size])

        chunks.append(chunk)

    return chunks
