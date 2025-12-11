from typing import Iterable, List, Dict, Optional, Tuple, Any

import cv2
import numpy as np
from PIL import Image
from paddleocr import PaddleOCR


# Initialize PaddleOCR once.
# PaddleOCR 3.x deprecates `use_angle_cls`; use `use_textline_orientation` instead.
_ocr = PaddleOCR(use_textline_orientation=False, lang="en")


def _pil_to_bgr(image: Image.Image) -> np.ndarray:
	return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2BGR)


def _iter_ocr_items(results: Any) -> Iterable[Tuple[Optional[np.ndarray], str, Optional[float]]]:
	"""Yield (polygon, text, score) tuples from PaddleOCR outputs.

	Supports PaddleOCR 3.x `predict()` (list[dict]) and older-style (list[list[...]]).
	"""

	if isinstance(results, list) and results and isinstance(results[0], dict):
		for page in results:
			texts = page.get("rec_texts") or []
			scores = page.get("rec_scores") or []

			polys = page.get("rec_polys")
			if not polys:
				polys = page.get("dt_polys") or []

			for i, text in enumerate(texts):
				if not text:
					continue
				score = float(scores[i]) if i < len(scores) else None
				poly = polys[i] if i < len(polys) else None
				yield (np.asarray(poly) if poly is not None else None), text, score
		return

	for res in results or []:
		for box, (text, score) in res:
			if not text:
				continue
			yield np.asarray(box), text, float(score) if score is not None else None


def run_ocr_best_config(image: Image.Image) -> str:
	"""Run PaddleOCR and return concatenated text lines."""

	bgr = _pil_to_bgr(image)

	# PaddleOCR.predict() does not accept `cls`; orientation is controlled by init flags.
	results = _ocr.predict(bgr)

	lines: List[str] = [text for _, text, _ in _iter_ocr_items(results)]
	return "\n".join(lines)


def get_boxes(image: Image.Image, psm: int = 6) -> List[Dict]:  # psm kept for API parity
	bgr = _pil_to_bgr(image)
	results = _ocr.predict(bgr)

	boxes: List[Dict] = []
	for poly, text, score in _iter_ocr_items(results):
		if poly is None:
			continue

		pts = np.asarray(poly, dtype=float).reshape(-1, 2)
		xs = pts[:, 0]
		ys = pts[:, 1]
		left = float(xs.min())
		top = float(ys.min())
		width = float(xs.max() - left)
		height = float(ys.max() - top)

		boxes.append(
			{
				"text": text,
				"left": int(left),
				"top": int(top),
				"width": int(width),
				"height": int(height),
				"conf": float(score) if score is not None else 0.0,
			}
		)

	return boxes
