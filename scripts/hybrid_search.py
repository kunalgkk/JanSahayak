"""
JanSahayak — Hybrid Search (Semantic + Keyword)
--------------------------------------------------
Semantic search akela kabhi-kabhi specific keywords miss kar deta hai
(jaise "orphan", "Employee ID", exact scheme names). Yeh script semantic
similarity (meaning-based) aur BM25 keyword search (exact-word-based)
dono ko combine karke better ranking deta hai.

Chalane se pehle: build_vector_store.py already chal chuka ho.
"""

import os
import re
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "jansahayak_documents"

# Kitna weight semantic ko denge, kitna keyword (BM25) ko — dono milaake 1.0
SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "..", "data", "vector_store")


def tokenize(text):
    """Simple tokenizer — lowercase karke words alag karta hai (BM25 ke liye)."""
    return re.findall(r"\w+", text.lower())


def normalize_scores(scores):
    """Scores ko 0-1 range me laata hai taaki semantic aur BM25 fair compare ho sakein."""
    scores = np.array(scores, dtype=float)
    min_s, max_s = scores.min(), scores.max()
    if max_s - min_s < 1e-9:
        return np.zeros_like(scores)
    return (scores - min_s) / (max_s - min_s)


def main():
    print("Model load ho raha hai...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    print("Saare chunks load kar rahe hain (BM25 index banane ke liye)...")
    all_data = collection.get(include=["documents", "embeddings", "metadatas"])

    documents = all_data["documents"]
    metadatas = all_data["metadatas"]
    embeddings = np.array(all_data["embeddings"])

    print(f"Total chunks: {len(documents)}")

    # BM25 index banate hain (keyword search ke liye)
    tokenized_corpus = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)

    print("\nReady! Apna sawaal type karo (ya 'exit' likho band karne ke liye)\n")

    while True:
        query = input("Question: ").strip()
        if query.lower() in ("exit", "quit"):
            break
        if not query:
            continue

        # --- Semantic similarity (poore corpus ke saath, sahi comparison ke liye) ---
        query_embedding = model.encode([query])[0]
        semantic_scores = embeddings @ query_embedding / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # --- BM25 keyword scores ---
        keyword_scores = bm25.get_scores(tokenize(query))

        # --- Dono ko normalize karke combine karo ---
        norm_semantic = normalize_scores(semantic_scores)
        norm_keyword = normalize_scores(keyword_scores)
        combined = SEMANTIC_WEIGHT * norm_semantic + KEYWORD_WEIGHT * norm_keyword

        top_indices = np.argsort(combined)[::-1][:5]

        print("\n--- Top matches (Hybrid: semantic + keyword) ---")
        for rank, idx in enumerate(top_indices, start=1):
            meta = metadatas[idx]
            print(
                f"\n[{rank}] File: {meta['filename']} | Jurisdiction: {meta['jurisdiction']} "
                f"| Combined: {combined[idx]:.3f} (semantic: {norm_semantic[idx]:.3f}, keyword: {norm_keyword[idx]:.3f})"
            )
            print(f"    {documents[idx][:300]}...")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
