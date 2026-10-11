"""
JanSahayak — Backend API (FastAPI)
--------------------------------------
Yeh tumhare existing hybrid_search.py + rag.py ki logic ko ek web API
ke roop me expose karta hai, taaki frontend (HTML/JS) usse call kar sake.

Chalane ka tarika:
    uvicorn backend.main:app --reload --port 8000

Phir frontend/index.html ko browser me kholo.
"""

import os
import re
import numpy as np
import chromadb
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
import google.generativeai as genai

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ============================================================
# CONFIG — rag.py jaisa hi
# ============================================================
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "jansahayak_documents"
GEMINI_MODEL_NAME = "gemini-3.5-flash-lite"

SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5
TOP_K_CHUNKS = 5

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_DIR = os.path.join(BASE_DIR, "data", "vector_store")

# ============================================================
# Setup — ek hi baar server start hote waqt hota hai
# ============================================================
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY .env file me nahi mili!")

genai.configure(api_key=api_key)
gemini_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

print("Model aur vector store load ho rahe hain (server start ho raha hai)...")
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)

client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
collection = client.get_collection(COLLECTION_NAME)

all_data = collection.get(include=["documents", "embeddings", "metadatas"])
documents = all_data["documents"]
metadatas = all_data["metadatas"]
embeddings = np.array(all_data["embeddings"])

tokenized_corpus = [re.findall(r"\w+", doc.lower()) for doc in documents]
bm25 = BM25Okapi(tokenized_corpus)

print(f"Ready! Total chunks loaded: {len(documents)}")

# ============================================================
# FastAPI app
# ============================================================
app = FastAPI(title="JanSahayak API")

# Frontend (alag file/port se) backend ko call kar sake, isliye CORS allow karte hain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


class SourceInfo(BaseModel):
    filename: str
    jurisdiction: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]


def tokenize(text):
    return re.findall(r"\w+", text.lower())


def normalize_scores(scores):
    scores = np.array(scores, dtype=float)
    min_s, max_s = scores.min(), scores.max()
    if max_s - min_s < 1e-9:
        return np.zeros_like(scores)
    return (scores - min_s) / (max_s - min_s)


def hybrid_retrieve(query, top_k=TOP_K_CHUNKS):
    query_embedding = embedding_model.encode([query])[0]
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
        })
    return results


def build_prompt(query, retrieved_chunks):
    context_blocks = []
    for i, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[Source {i}: {chunk['filename']} ({chunk['jurisdiction']})]\n{chunk['text']}"
        )
    context_text = "\n\n".join(context_blocks)

    prompt = f"""Tum ek government scheme assistant ho jiska naam JanSahayak hai. Neeche diye gaye documents ke context ke aadhar par user ke sawaal ka jawab do.

NIYAM:
1. Sirf neeche diye gaye context se answer do. Agar context me answer nahi hai, to saaf keh do "Yeh jaankari diye gaye documents me उपलब्ध nahi hai."
2. Apne answer ke end me ek "Source(s):" section banao, jisme sirf unique file names list karo (agar ek hi file ke multiple chunks context me the, to us file ka naam sirf ek baar likho — "Source 1, Source 2" jaise numbering mat karo, bas file names ek list me do).
3. Answer clear aur seedha ho, unnecessary lamba mat karo.
4. Agar user Hindi me poochhe to Hindi me jawab do, English me poochhe to English me.

CONTEXT:
{context_text}

USER KA SAWAAL: {query}

ANSWER:"""
    return prompt


@app.get("/")
def health_check():
    return {"status": "JanSahayak API chal raha hai", "total_chunks": len(documents)}


@app.get("/documents")
def list_documents():
    """Saare unique indexed documents ki list deta hai (real data, vector store se)."""
    seen = set()
    doc_list = []
    for meta in metadatas:
        key = (meta["filename"], meta["jurisdiction"])
        if key not in seen:
            seen.add(key)
            doc_list.append({"filename": meta["filename"], "jurisdiction": meta["jurisdiction"]})
    doc_list.sort(key=lambda d: (d["jurisdiction"], d["filename"]))
    return {"total": len(doc_list), "documents": doc_list}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    retrieved_chunks = hybrid_retrieve(request.question)
    prompt = build_prompt(request.question, retrieved_chunks)

    try:
        response = gemini_model.generate_content(prompt)
        answer_text = response.text
    except Exception as e:
        answer_text = f"Maaf karo, answer generate karte waqt error aayi: {e}"

    # Duplicate sources hata dete hain (ek hi document ke multiple chunks aa sakte hain)
    seen = set()
    unique_sources = []
    for chunk in retrieved_chunks:
        key = (chunk["filename"], chunk["jurisdiction"])
        if key not in seen:
            seen.add(key)
            unique_sources.append(SourceInfo(filename=chunk["filename"], jurisdiction=chunk["jurisdiction"]))

    return AnswerResponse(answer=answer_text, sources=unique_sources)
