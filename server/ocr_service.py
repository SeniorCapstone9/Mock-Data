import os

import fitz  # pymupdf
from PIL import Image
from ocr_engine import run_ocr_best_config

class OCRService:
    def __init__(self):
        print("Initializing OCR Service (Typed Text Mode)...")
        # OCR is intentionally centralized in `ocr_engine.py`.
        # This service handles file/PDF orchestration and delegates preprocessing to `preprocess.py`.
        print("OCR Service Initialized")

    def process_pdf(self, pdf_path):
        """
        Converts PDF pages to images and processes them.
        """
        print(f"Processing PDF: {pdf_path}")
        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            print(f"Failed to open PDF: {e}")
            return "Error: Could not open PDF file."

        full_text = []
        
        for page_num in range(len(doc)):
            print(f"Processing Page {page_num + 1}/{len(doc)}")
            temp_img_path = None
            try:
                page = doc.load_page(page_num)
                
                # Render page to image (2x zoom for better resolution)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) 
                
                # Save temp file
                temp_img_path = f"{pdf_path}_page_{page_num}.png"
                pix.save(temp_img_path)
                
                # Process the temporary image
                page_text = self.process_image(temp_img_path)
                
                header = f"--- Page {page_num+1} ---"
                full_text.append(f"{header}\n{page_text}")
                
            except Exception as e:
                print(f"Error processing page {page_num}: {e}")
                full_text.append(f"--- Page {page_num+1} (Error) ---")
            finally:
                # Cleanup temp file
                if temp_img_path and os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                    
        return "\n\n".join(full_text)

    def process_image(self, image_path):
        """
        Runs full OCR (Detection + Recognition) on the image.
        """
        if image_path.lower().endswith('.pdf'):
            return self.process_pdf(image_path)

        print(f"Scanning image: {image_path}")
        try:
            img = Image.open(image_path).convert("RGB")
            final_text = run_ocr_best_config(img)
            print("Scan complete.")
            return final_text

        except Exception as e:
            print(f"OCR Failed: {e}")
            return f"Error scanning image: {str(e)}"

# Global instance
ocr_service = None

def get_ocr_service():
    global ocr_service
    if ocr_service is None:
        ocr_service = OCRService()
    return ocr_service
