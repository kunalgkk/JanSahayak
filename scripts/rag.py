"""
JanSahayak — RAG (Retrieval-Augmented Generation)
-----------------------------------------------------
Yeh script poora Layer 4 hai: user ka sawaal leta hai, hybrid search se
relevant chunks dhoondta hai, phir Gemini LLM ko un chunks ke saath
bhejta hai taaki woh un chunks ke andar se hi ek accurate, cited answer
banaye — bahar se kuch bana ke na de (hallucination avoid karne ke liye).

Chalane se pehle: build_vector_store.py chal chuka ho, aur .env file me
GEMINI_API_KEY set ho.
"""

import os
import re
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
import google.generativeai as genai

# ============================================================
# CONFIG
# ============================================================
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "jansahayak_documents"
GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"  # 500 requests/day free-tier (vs 20/day on regular Flash)

SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5
TOP_K_CHUNKS = 5  # kitne chunks LLM ko context ke roop me denge

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "..", "data", "vector_store")

# ============================================================
# Setup: Gemini API key load karo .env se
# ============================================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY .env file me nahi mili! Pehle .env file check karo.")

genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)


def tokenize(text):
    return re.findall(r"\w+", text.lower())


def normalize_scores(scores):
    scores = np.array(scores, dtype=float)
    min_s, max_s = scores.min(), scores.max()
    if max_s - min_s < 1e-9:
        return np.zeros_like(scores)
    return (scores - min_s) / (max_s - min_s)


def hybrid_retrieve(query, model, documents, metadatas, embeddings, bm25, top_k=TOP_K_CHUNKS):
    """Hybrid search se top matching chunks dhoondta hai."""
    query_embedding = model.encode([query])[0]
    semantic_scores = embeddings @ query_embedding / (
        np.linalg.norm(embeddings, axis=1) * np.linalg.norm(query_embedding)
    )
    keyword_scores = bm25.get_scores(tokenize(query))

    norm_semantic = normalize_scores(semantic_scores)
    norm_keyword = normalize_scores(keyword_scores)
    combined = SEMANTIC_WEIGHT * norm_semantic + KEYWORD_WEIGHT * norm_keyword

    top_indices = np.argsort(combined)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "text": documents[idx],
            "filename": metadatas[idx]["filename"],
            "jurisdiction": metadatas[idx]["jurisdiction"],
            "score": combined[idx],
        })
    return results


def build_prompt(query, retrieved_chunks):
    """LLM ke liye prompt banata hai — sirf retrieved context use karne ko bolta hai."""
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[Source {i}: {chunk['filename']} ({chunk['jurisdiction']})]\n{chunk['text']}"
        )
    context_text = "\n\n".join(context_blocks)

    prompt = f"""Tum ek government scheme assistant ho jiska naam JanSahayak hai. Neeche diye gaye documents ke context ke aadhar par user ke sawaal ka jawab do.

NIYAM:
1. Sirf neeche diye gaye context se answer do. Agar context me answer nahi hai, to saaf keh do "Yeh jaankari diye gaye documents me उपलब्ध nahi hai."
2. Apne answer ke end me batao kaunse Source(s) se yeh jaankari li hai (jaise "[Source: AICTE_3039_G.pdf]").
3. Answer clear aur seedha ho, unnecessary lamba mat karo.
4. Agar user Hindi me poochhe to Hindi me jawab do, English me poochhe to English me.

CONTEXT:
{context_text}

USER KA SAWAAL: {query}

ANSWER:"""
    return prompt


def main():
    print("Model aur vector store load ho rahe hain...")
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    all_data = collection.get(include=["documents", "embeddings", "metadatas"])
    documents = all_data["documents"]
    metadatas = all_data["metadatas"]
    embeddings = np.array(all_data["embeddings"])

    tokenized_corpus = [tokenize(doc) for doc in documents]
    bm25 = BM25Okapi(tokenized_corpus)

    print(f"Ready! Total chunks: {len(documents)}\n")
    print("Apna sawaal type karo (ya 'exit' likho band karne ke liye)\n")

    while True:
        query = input("Question: ").strip()
        if query.lower() in ("exit", "quit"):
            break
        if not query:
            continue

        print("\nSearching relevant documents...")
        retrieved_chunks = hybrid_retrieve(query, model, documents, metadatas, embeddings, bm25)

        print("Gemini se answer generate ho raha hai...\n")
        prompt = build_prompt(query, retrieved_chunks)

        try:
            response = gemini_model.generate_content(prompt)
            print("--- ANSWER ---")
            print(response.text)
        except Exception as e:
            print(f"[ERROR] Gemini call fail hui: {e}")

        print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
