from pathlib import Path

from pypdf import PdfReader
from docx import Document


# ==========================================
# UPLOAD DIRECTORY
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = PROJECT_DIR / "uploads"


# ==========================================
# READ TXT
# ==========================================

def read_txt(file_path: Path) -> str:

    return file_path.read_text(
        encoding="utf-8"
    )


# ==========================================
# READ PDF
# ==========================================

def read_pdf(file_path: Path) -> str:

    reader = PdfReader(str(file_path))

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


# ==========================================
# READ DOCX
# ==========================================

def read_docx(file_path: Path) -> str:

    document = Document(str(file_path))

    paragraphs = []

    for paragraph in document.paragraphs:

        if paragraph.text.strip():
            paragraphs.append(
                paragraph.text
            )

    return "\n".join(paragraphs)


# ==========================================
# READ DOCUMENT
# ==========================================

def read_document(file_path: str) -> str:

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    extension = path.suffix.lower()

    if extension == ".txt":
        return read_txt(path)

    elif extension == ".pdf":
        return read_pdf(path)

    elif extension == ".docx":
        return read_docx(path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )


# ==========================================
# CHUNK TEXT
# ==========================================

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
):

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    words = text.split()

    chunks = []

    start = 0

    while start < len(words):

        end = start + chunk_size

        chunk = " ".join(
            words[start:end]
        )

        if chunk.strip():
            chunks.append(chunk)

        start = end - overlap

    return chunks


# ==========================================
# CHUNK DOCUMENT
# ==========================================

def chunk_document(
    file_path: str,
    chunk_size: int = 500,
    overlap: int = 50
):

    text = read_document(file_path)

    if not text.strip():
        raise ValueError(
            f"No text extracted from {file_path}"
        )

    chunks = chunk_text(
        text,
        chunk_size=chunk_size,
        overlap=overlap
    )

    return chunks


# ==========================================
# FIND UPLOADED DOCUMENT
# ==========================================

def get_uploaded_documents():

    allowed_extensions = {
        ".txt",
        ".pdf",
        ".docx"
    }

    if not UPLOAD_DIR.exists():
        return []

    return [
        file
        for file in UPLOAD_DIR.iterdir()
        if (
            file.is_file()
            and file.suffix.lower()
            in allowed_extensions
        )
    ]


# ==========================================
# PROCESS DOCUMENT
# ==========================================

def process_document(file_path):

    chunks = chunk_document(
        file_path
    )

    # --------------------------------------
    # Simple output
    # --------------------------------------

    print()
    print(
        f"✓ Chunking completed: {file_path.name}"
    )

    print(
        f"  Total chunks: {len(chunks)}"
    )

    # Show only 2 samples

    for i, chunk in enumerate(
        chunks[:2],
        start=1
    ):

        print()
        print(
            f"  Sample chunk {i}:"
        )

        print(
            f"  {chunk[:300]}..."
        )

    print()

    # --------------------------------------
    # Send chunks to embedding/vector stage
    # --------------------------------------

    return chunks


# ==========================================
# MAIN
# ==========================================

if __name__ == "__main__":

    documents = get_uploaded_documents()

    if not documents:

        print(
            "No documents found in uploads/"
        )

        raise SystemExit(0)


    for file_path in documents:

        try:

            chunks = process_document(
                file_path
            )

            # --------------------------------
            # NEXT STEP
            # --------------------------------
            #
            # Later:
            #
            # vectors = create_embeddings(chunks)
            #
            # --------------------------------

        except Exception as e:

            print(
                f"✗ Failed: {file_path.name}"
            )

            print(
                f"  Error: {e}"
            )