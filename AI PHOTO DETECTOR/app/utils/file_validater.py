import io
from pathlib import Path
from PIL import Image
from app.core.config import Settings
from app.core.exceptions import InvalidFileTypeError

def validate_image_file(filename: str,
                        content_type: str,
                        content: bytes,
                        settings: Settings) -> None:

    if not filename:
        raise InvalidFileTypeError("Filename is missing.")
    extension = Path(filename).suffix.lower().lstrip('.')

    if extension not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise InvalidFileTypeError(f"Invalid file extension: {extension}. Allowed extensions are: {settings.ALLOWED_IMAGE_EXTENSIONS}")
    
    if content_type not in settings.ALLOWED_IMAGE_MIME_TYPES:
        raise InvalidFileTypeError(f"Invalid content type: {content_type}. Allowed content types are: {settings.ALLOWED_IMAGE_MIME_TYPES}")
    
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024 

    if len(content) > max_bytes:
        raise InvalidFileTypeError(f"File size exceeds the maximum limit of {settings.MAX_IMAGE_SIZE_MB} MB.")

    if not content:
        raise InvalidFileTypeError("File content is empty.")

    try:
        image = Image.open(io.BytesIO(content))
        image.verify()  # Verify that it's a valid image

    except Exception as e:
        raise InvalidFileTypeError(f"Invalid image file: {e}")
