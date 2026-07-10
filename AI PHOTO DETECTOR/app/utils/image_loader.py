import io
from PIL import Image
import cv2
import numpy as np

def load_pillow_image(image_bytes: bytes) -> Image.Image:
    try:
     """Loads an image from bytes using Pillow."""
     image = Image.open(io.BytesIO(image_bytes))
     return image.convert('RGB')
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")
    

def load_opencv_image(image_bytes: bytes) -> np.ndarray:
    try:
        """Loads an image from bytes using OpenCV."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")
    return image

