import sys
import os

print("Verifying imports...")
try:
    import paddle
    import paddleocr
    import transformers
    import torch
    import cv2
    from PIL import Image
    print("Dependencies imported successfully.")
    
    from ocr_service import OCRService
    print("OCRService imported successfully.")
    
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
