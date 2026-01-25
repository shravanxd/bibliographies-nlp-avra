# Transformer Bibliographies to Structured Data - Implementation Plan

## Goal
Transform three specific autobiography bibliographies (`kaplan.pdf`, `matthews.pdf`, `briscoe.pdf`) into structured data (Excel/CSV) using OCR and GPT-based extraction.

## User Review Required
> [!IMPORTANT]
> **OpenAI API Key**: To use the GPT API for processing, I will need an OpenAI API key. Please ensure it is set in your environment or provide it.
> **Cost Warning**: Processing large PDFs via GPT-4 (or similar) can incur costs. I will use efficient prompting.

## Proposed Changes

### 1. OCR Processing
I will create a Python script `ocr_bibliographies.py` to:
- Convert PDF pages to images using `pdf2image` (or `pdftotext` if text layer exists, but likely scanned images based on "OCR tool" request).
- Use `tesseract` to extract text from images each page.
- Save the raw text to `.txt` files (e.g., `kaplan.txt`).

### 2. Structured Data Extraction
I will create a Python script `extract_bibliographies.py` to:
- Read the `.txt` files.
- Chunk the text to fit within context windows.
- Send chunks to the OpenAI API with the specific prompt and schema provided in the request.
- Parse the JSON/structured response.
- Aggregate results into a list of records.

### 3. Output Generation
- The script will save the aggregated records to `.csv` or `.xlsx` files (e.g., `kaplan.csv`).
- Columns will match the user's requirements (author details, publication info, dictation/translation flags, etc.).

## Verification Plan

### Automated Tests
- I will run the OCR script on a single page first to verify text extraction quality.
- I will run the extraction script on a small sample of text (first 5 pages) to verify the schema output and columns.

### Manual Verification
- **CSV Check**: Open the generated CSVs and verify columns exist and data looks extraction-correct.
- **Spot Check**: Compare 2-3 entries in `kaplan.csv` against the original PDF to ensure accuracy.

### Phase 2: Additional Bibliographies (`stuhr-rommerein` & `iwabuchi`)
- **Process**: Reuse `extract_bibliographies.py` (generic script).
- **Files**: `stuhr-rommerein_1980.pdf` and `sturh iwabuchi.pdf`.
- **Workflow**:
    1. Extract text using `pdftotext`.
    2. Extract data using existing LLM script.
    3. Validate CSV output.

### Phase 3: Accuracy Improvement (Unstructured API)
- **Goal**: Improve PDF-to-text conversion accuracy for `briscoe`, `kaplan`, and `matthews` using the Unstructured API.
- **Workflow**:
    1. Develop `scripts/unstructured_parse.py` to interface with the Unstructured API.
    2. Process `briscoe.pdf`, `kaplan.pdf`, and `matthews.pdf`.
    3. Save outputs as `{name}_uAPI.txt`.
    4. Transition extraction pipeline to use these new text files for better LLM performance.

### Phase 4: Final Personalized Extraction
- **Goal**: Run the final extraction with high-precision, small chunks (6000 chars) and book-specific logic.
- **Features**:
    - **Progress Saving**: Automated `.progress` files allow resumption from any chunk.
    - **Incremental Output**: CSVs grow in real-time.
    - **Semantic Chunking**: Entry boundary detection ensures no entries are cut in half.
