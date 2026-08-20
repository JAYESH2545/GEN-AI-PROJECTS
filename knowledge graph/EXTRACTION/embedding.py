import sys
import time
from pathlib import Path

import numpy as np
import ollama


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
# OLLAMA CONFIG
# ============================================================

EMBED_MODEL = "qwen3-embedding:4b"

# Local model calls have no network layer to time out on their own, so
# a stuck/overloaded Ollama server can hang a batch forever without
# this. app.py serializes every Ollama call behind one lock, so a hang
# here would freeze fact extraction and querying for every job too.
OLLAMA_TIMEOUT = 120

ollama_client = ollama.Client(timeout=OLLAMA_TIMEOUT)


# ============================================================
# CREATE EMBEDDINGS
# ============================================================

def create_embeddings(chunks, batch_size=8, retries=3, on_batch_done=None):
    """
    Convert text chunks into vector embeddings via Ollama.

    Returns a 2D numpy array (rows support `.tolist()`), matching the
    interface the previous sentence-transformers model exposed, so
    callers (app.py, embed_document below) need no changes.

    Batches are retried with backoff on transient failures. A batch
    that still fails after all retries raises, so the caller can skip
    just that document/job instead of silently storing wrong vectors.

    A single call for a whole document can legitimately take minutes
    (qwen3-embedding:4b is far slower than the old local MiniLM model,
    more so with concurrent jobs queued behind the same Ollama model).
    Without per-batch feedback that looks identical to a hang from the
    caller's side. If given, `on_batch_done(batches_done, total_batches)`
    is called after each batch so a caller can report real progress.
    """

    all_embeddings = []
    total_batches = (len(chunks) + batch_size - 1) // batch_size

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        last_error = None

        for attempt in range(retries):
            try:
                response = ollama_client.embed(
                    model=EMBED_MODEL,
                    input=batch
                )
                all_embeddings.extend(response["embeddings"])
                break

            except Exception as e:
                last_error = e

                print(
                    f"  Embedding batch {i // batch_size + 1} failed "
                    f"(attempt {attempt + 1}/{retries}): {e}"
                )

                if attempt < retries - 1:
                    time.sleep(2 * (attempt + 1))

        else:
            raise RuntimeError(
                f"Embedding batch {i // batch_size + 1} "
                f"failed after {retries} attempts"
            ) from last_error

        if on_batch_done is not None:
            on_batch_done(i // batch_size + 1, total_batches)

    return np.array(all_embeddings, dtype="float32")


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
# CHECK OLLAMA
# ============================================================

def check_ollama():

    print("\nChecking Ollama...")

    try:

        models = ollama.list()

        installed_models = [model.model for model in models.models]

        if not any(EMBED_MODEL in model for model in installed_models):

            print(f"\nModel '{EMBED_MODEL}' is not installed.")
            print(f"Run:\nollama pull {EMBED_MODEL}")

            return False

        print("✓ Ollama is ready.")
        print(f"✓ Model: {EMBED_MODEL}")

        return True

    except Exception as e:

        print("\nCould not connect to Ollama.")
        print(e)
        print("\nMake sure Ollama is installed and running.")

        return False


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

    if not check_ollama():
        raise SystemExit(1)

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
