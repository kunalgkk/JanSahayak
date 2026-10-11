"""
JanSahayak — Embeddings + Vector Store Builder
------------------------------------------------
Yeh script data/processed/{central, mp, rajasthan} ke saare JSON files
padhta hai, unke text ko chunks me todta hai, embeddings banata hai
(multilingual model se — Hindi aur English dono ke liye), aur ChromaDB
me store karta hai taaki baad me semantic search ho sake.

Chalane se pehle: ingest.py already chal chuka ho aur data/processed/
me JSON files ban chuki hon.
"""

import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

# ============================================================
# CONFIG
# ============================================================
JURISDICTIONS = ["central", "mp", "rajasthan"]

# Multilingual model — Hindi aur English dono documents ke liye kaam karega
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# Chunking settings — kitne words ka ek chunk banega
CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 50

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DIR = os.path.join(BASE_DIR, "..", "data", "processed")
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "..", "data", "vector_store")

COLLECTION_NAME = "jansahayak_documents"


def chunk_text(text, chunk_size=CHUNK_SIZE_WORDS, overlap=CHUNK_OVERLAP_WORDS):
    """Text ko overlapping word-chunks me todta hai."""
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap  # overlap rakhte hain taaki context na tute

    return chunks


def load_all_documents():
    """Saare processed JSON documents padhta hai, jurisdiction ke saath."""
    documents = []
    for jurisdiction in JURISDICTIONS:
        folder = os.path.join(PROCESSED_DIR, jurisdiction)
        if not os.path.isdir(folder):
            print(f"[SKIP] Folder not found: {folder}")
            continue

        json_files = [f for f in os.listdir(folder) if f.lower().endswith(".json")]
        print(f"Loading {len(json_files)} documents from {jurisdiction}...")

        for json_file in json_files:
            path = os.path.join(folder, json_file)
            with open(path, "r", encoding="utf-8") as f:
                record = json.load(f)
                documents.append(record)

    return documents


def build_vector_store():
    print("Loading embedding model (pehli baar thoda time lagega, model download hoga)...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    print("\nLoading processed documents...")
    documents = load_all_documents()
    print(f"Total documents loaded: {len(documents)}\n")

    # ChromaDB client — disk pe persist karega taaki baar-baar rebuild na karna pade
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)

    # Agar collection pehle se hai to delete karke fresh banate hain
    try:
        client.delete_collection(COLLECTION_NAME)
        print("Purani collection mil gayi thi, delete karke fresh bana rahe hain.\n")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunk_texts = []
    all_chunk_ids = []
    all_metadatas = []

    for doc in documents:
        filename = doc["filename"]
        jurisdiction = doc["jurisdiction"]
        full_text = doc.get("full_text", "")

        chunks = chunk_text(full_text)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{jurisdiction}__{filename}__chunk{i}"
            all_chunk_texts.append(chunk)
            all_chunk_ids.append(chunk_id)
            all_metadatas.append({
                "filename": filename,
                "jurisdiction": jurisdiction,
                "chunk_index": i,
            })

    print(f"Total chunks created: {len(all_chunk_texts)}")
    print("Embeddings ban rahe hain, thoda time lagega...\n")

    # Batch me embed karte hain taaki memory issue na ho
    batch_size = 64
    for start in range(0, len(all_chunk_texts), batch_size):
        end = start + batch_size
        batch_texts = all_chunk_texts[start:end]
        batch_ids = all_chunk_ids[start:end]
        batch_metadatas = all_metadatas[start:end]

        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()

        collection.add(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas,
        )

        print(f"  Processed chunks {start} to {min(end, len(all_chunk_texts))} / {len(all_chunk_texts)}")

    print(f"\nDone! Vector store ban gaya: {VECTOR_STORE_DIR}")
    print(f"Total chunks stored: {collection.count()}")


if __name__ == "__main__":
    build_vector_store()
