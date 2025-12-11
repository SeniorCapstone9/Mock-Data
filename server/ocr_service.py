import os
import fitz # pymupdf
from paddleocr import PaddleOCR

class OCRService:
    def __init__(self):
        print("Initializing OCR Service (Typed Text Mode)...")
        # Initialize PaddleOCR for both detection and recognition
        # use_angle_cls=True handles rotated text
        self.engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        print("OCR Service Initialized: PaddleOCR")

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
                if os.path.exists(temp_img_path):
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
            # PaddleOCR.ocr returns a list of results.
            # result structure: [ [ [ [x1,y1]..], "text", confidence ], ... ]
            # The 'cls' arg enables angle classification.
            result = self.engine.ocr(image_path, cls=True)
            
            extracted_lines = []
            
            # Paddle's result can be nested like [ [line1], [line2] ] or None if no text found
            if result and result[0]:
                for line in result[0]:
                    # line[1] is the ("text", confidence) tuple
                    text_content = line[1][0]
                    extracted_lines.append(text_content)
            
            final_text = "\n".join(extracted_lines)
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
