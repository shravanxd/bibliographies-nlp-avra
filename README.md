# Bibliography Extraction Project

This project implements a robust pipeline to extract structured data (authors, titles, dates, publishers, etc.) from unstructured bibliography PDFs. The target files were Briscoe, Kaplan, and Matthews, each presenting unique challenges regarding text layout and encoding.

## What We Did

We built a Python-based extraction system that converts raw PDF text into clean, structured CSV datasets. The core of the system relies on Large Language Models (LLMs) to parse complex bibliography entries that regular expressions could not handle. We also implemented a rigorous text sanitization layer to handle corrupted PDF text layers.

## The Pipeline

The data flows through four main stages:

1. **Text Extraction**: We use `pdftotext` to convert the visual PDF into a plain text stream.
2. **Sanitization**: Validates the text encoding. For problematic files, we strip toxic control characters and normalize Unicode to prevent API failures.
3. **AI Processing**: The text is split into chunks of approximately 15,000 characters. Each chunk is sent to GPT-4o-mini with a strict JSON schema to extract fields like Author, Title, Year, and Publisher.
4. **Post-Processing**: The JSON responses are converted to CSV rows. For multi-column layouts, we apply a sorting algorithm to restore the correct alphabetical order.

## Scripts

The project is organized into modular scripts located in the `scripts/` directory:

*   **`extract_bibliographies.py`**: The general-purpose extraction script used for standard files like Kaplan and Briscoe. It handles chunking and API communication.
*   **`extract_matthews.py`**: A specialized script for the Matthews PDF. It includes the rigorous `clean_for_api` function to fix encoding issues and handles the specific chunking requirements for that file.
*   **`sort_matthews.py`**: A utility script that sorts the final CSV output. This fixes the zigzag reading order caused by the two-column layout of the original PDF.
*   **`ocr_bibliographies.py`**: A fallback script that uses `pdf2image` and Tesseract OCR to regenerate the text layer if the original is too corrupt to save.

## NLP Methods

We utilized OpenAI's GPT-4o-mini model for the extraction. Instead of generic prompting, we enforced **JSON Mode** to guarantee valid output. The system prompt defines a schema with specific rules, such as identifying the first vs. second author, extracting "pp" for page counts, and separating translator names from the title. This approach eliminates parsing errors common with free-text LLM outputs.

## Challenges and Solutions

The biggest challenge was the **Matthews PDF**.

1.  **Toxic Text Layer**: The raw text contained invisible control characters (C0 and C1 codes) and null bytes. These caused the OpenAI API client to hang indefinitely because the JSON payload became malformed or corrupt at the network layer.
    *   **Solution**: We wrote a custom sanitization function that performs NFKC normalization and strips all non-printable characters except for standard whitespace.

2.  **Reading Order**: The PDF has a two-column layout. The text extractor read straight across the page, mixing the left and right columns (e.g., Entry 1, then Entry 10, then Entry 2).
    *   **Solution**: Rather than trying to rebuild the layout logic, we extracted the data "out of order" and created `scripts/sort_matthews.py` to sort the final dataset alphabetically, which perfectly restores the correct sequence.
