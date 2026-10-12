from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from document_processor import load_documents, create_chunks


documents = load_documents()

chunks = []

for document in documents:

    document_chunks = create_chunks(document["text"])

    for chunk in document_chunks:

        chunks.append({
            "filename": document["filename"],
            "text": chunk
        })


if chunks:

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    document_vectors = vectorizer.fit_transform(
        [chunk["text"] for chunk in chunks]
    )

else:

    vectorizer = None
    document_vectors = None


def search_documents(question, top_k=3):

    if not chunks:
        return []

    question_vector = vectorizer.transform([question])

    scores = cosine_similarity(
        question_vector,
        document_vectors
    )[0]

    ranked_indices = scores.argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:

        if scores[index] <= 0:
            continue

        results.append({
            "filename": chunks[index]["filename"],
            "text": chunks[index]["text"],
            "score": float(scores[index])
        })

    return results


def answer_question(question):

    results = search_documents(question)

    if not results:

        return {
            "answer": "I could not find relevant information in the available government documents.",
            "sources": []
        }

    best_result = results[0]

    answer = best_result["text"]

    sources = []

    for result in results:

        sources.append({
            "document": result["filename"],
            "score": round(result["score"], 3)
        })

    return {
        "answer": answer,
        "sources": sources
    }
