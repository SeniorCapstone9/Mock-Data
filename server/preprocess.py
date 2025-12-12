import cv2
import numpy as np
from PIL import Image
from typing import List, Optional

try:
    from pdf2image import convert_from_path
except ImportError:  # Gracefully handle optional dependency until installed
    convert_from_path = None


def load_image(path: str) -> Image.Image:
    return Image.open(path)


def pil_to_cv(image: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def cv_to_pil(image: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))


def to_grayscale(image: Image.Image) -> Image.Image:
    return image.convert("L")


def adaptive_threshold(gray: Image.Image) -> Image.Image:
    cv_img = np.array(gray)
    thr = cv2.adaptiveThreshold(
    cv_img, 255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    21, 10
)
    return Image.fromarray(thr)


def denoise(binary: Image.Image) -> Image.Image:
    cv_img = np.array(binary)
    kernel = np.ones((2, 2), np.uint8)
    opened = cv2.morphologyEx(cv_img, cv2.MORPH_OPEN, kernel)
    return Image.fromarray(opened)


def normalize_lighting(image: np.ndarray) -> np.ndarray:
    """Flatten shadows/bright spots common in photographed pages."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    background = cv2.medianBlur(gray, 31)
    normalized = cv2.divide(gray, background, scale=255)
    return normalized


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """Boost contrast while keeping noise controlled via CLAHE."""
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def deskew(image: Image.Image) -> Image.Image:
    gray = np.array(image.convert("L"))

    edges = cv2.Canny(gray, 50, 150)

    coords = np.column_stack(np.where(edges > 0))
    if coords.size == 0:
        return image

    rect = cv2.minAreaRect(coords)
    angle = rect[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = gray.shape
    center = (w // 2, h // 2)

    # Compute rotation matrix and expand canvas so that rotated content is not cropped
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    cos = abs(M[0, 0])
    sin = abs(M[0, 1])

    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))

    # Adjust translation to keep image centered in the new canvas
    M[0, 2] += (new_w / 2) - center[0]
    M[1, 2] += (new_h / 2) - center[1]

    rotated = cv2.warpAffine(
        np.array(image),
        M,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return Image.fromarray(rotated)



def resize_for_ocr(image: Image.Image, min_dim: int = 1500) -> Image.Image:
    w, h = image.size
    if max(w, h) >= min_dim:
        return image
    scale = min_dim / max(w, h)
    new_size = (int(w * scale), int(h * scale))
    return image.resize(new_size, Image.LANCZOS)


def crop_to_content(image: Image.Image, pad: int = 12, threshold: int = 250) -> Image.Image:
    """Tightly crop around non-background pixels.

    Args:
        image: PIL RGB or grayscale image.
        pad: Extra pixels to keep around detected content.
        threshold: Pixels darker than this are considered content (0-255).
    """
    gray = np.array(to_grayscale(image))
    mask = gray < threshold
    if not np.any(mask):
        return image  # nothing to crop

    coords = np.argwhere(mask)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)

    # Apply padding and clamp to image bounds
    y0 = max(0, y0 - pad)
    x0 = max(0, x0 - pad)
    y1 = min(gray.shape[0] - 1, y1 + pad)
    x1 = min(gray.shape[1] - 1, x1 + pad)

    cropped = image.crop((x0, y0, x1 + 1, y1 + 1))
    return cropped


def _border_stats(gray: np.ndarray) -> tuple:
    h, w = gray.shape
    margin_h = max(5, h // 20)
    margin_w = max(5, w // 20)
    top = gray[:margin_h, :]
    bottom = gray[-margin_h:, :]
    left = gray[:, :margin_w]
    right = gray[:, -margin_w:]
    border = np.concatenate([top.ravel(), bottom.ravel(), left.ravel(), right.ravel()])
    mean = float(border.mean())
    std = float(border.std())
    return mean, std


def has_light_text_on_dark_background(image: Image.Image) -> bool:
    gray = np.array(to_grayscale(image))
    bg_mean, bg_std = _border_stats(gray)

    if bg_mean >= 150 or bg_std >= 20:
        return False

    bright_mask = gray > (bg_mean + 25)
    dark_mask = gray < (bg_mean - 25)
    total = gray.size
    bright_ratio = float(np.count_nonzero(bright_mask)) / total
    dark_ratio = float(np.count_nonzero(dark_mask)) / total

    return bright_ratio > 0.02 and bright_ratio > (dark_ratio * 1.2)


def minimal_preprocess(image: Image.Image) -> Image.Image:
    print("Applied minimal preprocessing for light text on dark background.")
    return to_grayscale(image)

def preprocess_handwritten(image: Image.Image) -> Image.Image:
    """Preprocessing tuned for handwritten notes on lined paper.

    - Keep more stroke detail (no aggressive morphological opening)
    - Slight blur + Otsu threshold to separate ink from paper/lines
    """
    image = image.convert("RGB")
    img = deskew(image)
    img = resize_for_ocr(img, min_dim=1800)
    gray = np.array(to_grayscale(img))

    # Gentle Gaussian blur to reduce noise while keeping strokes
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu threshold tends to work better for pen on paper
    _, thr = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Try to suppress horizontal ruling lines (lined paper)
    h, w = thr.shape
    line_kernel_width = max(30, w // 4)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (line_kernel_width, 1))
    detected_lines = cv2.morphologyEx(thr, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    no_lines = cv2.subtract(thr, detected_lines)

    # Light dilation to reconnect broken pen strokes
    stroke_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    enhanced = cv2.dilate(no_lines, stroke_kernel, iterations=1)

    print("Applied handwritten preprocessing pipeline (with line suppression).")
    return Image.fromarray(enhanced)


def preprocess_image(image: Image.Image) -> Image.Image:
    image = image.convert("RGB")

    if has_light_text_on_dark_background(image):
        return minimal_preprocess(image)

    # Keep preprocessing general and lightweight: deskew, modest upsize, contrast, simple threshold.
    img = deskew(image)
    img = resize_for_ocr(img, min_dim=1500)

    gray = np.array(to_grayscale(img))
    boosted = enhance_contrast(gray)

    # Use Otsu for broad applicability across scans and photos.
    _, thr = cv2.threshold(boosted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    cleaned = denoise(Image.fromarray(thr))
    print("Applied general-purpose preprocessing pipeline.")
    return cleaned



def full_pipeline(path: str) -> Image.Image:
    return preprocess_image(load_image(path))


def load_pdf_pages(path: str, dpi: int = 300, poppler_path: Optional[str] = None) -> List[Image.Image]:
    if convert_from_path is None:
        raise ImportError("pdf2image is required for PDF support. Install it via pip install pdf2image and ensure Poppler is available.")
    return convert_from_path(path, dpi=dpi, poppler_path=poppler_path)
