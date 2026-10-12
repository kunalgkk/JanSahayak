from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

import os
import shutil

from rag import answer_question
from eligibility import check_eligibility
from summarizer import summarize_text


app = FastAPI(
    title="JanSahayak AI",
    description="AI-powered Government Document Intelligence Platform"
)


# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------
# Home
# ------------------------------------------------

@app.get("/")
def home():

    return {
        "message": "JanSahayak AI Backend is running"
    }


# ------------------------------------------------
# Ask Question
# ------------------------------------------------

@app.post("/ask")
def ask_question(data: dict):

    question = data.get("question", "")

    if not question:

        return {
            "error": "Question is required"
        }

    result = answer_question(question)

    return result


# ------------------------------------------------
# Eligibility
# ------------------------------------------------

@app.post("/eligibility")
def eligibility(data: dict):

    result = check_eligibility(
        scheme=data.get("scheme", ""),
        age=data.get("age"),
        occupation=data.get("occupation"),
        income=data.get("income"),
        education=data.get("education")
    )

    return result


# ------------------------------------------------
# Summarize
# ------------------------------------------------

@app.post("/summarize")
def summarize(data: dict):

    text = data.get("text", "")

    if not text:

        return {
            "error": "Text is required"
        }

    summary = summarize_text(text)

    return {
        "summary": summary
    }


# ------------------------------------------------
# Upload Document
# ------------------------------------------------

@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    os.makedirs("documents", exist_ok=True)

    file_path = os.path.join(
        "documents",
        file.filename
    )

    with open(file_path, "wb") as buffer:

        shutil.copyfileobj(
            file.file,
            buffer
        )

    return {
        "message": "Document uploaded successfully",
        "filename": file.filename
    }


# ------------------------------------------------
# Run server
# ------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
