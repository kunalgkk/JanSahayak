import os
import pickle
import faiss

from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


class VectorStore:

    def __init__(self):

        self.index = None
        self.documents = []

    def create_index(self, chunks):

        self.documents = chunks

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = model.encode(
            texts,
            convert_to_numpy=True
        )

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(
            dimension
        )

        self.index.add(embeddings)

    def search(self, query, top_k=5):

        if self.index is None:
            return []

        query_embedding = model.encode(
            [query],
            convert_to_numpy=True
        )

        distances, indices = self.index.search(
            query_embedding,
            top_k
        )

        results = []

        for distance, index in zip(
            distances[0],
            indices[0]
        ):

            if index < len(self.documents):

                results.append({
                    "text": self.documents[index]["text"],
                    "filename": self.documents[index]["filename"],
                    "score": float(distance)
                })

        return results


    def save(self, path="data/vector_store.pkl"):

        os.makedirs(
            os.path.dirname(path),
            exist_ok=True
        )

        with open(path, "wb") as file:

            pickle.dump(
                self.documents,
                file
            )

        faiss.write_index(
            self.index,
            "data/faiss.index"
        )


    def load(self):

        if not os.path.exists(
            "data/faiss.index"
        ):
            return False

        self.index = faiss.read_index(
            "data/faiss.index"
        )

        with open(
            "data/vector_store.pkl",
            "rb"
        ) as file:

            self.documents = pickle.load(file)

        return True
