import os
import requests
import sys
from pypdf import PdfReader, PdfWriter
import time

# Unstructured API details provided by user
API_KEY = "eK5BM6c10LhR1PsjruHvLfINdM1s1H"
ENDPOINT = "https://api.unstructuredapp.io/general/v0/general"

def parse_chunk(pdf_chunk_path):
    print(f"  Requesting API for {pdf_chunk_path}...")
    headers = {
        "unstructured-api-key": API_KEY,
    }
    data = {
        "strategy": "hi_res",
        "coordinates": "false",
        "include_page_breaks": "true",
    }
    
    with open(pdf_chunk_path, "rb") as f:
        files = {"files": (os.path.basename(pdf_chunk_path), f, "application/pdf")}
        response = requests.post(ENDPOINT, headers=headers, files=files, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error from API: {response.status_code} - {response.text}")
        return None

def parse_pdf(pdf_path, output_path):
    print(f"Parsing {pdf_path} using Unstructured API...")
    
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")

    # Reduced chunk size for better visibility and reliability
    MAX_PAGES_PER_CHUNK = 20
    
    # Setup progress tracking
    basename = os.path.basename(pdf_path)
    progress_dir = os.path.join("data", "progress")
    if not os.path.exists(progress_dir):
        os.makedirs(progress_dir, exist_ok=True)
    progress_file = os.path.join(progress_dir, basename + "_uAPI.progress")

    start_page = 0
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as pf:
                start_page = int(pf.read().strip())
            print(f"Resuming from page {start_page + 1}...")
        except ValueError:
            pass

    # Initialize/Clear output file ONLY if starting from scratch
    if start_page == 0:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("")

    for i in range(start_page, total_pages, MAX_PAGES_PER_CHUNK):
        chunk_start = i
        chunk_end = min(i + MAX_PAGES_PER_CHUNK, total_pages)
        percent = (chunk_end / total_pages) * 100
        print(f"[{percent:6.2f}%] Processing pages {chunk_start + 1} to {chunk_end}...")

        chunk_pdf_path = f"temp_chunk_{chunk_start}_{chunk_end}.pdf"
        writer = PdfWriter()
        for j in range(chunk_start, chunk_end):
            writer.add_page(reader.pages[j])
        
        with open(chunk_pdf_path, "wb") as f_out:
            writer.write(f_out)

        elements = parse_chunk(chunk_pdf_path)
        
        # Cleanup temp file
        if os.path.exists(chunk_pdf_path):
            os.remove(chunk_pdf_path)

        if elements:
            chunk_text = ""
            for el in elements:
                chunk_text += el.get("text", "") + "\n"
            
            # Save INCREMENTALLY so you can check the file while it runs
            with open(output_path, "a", encoding="utf-8") as out:
                out.write(chunk_text)
            print(f"  Done. Segment saved to {output_path}")

            # Save progress
            with open(progress_file, 'w') as pf:
                pf.write(str(chunk_end))
        else:
            print(f"  CRITICAL: Failed to parse pages {chunk_start + 1}-{chunk_end}. Stopping.")
            return

        # Small delay between chunks to be safe
        time.sleep(2)

    # Done - clear progress file
    if os.path.exists(progress_file):
        os.remove(progress_file)

    print(f"\nFinal combined text successfully saved to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/unstructured_parse.py <pdf_path> [output_path]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        out_file = sys.argv[2]
    else:
        basename = os.path.basename(pdf_file)
        name = os.path.splitext(basename)[0]
        out_file = os.path.join("data", "text", f"{name}_uAPI.txt")

    parse_pdf(pdf_file, out_file)
