import cv2
import numpy as np 
from app.schemas.analysis import Signal

class EdgeServices:
    def analyze(self, image_path: str) -> list[Signal]:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            edges = cv2.Canny(gray_image, 100, 200)

            density = float(np.count_nonzero(edges)/ edges.size)

            metrics = {"edge_density": density }

            signals: list[Signal] = []

            if density< 0.025:
                signals.append(Signal(
                    name="Low Edge Density",
                    score=0.2,
                    severity="medium",
                    explanation=f"The edge density of the image is {density:.4f}, which is below the threshold of 0.025. This may indicate that the image is synthetic or heavily edited.",
                    category="edge"
                ))
            elif density> 0.15:
                signals.append(Signal(
                    name="High Edge Density",
                    score=0.2,
                    severity="medium",
                    explanation=f"The edge density of the image is {density:.4f}, which is above the threshold of 0.15. This may indicate that the image is synthetic or heavily edited.",
                    category="edge"
                ))
            return signals,metrics