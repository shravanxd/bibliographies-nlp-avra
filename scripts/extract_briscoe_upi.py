import os
import sys
import json
import re
import pandas as pd
from openai import OpenAI

# Configuration for Briscoe
INPUT_FILE = "data/text/briscoe_uAPI.txt"
OUTPUT_FILE = "output/briscoe_UPI.csv"
PROGRESS_FILE = "data/progress/briscoe_UPI.progress"
CHUNK_SIZE_TARGET = 6000

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

SYSTEM_PROMPT = """You are a specialist in bibliographical data extraction for "American Autobiography 1945-1980".

Example:
Input: "0044 Adams, John Quincy 1767-1848\\nJohn Quincy Adams in Russia. Edited by Charles Francis Adams. New York: Praeger Publishers, 1970. (1874) 662 p.\\nA reprint of Volume II..."
JSON Result:
{
  "entries": [
    {
      "author1_last_name": "Adams",
      "author1_first_name": "John Quincy",
      "date_of_birth": "1767",
      "date_of_death": "1848",
      "title": "John Quincy Adams in Russia",
      "editor1_last_name": "Adams",
      "editor1_first_name": "Charles Francis",
      "publisher": "Praeger Publishers",
      "publisher_location": "New York",
      "original_date_of_publication": "1874",
      "second_or_later_date_of_publication": "1970",
      "number_of_pages": "662 p",
      "summary": "A reprint of Volume II of his memoirs, comprising the record of his experiences during his successful mission to the court of Czar Alexander I..."
    }
  ]
}

Rules:
1. Ignore OCR noise like "Oversize", "Am3", "500S199", "M.L.", "STO RA VN".
2. Capture publication details: Location: Publisher, Year. (OrigYear) Pages.
3. author1 dates: Extract birth-death years if listed next to the name.

Return a JSON object with "entries" key. Use "N/A" for missing data.
"""

def sanitize_briscoe(text):
    noise_patterns = [
        r"Oversize",
        r"016\.92",
        r"Am3",
        r"500[S6]199",
        r"M\.L\.",
        r"STO RA VN",
        r"W=——= O== = N — N =z = —— = —— = = N=—— = ~===3 — — ——_",
        r"This content downloaded from.*",
        r"All use subject to.*",
        r"American autobiography, 1980.*",
        r"1945-.*"
    ]
    for pattern in noise_patterns:
        text = re.sub(pattern, "", text)
    return text

def split_into_semantic_chunks(text, target_size):
    pattern = re.compile(r'\n(\d{4}\s+)')
    matches = list(pattern.finditer(text))
    
    chunks = []
    current_chunk_start = 0
    for i in range(len(matches)):
        if matches[i].start() - current_chunk_start > target_size:
            chunks.append(text[current_chunk_start:matches[i].start()])
            current_chunk_start = matches[i].start()
            
    chunks.append(text[current_chunk_start:])
    return chunks

def process_chunk(chunk_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract entries from this Briscoe text:\n\n{chunk_text}"}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("entries", [])
    except Exception as e:
        print(f"  Error: {e}")
        return []

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Missing input: {INPUT_FILE}")
        return

    print(f"Reading and cleaning {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    text = sanitize_briscoe(text)
    chunks = split_into_semantic_chunks(text, CHUNK_SIZE_TARGET)
    print(f"Split into {len(chunks)} semantic chunks.")

    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            start_chunk = int(f.read().strip())
        print(f"Resuming from chunk {start_chunk}...")
    else:
        start_chunk = 0
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(OUTPUT_FILE, index=False)

    for i in range(start_chunk, len(chunks)):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        entries = process_chunk(chunks[i])
        
        if entries:
            df = pd.DataFrame(entries)
            for col in REQUIRED_COLUMNS:
                if col not in df.columns:
                    df[col] = "N/A"
            df = df[REQUIRED_COLUMNS]
            df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
            print(f"  Extracted {len(entries)} entries.")
        
        with open(PROGRESS_FILE, 'w') as f:
            f.write(str(i + 1))

if __name__ == "__main__":
    main()
