import time
import ollama
import faiss
import numpy as np
from pypdf import PdfReader

EMBED_MODEL = "qwen3-embedding:latest"
CHAT_MODEL = "qwen3:1.7b"

print("Embedding Model:", EMBED_MODEL)
print("Chat Model:", CHAT_MODEL)


def embed_chunks(texts, batch_size=2, retries=3):
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        for attempt in range(retries):
            try:
                response = ollama.embed(model=EMBED_MODEL,input=batch)
                all_embeddings.extend(response["embeddings"])
                break

            except Exception as e:
                print(f"Error embedding batch {i // batch_size + 1}: {e}")
                if attempt < retries - 1:
                    time.sleep(2)
                else:
                    raise

    return all_embeddings

chunk_embeddings = embed_chunks(pdf_chunks)
chunk_embeddings = np.array(chunk_embeddings, dtype="float32")

print("Embeddings generated:", chunk_embeddings.shape)
dimension = chunk_embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(chunk_embeddings)

print("FAISS index created. Total vectors:", index.ntotal)