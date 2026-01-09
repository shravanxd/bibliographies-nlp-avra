import os
import sys
import json
import pandas as pd
from openai import OpenAI

# Initialize client (expects OPENAI_API_KEY in env)
client = OpenAI()

import re

def sanitize_text(text):
    # Remove control characters but keep newlines and tabs
    return "".join(ch for ch in text if ch == '\n' or ch == '\t' or ch >= ' ')

REQUIRED_COLUMNS = [
    "author1_last_name", "author1_first_name", 
    "author2_last_name", "author2_first_name",
    "editor1_last_name", "editor1_first_name",
    "title", 
    "original_date_of_publication", "second_or_later_date_of_publication",
    "volume", "publisher", "publisher_location", "number_of_pages",
    "dictation", "name_of_transcriber",
    "translation", "name_of_translator",
    "summary", "occupations", 
    "date_of_birth", "date_of_death", 
    "place_of_birth", "other_places_lived"
]

SYSTEM_PROMPT = """You are a helpful assistant that transforms bibliography text into structured JSON data.
Extract independent bibliography entries from the provided text.
Return a valid JSON object with a key "entries" containing a list of objects.
Each object must have the following keys (use "N/A" if information is missing):
""" + ", ".join(REQUIRED_COLUMNS) + """

Rules:
- author1_last_name/first_name: Extract first author. "With..." usually means author2.
- author2_last_name/first_name: Second author. If none, "N/A".
- editor1_last_name/first_name: Only if “Edited by”, “ed.”, etc. Ignore introductions.
- title: Full title. Merge lines.
- original_date_of_publication: Earliest date.
- dictation: YES if "As told to", "Dictated by". "With" is NOT dictation.
- translation: YES if "Translated by".
- volume: "Volume II" etc or "N/A".
- number_of_pages: e.g. "290pp". Original edition only.
- occupations, bio dates, places: Extract if present in the text (some bibliographies include bio info).

JSON format only. No markdown formatting.
"""

def process_chunk(text_chunk):
    text_chunk = sanitize_text(text_chunk)
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract entries from this text:\n\n{text_chunk}"}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        return data.get("entries", [])
    except Exception as e:
        print(f"Error processing chunk: {e}")
        return []

def process_file(txt_file):
    print(f"Processing {txt_file}...")
    with open(txt_file, 'r', encoding='utf-8') as f:
        # Split by form feed (pages) from OCR
        raw_text = f.read()
        pages = raw_text.split('\f')
    
    all_entries = []
    basename = os.path.basename(txt_file)
    file_root = os.path.splitext(basename)[0]
    
    # Define paths relative to CWD (assuming script run from repo root) or absolute
    # Best to assume we are running from repo root, so:
    # output/ is at output/
    # data/progress/ is at data/progress/
    
    # If running from inside scripts/, these need to be ../output etc.
    # Let's try to detect or just assume root execution. 
    # Actually, let's make it robust by checking if output/ exists, otherwise assume parallel structure
    
    # Path logic:
    # output_csv -> output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        # Fallback or create? let's create
        os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, file_root + ".csv")
    
    # progress_file -> data/progress output directory
    progress_dir = os.path.join("data", "progress")
    if not os.path.exists(progress_dir):
        os.makedirs(progress_dir, exist_ok=True)
    progress_file = os.path.join(progress_dir, basename + ".progress")
    
    start_chunk = 0
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as pf:
                start_chunk = int(pf.read().strip())
            print(f"Resuming from chunk {start_chunk}...")
        except ValueError:
            pass

    if not os.path.exists(output_csv):
        # Initialize CSV with headers
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(output_csv, index=False)
    
    # Reload existing CSV to avoid header duplication if appending (mode='a' handles this but we need to be careful not to write header again)
    # The current code sets header=False for append, so that's fine.

    chunk_size = 2 
    for i in range(start_chunk * chunk_size, len(pages), chunk_size):
        current_chunk_idx = i // chunk_size
        chunk_pages = pages[i:i+chunk_size]
        chunk_text = "\n".join(chunk_pages)
        if len(chunk_text.strip()) < 50:
            # Still update progress even if skipping
            with open(progress_file, 'w') as pf:
                pf.write(str(current_chunk_idx + 1))
            continue
            
        print(f"  Processing chunk {current_chunk_idx + 1}...")
        print(f"    Chunk length: {len(chunk_text)}")
        print(f"    Preview: {chunk_text[:100]!r}")
        entries = process_chunk(chunk_text)
        print(f"    Found {len(entries)} entries")
        
        if entries:
            df = pd.DataFrame(entries)
            # Ensure columns exist
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    df[col] = "N/A"
            df = df[REQUIRED_COLUMNS]
            # Append to proper CSV
            df.to_csv(output_csv, mode='a', header=False, index=False)
            print(f"    Saved {len(entries)} entries to {output_csv}")
        
        # Save progress
        with open(progress_file, 'w') as pf:
            pf.write(str(current_chunk_idx + 1))

if __name__ == "__main__":
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python extract_bibliographies.py <txt_file1> [txt_file2 ...]")
        sys.exit(1)
        
    for txt_file in sys.argv[1:]:
        if not os.path.exists(txt_file):
            print(f"File not found: {txt_file}")
            continue
        process_file(txt_file)
