from PIL import Image, ExifTags
from app.schemas.analysis import Signal

class MetadataService:
    def analysis(self, image_path: str) -> tuple[dict[str, object], list[Signal]]:
        with Image.open(image_path) as image:
            metadata: dict[str, object] = {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "mode": image.mode,
            }

            signals: list[Signal] = []

            exif_data: dict[str, object] = {}
            exif = image._getexif() or {}

            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8', errors='ignore')
                except Exception:
                    value = str(value)

                exif_data[tag] = value
            
            metadata["exif"] = exif_data

            if not exif_data:
                signals.append(Signal(
                    name="No EXIF Metadata",
                    score=0.08,
                    severity="low",
                    explanation="The image is missing EXIF metadata, which may indicate that it has been edited or stripped of metadata for privacy reasons.",
                    category="metadata"
                ))
            elif "Software" in exif_data:
                signals.append(Signal(
                    name="Image Edited",
                    score=0.12,
                    severity="low",
                    explanation=f"The image contains EXIF metadata indicating it was edited with software: {exif_data['Software']}. This is a strong indicator that the image may have been manipulated.",
                    category="metadata"
                ))
            return metadata, signals
