import os
import sys
import json
import re
import unicodedata
import pandas as pd
from openai import OpenAI

# Initialize client
client = OpenAI()

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

def clean_for_api(s: str) -> str:
    """
    Rigorous sanitization for 'toxic' PDF text layers.
    1. Normalize Unicode (NFKC)
    2. Remove C0/C1 control codes (except \n\r\t)
    3. Remove Unicode format chars (Cf category - zero width, bidi, etc)
    4. Ensure UTF-8 roundtrip
    """
    if not s:
        return ""
        
    # Normalize to reduce weird composed characters / ligatures
    s = unicodedata.normalize("NFKC", s)

    # Remove C0/C1 control chars except newline/tab/carriage return
    # C0: 0x00-0x1F, C1: 0x7F-0x9F
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", s)

    # Remove Unicode "format" characters (zero-width, bidi overrides, etc.)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Cf")

    # Guarantee valid UTF-8 roundtrip
    s = s.encode("utf-8", "replace").decode("utf-8")

    return s

def process_chunk(text_chunk):
    # Pre-flight check: Ensure JSON encoding doesn't hang
    try:
        json.dumps({"t": text_chunk})
    except Exception as e:
        print(f"CRITICAL: Chunk failed JSON safety check: {e}")
        return []

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

def process_matthews(txt_file):
    print(f"Processing {txt_file} with RIGOROUS sanitization...")
    
    with open(txt_file, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # 1. Clean the ENTIRE text first
    print("Sanitizing text...")
    cleaned_text = clean_for_api(raw_text)
    
    # Check for nulls just in case
    if "\x00" in cleaned_text:
        print("WARNING: Null bytes still present after cleaning!")
    
    # 2. Split by page (form feed) - if form feeds survived sanitization
    # Note: re.sub might have removed \f (0x0C) if we were not careful, 
    # but the regex [\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F] includes \x0C (Form Feed).
    # The user's regex REMOVES \x0C. So we won't have page splits anymore!
    # We must decide: keep \f or rely on arbitrary chunking.
    # The user's prompt suggested keeping \n\r\t. \f is usually 0x0C.
    # Let's execute the user's EXACT regex logic which removes \f.
    # So we will chunk by characters/length instead of pages.
    
    # User suggestion: chunk(s, max_chars=20000)
    chunk_size = 15000 # Conservative buffer
    chunks = [cleaned_text[i:i+chunk_size] for i in range(0, len(cleaned_text), chunk_size)]
    
    print(f"Text cleaned. Total chars: {len(cleaned_text)}. Splitting into {len(chunks)} chunks of ~{chunk_size} chars.")

    # Setup output paths
    basename = os.path.basename(txt_file)
    file_root = os.path.splitext(basename)[0]
    
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    output_csv = os.path.join(output_dir, file_root + "_sanitized.csv")
    
    progress_dir = os.path.join("data", "progress")
    if not os.path.exists(progress_dir):
        os.makedirs(progress_dir, exist_ok=True)
    progress_file = os.path.join(progress_dir, basename + "_sanitized.progress")

    start_chunk = 0
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as pf:
                start_chunk = int(pf.read().strip())
            print(f"Resuming from chunk {start_chunk}...")
        except ValueError:
            pass

    if not os.path.exists(output_csv):
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(output_csv, index=False)

    for i in range(start_chunk, len(chunks)):
        chunk_text = chunks[i]
        
        print(f"  Processing chunk {i + 1}/{len(chunks)}...")
        entries = process_chunk(chunk_text)
        print(f"    Found {len(entries)} entries")
        
        if entries:
            df = pd.DataFrame(entries)
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    df[col] = "N/A"
            df = df[REQUIRED_COLUMNS]
            df.to_csv(output_csv, mode='a', header=False, index=False)
            print(f"    Saved to {output_csv}")
        
        with open(progress_file, 'w') as pf:
            pf.write(str(i + 1))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/extract_matthews.py <txt_file>")
        sys.exit(1)
        
    process_matthews(sys.argv[1])
