from sentence_transformers import SentenceTransformer
from chunking import chunk_document


# Load the embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embeddings(chunks):
    """
    Convert text chunks into vector embeddings.
    """

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True
    )

    return embeddings


def embed_document(file_path):
    """
    Read a document, create chunks,
    and generate an embedding for each chunk.
    """

    # Get chunks from chunking.py
    chunks = chunk_document(file_path)

    # Convert chunks into vectors
    embeddings = create_embeddings(chunks)

    results = []

    for i, (chunk, embedding) in enumerate(
        zip(chunks, embeddings),
        start=1
    ):
        results.append({
            "chunk_id": i,
            "text": chunk,
            "embedding": embedding.tolist()
        })

    return results


if __name__ == "__main__":

    file_path = "uploads/apple.txt"

    results = embed_document(file_path)

    for item in results:

        print("\n--------------------")
        print("Chunk ID:", item["chunk_id"])
        print("Text:", item["text"])

        print("Vector:")
        print(item["embedding"])

        print("Vector dimensions:")
        print(len(item["embedding"]))