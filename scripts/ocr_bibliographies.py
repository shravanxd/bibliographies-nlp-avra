import os
import sys
from pdf2image import convert_from_path, pdfinfo_from_path
import pytesseract

def ocr_pdf_chunked(pdf_path, output_txt_path, chunk_size=10):
    print(f"Processing {pdf_path}...")
    try:
        # Get total pages
        info = pdfinfo_from_path(pdf_path)
        total_pages = info["Pages"]
        print(f"  Total pages: {total_pages}")
        
        # clear output file
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write("")

        for i in range(1, total_pages + 1, chunk_size):
            last_page = min(i + chunk_size - 1, total_pages)
            print(f"  Processing pages {i} to {last_page}...")
            
            images = convert_from_path(pdf_path, first_page=i, last_page=last_page)
            
            chunk_text = ""
            for j, image in enumerate(images):
                page_num = i + j
                print(f"    OCR Page {page_num}")
                text = pytesseract.image_to_string(image)
                chunk_text += text + "\n\f"
            
            with open(output_txt_path, 'a', encoding='utf-8') as f:
                f.write(chunk_text)
                
        print(f"  Completed. Saved to {output_txt_path}")
        
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ocr_bibliographies.py <pdf_file1> [pdf_file2 ...]")
        sys.exit(1)
        
    for pdf_file in sys.argv[1:]:
        if not os.path.exists(pdf_file):
            print(f"File not found: {pdf_file}")
            continue
            
        base_name = os.path.basename(pdf_file)
        root_name = os.path.splitext(base_name)[0]
        # output to data/text if it exists, else same dir
        output_dir = "data/text"
        if not os.path.exists(output_dir):
            output_dir = os.path.dirname(pdf_file)
            
        output_txt = os.path.join(output_dir, f"{root_name}_ocr.txt")
        ocr_pdf_chunked(pdf_file, output_txt)
