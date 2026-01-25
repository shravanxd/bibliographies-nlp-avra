import os
import sys
import json
import re
import pandas as pd
from openai import OpenAI

# Configuration for Matthews
INPUT_FILE = "data/text/matthews_uAPI.txt"
OUTPUT_FILE = "output/matthews_UPI.csv"
PROGRESS_FILE = "data/progress/matthews_UPI.progress"
CHUNK_SIZE_TARGET = 6000 # Smaller chunks for dense text

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

SYSTEM_PROMPT = """You are a specialist in bibliographical data extraction for British Autobiographies.

Format Example:
Input: "ABBOTT, Maj.Gen. Augustus. Military Journal, 1838-42; service with Bengal Artillery in the Afghan War; marches; military details. The Afghan War, ed. Charles R. Low (1879). 1"
JSON Result:
{
  "entries": [
    {
      "author1_last_name": "ABBOTT",
      "author1_first_name": "Augustus (Maj.Gen.)",
      "title": "The Afghan War (Military Journal, 1838-42)",
      "editor1_last_name": "Low",
      "editor1_first_name": "Charles R.",
      "original_date_of_publication": "1879",
      "summary": "Service with Bengal Artillery in the Afghan War; marches; military details.",
      "occupations": "Major-General; Bengal Artillery"
    }
  ]
}

Extraction Rules:
1. Entry Boundary: Starts with ALL CAPS LAST NAME followed by a comma.
2. Author: The ALL CAPS name is the last name. The following name is the first name.
3. Title: Often appears at the end before the date in parentheses. 
4. Summary: The descriptive text about their life.
5. Index Number: The number at the VERY END of the entry (e.g. "1") is an ID, not a date.
6. Occupation/Locations: Extract from the summary (e.g. "Leeds", "Surgeon").

Return a JSON object with "entries" key. Use "N/A" for missing data.
"""

def clean_matthews(text):
    # Remove JSTOR headers/footers
    text = re.sub(r"This content downloaded from.*", "", text)
    text = re.sub(r"All use subject to.*", "", text)
    text = re.sub(r"https://about\.jstor\.org/terms", "", text)
    text = re.sub(r"BRITISH AUTOBIOGRAPHIES", "", text)
    text = re.sub(r"University of California Press", "", text)
    return text

def split_into_semantic_chunks(text, target_size):
    pattern = re.compile(r'\n\[?[A-Z\-]{3,},')
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
                {"role": "user", "content": f"Extract entries from this Matthews text:\n\n{chunk_text}"}
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

    text = clean_matthews(text)
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
