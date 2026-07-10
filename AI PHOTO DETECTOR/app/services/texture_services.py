import cv2
import numpy as np
from app.schemas.analysis import Signal
class TextureService:
    def analyze_texture(self) -> dict[str, float]:
        self.img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        self.laplacian_matrix = cv2.Laplacian(self.img, cv2.CV_64F)
        self.blur_score = self.laplacian_matrix.var()

        metrics = {"blur_score": self.blur_score}

        signals: list[Signal] = []
    
        if self.blur_score < 1000:
            return {
                "signal": Signal(
                    name="low Contrast Texture",
                    score=0.2,
                    severity="medium",
                    explanation=f"The texture analysis shows a low contrast value of {self.blur_score:.2f}, which may indicate that the image is synthetic or can be AI-generated.",
                    category="texture"
                )
            }
        elif self.blur_score > 1000:
            return {
                "signal": Signal(
                    name="High Contrast Texture",
                    score=0.2,
                    severity="medium",
                    explanation=f"The texture analysis shows a high contrast value of {self.blur_score:.2f}, which may indicate that the image is not synthetic or AI-generated.",
                    category="texture"
                )
            }
        elif self.blur_score > 500:
            return {
                "signal": Signal(
                    name="Moderate Contrast Texture",
                    score=0.1,
                    severity="low",
                    explanation=f"The texture analysis shows a moderate contrast value of {self.blur_score:.2f}, which may indicate that the image is too blurry to determine if it is synthetic or AI-generated.",
                    category="texture"
                )
            }

    return signals, metrics
