import time
from enum import Enum
from PIL import Image
from manga_ocr import MangaOcr
import numpy as np
import cv2
import sys

from detector import detect_text
from apple_vision import AppleVisionOCR

# load the model once when the backend starts.

if sys.platform == "darwin":
    ocr = AppleVisionOCR(
        reading_order="vision",
        language="ja-JP",
        engine="visionkit",
        debug=True,
    )
elif sys.platform == "win32":
    ocr = MangaOcr()
else:
    raise RuntimeError("Unsupported operating system")

def recognize_text(image):
    return ocr(image)

# image utils
def pil_to_cv(image):
    arr = np.array(image.convert("RGB"))

    return cv2.cvtColor(
        arr,
        cv2.COLOR_RGB2BGR,
    )

class CaptureMode(str, Enum):
    PAGE = "page"
    TEXTBOX = "textbox"

# comic text detector expects cv format but manga ocr expects pil
# we convert the image to pil then to cv and we can use the original
# pil image later.
def detect_regions(image: Image.Image, captureMode: CaptureMode):

    image_width, image_height = image.size

    if (image_height < 10 or image_width < 10):
        return {
            "regions": [],
            "reason": "Selected image size too small.",
            "valid": False
        }

    if (captureMode == CaptureMode.TEXTBOX):
        if (image_height > 1200 or image_width > 1200):
            return {
                "regions": [],
                "reason": "Selected image size too large.",
                "valid": False
            }
        
        text = recognize_text(image).strip()

        if not text:
            return {
                "regions": [],
                "reason": "No text found.",
                "valid": False,
            }

        return {
            "regions": [
                {
                    "text": text,
                    "x": 0.0,
                    "y": 0.0,
                    "width": 1.0,
                    "height": 1.0,
                }
            ],
            "reason": None,
            "valid": True,
        }

    cv_image = pil_to_cv(image)

    # performance debug
    if __debug__:
        start = time.perf_counter()

    lines, classes, confidences = detect_text(cv_image)

    # performance debug
    if __debug__:
        print(
            "Detection:",
            time.perf_counter() - start,
            "seconds",
        )
    
    regions = []

    if (len(lines) == 0):
        return {
            "regions": [],
            "reason": "No text blocks detected.",
            "valid": False
        }
    
    # performance debug
    ocr_total = 0.0

    for line in lines:
        x1, y1, x2, y2 = line
        padding = 10
        crop = image.crop(
            (
                max(0, x1 - padding),
                max(0, y1 - padding),
                min(image_width, x2 + padding),
                min(image_height, y2 + padding),
            )
        )

        # performance debug
        if __debug__:
            start = time.perf_counter()

        text = recognize_text(crop).strip()

        # performance debug
        if __debug__:
            ocr_total += time.perf_counter() - start

        if not text:
            continue

        regions.append({
            "text": text,
            "x": x1 / image_width,
            "y": y1 / image_height,
            "width": (x2 - x1) / image_width,
            "height": (y2 - y1) / image_height,
        })

    if (len(regions) == 0):
        return {
            "regions": [],
            "reason": "No text found.",
            "valid": False
        }

    # performance debug
    if __debug__:
        print("Manga OCR Total:", ocr_total, "seconds")
        print("Manga OCR Individual:", ocr_total / len(regions), "seconds")

    return {
        "regions": regions,
        "reason": None,
        "valid": True
    }