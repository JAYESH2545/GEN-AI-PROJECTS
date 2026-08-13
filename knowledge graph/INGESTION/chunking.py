from pathlib import Path


def read_document(file_path: str) -> str:
    """
    Read a text document and return its contents.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return path.read_text(encoding="utf-8")


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50):
    """
    Split text into chunks.

    chunk_size = maximum number of words in each chunk
    overlap = number of words repeated between chunks
    """

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(words[start:end])

        chunks.append(chunk)

        # Move forward but keep some words from the previous chunk
        start = end - overlap

    return chunks


def chunk_document(file_path: str, chunk_size: int = 500, overlap: int = 50):
    """
    Read a document and split it into chunks.
    """

    text = read_document(file_path)

    return chunk_text(
        text,
        chunk_size=chunk_size,
        overlap=overlap
    )


if __name__ == "__main__":

    file_path = "uploads/apple.txt"

    chunks = chunk_document(file_path)

    for i, chunk in enumerate(chunks, start=1):
        print(f"\n--- Chunk {i} ---")
        print(chunk)