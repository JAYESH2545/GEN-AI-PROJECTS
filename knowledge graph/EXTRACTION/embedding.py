from sentence_transformers import SentenceTransformer

import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Allow Python to find INGESTION/
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# IMPORT CHUNKING FUNCTIONS
# ============================================================

from INGESTION.chunking import (
    get_uploaded_documents,
    chunk_document
)


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print("Loading embedding model...")

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

print("✓ Embedding model loaded")


# ============================================================
# CREATE EMBEDDINGS
# ============================================================

def create_embeddings(chunks):
    """
    Convert text chunks into vector embeddings.
    """

    embeddings = model.encode(
        chunks,
        convert_to_numpy=True
    )

    return embeddings


# ============================================================
# EMBED ONE DOCUMENT
# ============================================================

def embed_document(file_path):
    """
    Read a document, create chunks,
    and generate an embedding for every chunk.
    """

    # --------------------------------------------------------
    # Get chunks from chunking.py
    # --------------------------------------------------------

    chunks = chunk_document(
        file_path
    )

    if not chunks:
        raise ValueError(
            f"No chunks created for {file_path}"
        )


    # --------------------------------------------------------
    # Convert chunks into vectors
    # --------------------------------------------------------

    embeddings = create_embeddings(
        chunks
    )


    # --------------------------------------------------------
    # Combine chunk + embedding
    # --------------------------------------------------------

    results = []

    for chunk_id, (chunk, embedding) in enumerate(
        zip(chunks, embeddings),
        start=1
    ):

        results.append({

            "chunk_id": chunk_id,

            "text": chunk,

            "embedding": embedding.tolist()

        })


    return results


# ============================================================
# PROCESS ALL UPLOADED DOCUMENTS
# ============================================================

def process_uploaded_documents():

    documents = get_uploaded_documents()


    if not documents:

        print()
        print("No documents found in uploads/")

        return []


    all_results = []


    # --------------------------------------------------------
    # Process every uploaded document
    # --------------------------------------------------------

    for file_path in documents:

        print()
        print("=" * 60)

        print(
            f"Embedding: {file_path.name}"
        )

        print("=" * 60)


        try:

            results = embed_document(
                file_path
            )


            all_results.extend(
                results
            )


            # ------------------------------------------------
            # Success message
            # ------------------------------------------------

            print(
                "✓ Embedding completed"
            )

            print(
                f"  Total chunks: {len(results)}"
            )


            # ------------------------------------------------
            # Show only 2 samples
            # ------------------------------------------------

            for item in results[:2]:

                print()

                print(
                    f"  Chunk ID: {item['chunk_id']}"
                )

                print(
                    f"  Text: "
                    f"{item['text'][:200]}..."
                )

                print(
                    f"  Vector dimensions: "
                    f"{len(item['embedding'])}"
                )

                print(
                    f"  Vector sample: "
                    f"{item['embedding'][:5]}"
                )


        except Exception as e:

            print()

            print(
                f"✗ Failed: {file_path.name}"
            )

            print(
                f"  Error: {e}"
            )


    return all_results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    results = process_uploaded_documents()


    print()
    print("=" * 60)

    print(
        "EMBEDDING COMPLETE"
    )

    print("=" * 60)

    print(
        f"Total embedded chunks: "
        f"{len(results)}"
    )