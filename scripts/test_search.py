"""
JanSahayak — Test Search Script
----------------------------------
Yeh chhota script vector store ko test karta hai — koi bhi question
poochho, aur yeh top matching chunks dikhayega (unke source document
aur jurisdiction ke saath).

Chalane se pehle: build_vector_store.py already chal chuka ho.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "jansahayak_documents"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "..", "data", "vector_store")


def main():
    print("Model load ho raha hai...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    print(f"Vector store loaded. Total chunks: {collection.count()}\n")
    print("Apna sawaal type karo (ya 'exit' likho band karne ke liye)\n")

    while True:
        query = input("Question: ").strip()
        if query.lower() in ("exit", "quit"):
            break
        if not query:
            continue

        query_embedding = model.encode([query]).tolist()

        results = collection.query(
            query_embeddings=query_embedding,
            n_results=10,
        )

        print("\n--- Top matches ---")
        for i in range(len(results["documents"][0])):
            doc_text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]

            print(f"\n[{i + 1}] File: {metadata['filename']} | Jurisdiction: {metadata['jurisdiction']} | Similarity: {1 - (distance / 2):.3f}")
            print(f"    {doc_text[:300]}...")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
