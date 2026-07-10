import cv2
import numpy as np
import os
from app.schemas.analysis import Signal

def frequency_analysis(self, image_path: str) -> tuple[list[Signal], dict[str, float]]:

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    fft = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft)

    magnitude = np.abs(fft_shift)
    magnitude = np.log1p(magnitude)

    h, w = magnitude.shape

    center_y = h // 2
    center_x = w // 2

    radius = min(h, w) // 8

    y, x = np.ogrid[:h, :w]

    mask = ((x - center_x) ** 2 +(y - center_y) ** 2) <= radius ** 2

    low_frequency_energy = float(np.sum(magnitude[mask]))
    high_frequency_energy = float(np.sum(magnitude[~mask]))

    energy_ratio = (high_frequency_energy /(low_frequency_energy + 1e-8))

    metrics = {
        "low_frequency_energy": low_frequency_energy,
        "high_frequency_energy": high_frequency_energy,
        "energy_ratio": energy_ratio,
    }

    signals: list[Signal] = []

    if energy_ratio > 8.0:
        signals.append(
            Signal(
                name="Abnormal High Frequency Content",
                score=0.8,
                severity="high",
                explanation=(f"High-frequency energy ratio is{energy_ratio:.2f}, indicating unusual detailor possible image manipulation."), 
                category="forensics",
            )
        )

    elif energy_ratio < 3.0:
        signals.append(
            Signal(
                name="Frequency Distribution Consistent",
                score=0.2,
                severity="low",
                explanation=(f"Frequency energy ratio is {energy_ratio:.2f}, appearing normal."),
                category="forensics",
            )
        )

    else:
        signals.append(
            Signal(
                name="Moderate Frequency Anomaly",
                score=0.4,
                severity="medium",
                explanation=(
                    f"Frequency energy ratio is {energy_ratio:.2f}. Results are inconclusive."),
                category="forensics",
            )
        )

    return signals, metrics

def lighting_consistency_analysis(self, image_path: str, block_size: int = 32) -> tuple[list[Signal], dict[str, float]]:

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

    lightness = lab[:, :, 0]

    grad_x = cv2.Sobel(lightness,cv2.CV_64F,1,0, ksize=3)

    grad_y = cv2.Sobel(lightness,cv2.CV_64F,0,1,ksize=3)

    gradient_magnitude = np.sqrt(grad_x ** 2 +grad_y ** 2)

    h, w = gradient_magnitude.shape

    block_means = []

    for y in range(0, h - block_size + 1, block_size):
        for x in range(0, w - block_size + 1, block_size):

            block = gradient_magnitude[y:y + block_size, x:x + block_size]
            block_means.append(np.mean(block))

    block_means = np.array(block_means)

    mean_gradient = float(np.mean(block_means))
    std_gradient = float(np.std(block_means))

    consistency_score = float(
        mean_gradient / (std_gradient + 1e-8)
    )

    metrics = {
        "mean_gradient": mean_gradient,
        "std_gradient": std_gradient,
        "lighting_consistency_score": consistency_score,
    }

    signals: list[Signal] = []

    if std_gradient > 20:
        signals.append(
            Signal(
                name="Lighting Inconsistency Detected",
                score=0.8,
                severity="high",
                explanation=(
                    f"Lighting gradients vary significantly across the image (std={std_gradient:.2f}), which may indicate object insertion or compositing."),
                category="forensics",
            )
        )

    elif std_gradient < 8:
        signals.append(
            Signal(
                name="Lighting Appears Consistent",
                score=0.2,
                severity="low",
                explanation=(
                    f"Lighting gradients are relatively uniform (std={std_gradient:.2f})."),
                category="forensics",
            )
        )

    else:
        signals.append(
            Signal(
                name="Moderate Lighting Variation",
                score=0.4,
                severity="medium",
                explanation=(
                    f"Lighting variation is moderate (std={std_gradient:.2f})." ),
                category="forensics",
            )
        )

    return signals, metrics


def resampling_detection(self, image_path: str) -> tuple[list[Signal], dict[str, float]]:

    image = cv2.imread(image_path)

    if image is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    sobel_x = cv2.Sobel(gray,cv2.CV_64F,1,0, ksize=3)

    sobel_y = cv2.Sobel(gray,cv2.CV_64F,0,1,ksize=3)

    edge_response = np.sqrt(sobel_x ** 2 +sobel_y ** 2)

    fft = np.fft.fft2(edge_response)
    fft_shift = np.fft.fftshift(fft)

    magnitude = np.abs(fft_shift)
    magnitude = np.log1p(magnitude)

    mean_spectrum = float(np.mean(magnitude))
    max_spectrum = float(np.max(magnitude))
    std_spectrum = float(np.std(magnitude))

    periodicity_score = float(
        max_spectrum /
        (mean_spectrum + 1e-8)
    )

    metrics = {
        "mean_spectrum": mean_spectrum,
        "max_spectrum": max_spectrum,
        "std_spectrum": std_spectrum,
        "periodicity_score": periodicity_score,
    }

    signals: list[Signal] = []

    if periodicity_score > 12:
        signals.append(
            Signal(
                name="Resampling Artifacts Detected",
                score=0.85,
                severity="high",
                explanation=(f"Strong periodic frequency peaks detected (score={periodicity_score:.2f}), which may indicate image scaling or geometric transformation."),
                category="forensics",
            )
        )

    elif periodicity_score < 6:
        signals.append(
            Signal(
                name="No Significant Resampling Artifacts",
                score=0.2,
                severity="low",
                explanation=(f"Frequency periodicity appears normal (score={periodicity_score:.2f})."),
                category="forensics",
            )
        )

    else:
        signals.append(
            Signal(
                name="Moderate Resampling Evidence",
                score=0.4,
                severity="medium",
                explanation=(f"Some periodic frequency patterns were observed (score={periodicity_score:.2f})."
                ),
                category="forensics",
            )
        )

    return signals, metrics

