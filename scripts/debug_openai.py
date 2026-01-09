from openai import OpenAI
import os
import sys

# Assume run from repo root
filename = 'matthews_start.txt'

if not os.path.exists(filename):
    print(f"{filename} not found!")
    sys.exit(1)

client = OpenAI()

try:
    with open(filename, 'r') as f:
        text = f.read()
    
    print(f"Sending {len(text)} chars to OpenAI...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Extract data."},
            {"role": "user", "content": text}
        ]
    )
    print("Response received!")
    print(response.choices[0].message.content[:200])
except Exception as e:
    print(f"Error: {e}")
