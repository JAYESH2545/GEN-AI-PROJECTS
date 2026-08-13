from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil

app = FastAPI(title="Zero to GraphRAG - Document Upload")

# Folder where uploaded documents will be stored
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}


@app.get("/")
def home():
    return {
        "message": "Zero to GraphRAG document upload API",
        "upload_endpoint": "/upload"
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document and save it in the uploads/ folder.
    """

    # Get file extension
    extension = Path(file.filename).suffix.lower()

    # Check file type
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {extension} is not supported. "
                   f"Allowed types: {ALLOWED_EXTENSIONS}"
        )

    # Create the destination path
    destination = UPLOAD_DIR / file.filename

    # Save the uploaded file
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Document uploaded successfully",
        "filename": file.filename,
        "location": str(destination)
    }