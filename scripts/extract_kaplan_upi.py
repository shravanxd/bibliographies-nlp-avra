import os
import sys
import json
import re
import pandas as pd
from openai import OpenAI

# Configuration for Kaplan
INPUT_FILE = "data/text/kaplan_uAPI.txt"
OUTPUT_FILE = "output/kaplan_UPI.csv"
PROGRESS_FILE = "data/progress/kaplan_UPI.progress"
CHUNK_SIZE_TARGET = 6000 # Smaller chunks for higher accuracy

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

SYSTEM_PROMPT = """You are a specialist in bibliographical data extraction for bibliographies of American Autobiographies.
Extract ALL independent entries from the provided text. DO NOT SKIP ANY.

Format Example:
Input: "Abbot, Willis John, 1863-1934. [3] Watching the world go by. Boston: Little, Brown, 1934. 358 p. WU. Reporter in Chicago and N.Y."
JSON Result:
{
  "entries": [
    {
      "author1_last_name": "Abbot",
      "author1_first_name": "Willis John",
      "date_of_birth": "1863",
      "date_of_death": "1934",
      "title": "Watching the world go by",
      "publisher": "Little, Brown",
      "publisher_location": "Boston",
      "original_date_of_publication": "1934",
      "number_of_pages": "358 p",
      "summary": "Reporter in Chicago and N.Y."
    }
  ]
}

Extraction Rules:
1. Author: Name is at the start of the entry. ID number is in brackets [ID].
2. Publication: Location: Publisher, Year.
3. Summary: The text following the publication details.

Return a JSON object with "entries" key. Use "N/A" for missing data.
"""

def split_into_semantic_chunks(text, target_size):
    # Kaplan entries start with Name at start of line
    pattern = re.compile(r'\n[A-Z][a-z]+,\s[A-Z]')
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
                {"role": "user", "content": f"Extract ALL entries from this Kaplan text:\n\n{chunk_text}"}
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

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        text = f.read()

    # The previous find() was hitting headers and cutting everything.
    # We will look for the real index or just process all and let LLM safe-fail.
    real_index_start = text.rfind("\nSUBJECT INDEX")
    if real_index_start != -1 and real_index_start > 100000: # Ensure it's the main one
        text = text[:real_index_start]

    chunks = split_into_semantic_chunks(text, CHUNK_SIZE_TARGET)
    print(f"Split into {len(chunks)} semantic chunks.")

    if not os.path.exists(OUTPUT_FILE):
        pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(OUTPUT_FILE, index=False)

    for i in range(len(chunks)):
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
