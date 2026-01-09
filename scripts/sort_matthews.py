import pandas as pd
import sys
import os

def sort_csv(input_csv, output_csv):
    if not os.path.exists(input_csv):
        print(f"Error: {input_csv} not found.")
        sys.exit(1)

    print(f"Reading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Sort by author1_last_name, then first_name
    # Handle NaN values safely
    df['author1_last_name'] = df['author1_last_name'].fillna('')
    df['author1_first_name'] = df['author1_first_name'].fillna('')
    
    print("Sorting by Author Last Name...")
    df_sorted = df.sort_values(by=['author1_last_name', 'author1_first_name'])
    
    print(f"Saving sorted data to {output_csv}...")
    df_sorted.to_csv(output_csv, index=False)
    print("Done!")

if __name__ == "__main__":
    input_file = "output/matthews_sanitized.csv"
    output_file = "output/matthews_final.csv"
    
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    sort_csv(input_file, output_file)
