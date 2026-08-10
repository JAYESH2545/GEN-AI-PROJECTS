from pypdf import PdfReader
from io import BytesIO

def load_and_chunk_pdf(pdf_bytes, chunk_size=1000, overlap=150):
    reader = PdfReader(BytesIO(pdf_bytes))

    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"

    chunks = []
    start = 0

    while start < len(full_text):
        end = start + chunk_size
        chunk = full_text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks