import cv2
import numpy as np
import os
from app.schemas.analysis import Signal
class ForensicService:

    def ELA(self, image_path: str, quality: int = 90) -> tuple[list[Signal], dict[str, float]]:

        original = cv2.imread(image_path)

        if original is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        encoded = cv2.imencode(".jpg", original, encode_param)
        
        recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

        ela_map = cv2.absdiff(original, recompressed)

        max_diff = float(np.max(ela_map))
        mean_diff = float(np.mean(ela_map))

        metrics = {
            "max_diff": max_diff,
            "mean_diff": mean_diff,
        }

        signals: list[Signal] = []

        if mean_diff > 15:
            signals.append(
                Signal(
                    name="High ELA Variation",
                    score=0.8,
                    severity="high",
                    explanation=f"ELA mean difference is {mean_diff:.2f}. High variation may indicate manipulation.",
                    category="forensics",
                )
            )
        elif mean_diff < 5:
            signals.append(
                Signal(
                    name="Low ELA Variation",
                    score=0.1,
                    severity="low",
                    explanation=f"ELA mean difference is {mean_diff:.2f}. Compression appears consistent.",
                    category="forensics",
                )
            )
        else:
            signals.append(
                Signal(
                    name="Moderate ELA Variation",
                    score=0.4,
                    severity="medium",
                    explanation=f"ELA mean difference is {mean_diff:.2f}. Results are inconclusive.",
                    category="forensics",
                )
            )

        return signals, metrics

    def jpeg_consistency_analysis(self, image_path: str, quality: int = 90) -> tuple[list[Signal], dict[str, float]]:

        image = cv2.imread(image_path)

        if image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        _, encoded = cv2.imencode(".jpg", image, encode_param)

        recompressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

        diff = cv2.absdiff(image, recompressed).astype(np.float32)

        mean_diff = float(np.mean(diff))
        std_diff = float(np.std(diff))

        metrics = {
            "mean_difference": mean_diff,
            "std_difference": std_diff,
        }

        signals: list[Signal] = []

        if std_diff > 10:
            signals.append(
                Signal(
                    name="JPEG Compression Inconsistency",
                    score=0.75,
                    severity="high",
                    explanation=(
                        f"JPEG recompression differences show high variance "
                        f"({std_diff:.2f}), which may indicate edited regions."
                    ),
                    category="forensics",
                )
            )
        else:
            signals.append(
                Signal(
                    name="JPEG Compression Consistent",
                    score=0.2,
                    severity="low",
                    explanation=(
                        f"JPEG recompression variance ({std_diff:.2f}) appears uniform."
                    ),
                    category="forensics",
                )
            )

        return signals, metrics

    def noise_consistency_analysis(self, image_path: str, block_size: int = 16) -> tuple[list[Signal], dict[str, float]]:

        image = cv2.imread(image_path)

        if image is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        noise_residual = cv2.GaussianBlur(gray, (5, 5), 0)
        noise_residual = cv2.absdiff(gray, noise_residual)

        h, w = noise_residual.shape

        var_values = []

        for i in range(0, h - block_size + 1, block_size):
            for j in range(0, w - block_size + 1, block_size):

                block = noise_residual[
                    i:i + block_size, j:j + block_size]

                var_values.append(np.var(block))

        var_values = np.array(var_values)

        mean_variance = float(np.mean(var_values))
        std_variance = float(np.std(var_values))

        metrics = {
            "mean_noise_variance": mean_variance,
            "std_noise_variance": std_variance,
        }

        signals: list[Signal] = []

        if std_variance > 100:
            signals.append(
                Signal(
                    name="Noise Inconsistency Detected",
                    score=0.8,
                    severity="high",
                    explanation=(
                        f"Noise variance varies significantly across the image (std={std_variance:.2f}), which may indicate splicing or object insertion."),
                    category="forensics",
                )
            )
        else:
            signals.append(
                Signal(
                    name="Noise Pattern Consistent",
                    score=0.2,
                    severity="low",
                    explanation=(
                        f"Noise distribution appears relatively uniform "
                        f"(std={std_variance:.2f})."
                    ),
                    category="forensics",
                )
            )

        return signals, metrics