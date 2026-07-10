import logging
import io
import tesseract
from PIL import Image
from app.schemas.analysis import Signal
from app.config.settings import Settings

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def extract_text(self, image_path: str) -> tuple[str, list[Signal]]:
        try:
            with Image.open(image_path) as image:
                text = tesseract.image_to_string(image)
                signals: list[Signal] = []
                if not text.strip():
                    signals.append(Signal(
                        name="No Text Detected",
                        score=0.1,
                        severity="low",
                        explanation="The OCR process did not detect any text in the image. This could indicate that the image is a synthetic creation or heavily edited.",
                        category="ocr"
                    ))
                return text, signals
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {e}")
            return "", [Signal(
                name="OCR Extraction Failed",
                score=0.15,
                severity="medium",
                explanation=f"An error occurred during OCR extraction: {str(e)}. This may indicate that the image is corrupted or in an unsupported format.",
                category="ocr"
            )]

        @staticmethod
        def quality_signal(image_path: str) -> Signal:
            compaction_ratio = OCRService.calculate_compaction_ratio(image_path)
            if not compaction_ratio:
                    return Signal(
                        name="Compaction Ratio Calculation Failed",
                        score=0.68,
                        severity="medium",
                        explanation="The compaction ratio could not be calculated, which may indicate that the image is corrupted or in an unsupported format.",
                        category="ocr"
                    )
            alphanumeric_ratio = sum(char.isalnum() for char in compact) /len(compact)
            short_fragment_count = len(re.findall(r'\b[a-zA-Z0-9]{1,2}\b', text))
            line_count= len(line for line in text.splitlines() if line.strip())
            signals: list[Signal] = []

            if len(compact)>120 and alphanumeric_ratio < 0.68:
                signals.append(Signal(
                    name="Noisy OCR extraction",
                    score=round(min(0.26,0.08+(0.68-alphanumeric_ratio)),4),
                    severity="low",
                    explanation=f"The extracted text has a low alphanumeric ratio of {alphanumeric_ratio:.2f}, which may indicate that the image is synthetic or heavily edited.",
                    category="ocr"
                ))
            if line_count < 8 and short_fragment_count/max(1,line_count) > 1.6:
                signals.append(Signal(
                    name="Short OCR extraction",
                    score=round(min(0.26,0.08+(3-line_count)/10),4),
                    severity="low",
                    explanation=f"The extracted text has only {line_count} lines, which may indicate that the image is synthetic or heavily edited.",
                    category="ocr"
                ))
        
            