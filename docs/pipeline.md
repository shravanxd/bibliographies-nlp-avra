# Bibliography Data Extraction Pipeline

This document explains the technical pipeline used to convert raw PDF bibliographies (Briscoe, Kaplan, and Matthews) into structured CSV datasets. The process consists of four main stages: text extraction, sanitization, AI processing, and final output assembly.

## 1. Input Data Processing

The pipeline begins with the raw PDF files. The first step represents the conversion of these visual documents into machine-readable text. We use the command line tool pdftotext to extract the plain text layer from the PDF files. This tool preserves the physical layout of the text which is crucial for identifying entry boundaries.

For simple files like Kaplan and Briscoe, this raw text is largely ready for processing. However, the Matthews file required special handling due to invisible corruption in its text layer which we address in the next stage.

## 2. Text Sanitization and Preparation

Before data can be extracted, the raw text must be cleaned. This is the most critical technical step for ensuring stability.

### Encoding Repair
The Matthews file contained corrupted characters (invisible control codes) that caused the extraction process to hang. We implemented a rigorous sanitization module that performs three specific cleaning actions. First, it normalizes all text to a standard form (NFKC) to fix combined characters. Second, it strips out "toxic" control characters (like null bytes and printer codes) while keeping essential formatting like newlines. Third, it removes formatting markers that are not visible to the human eye but confuse the software.

### Chunking
The text files are too large to process in a single pass. The system splits the sanitized text into manageable "chunks" of approximately 15,000 characters. Care is taken to split text at safe boundaries to avoid cutting a bibliography entry in half.

## 3. AI Extraction (The Intelligence Layer)

This is the core of the pipeline where unstructured text is converted into structured data.

### The Model
We use a Large Language Model (GPT-4o-mini) to analyze each text chunk. The model is acting as a specialized reader that looks for bibliography entries.

### Structured Output
Instead of asking for a paragraph of text, we enforce a strict JSON schema. The model must return data in a specific format with keys like "author", "title", "year", and "publisher". This guarantees that every single entry extracted fits perfectly into our output columns. If a chunk contains no entries, the model returns an empty list rather than hallucinating data.

### Resumability
The process is designed to be interrupted and resumed. A progress file tracks exactly which chunk was last successfully processed. If the script is stopped, it reads this file upon restarting and continues from exactly where it left off, ensuring no data is duplicated or lost.

## 4. Post-Processing and Output

As the AI extracts entries, they are immediately validated and appended to a CSV file.

### Column Mapping
The JSON data from the model is mapped to our standardized columns (Author Last Name, Title, Year, etc.). Any missing fields are filled with "N/A" to ensure the CSV remains rectangular and valid.

### Reordering
The Matthews PDF has a two-column layout which causes the text reader to read across the page (Entry 1, Entry 9, Entry 2, Entry 10). To fix this, we apply a final sorting step. A dedicated script reads the completed CSV and sorts all entries alphabetically by author name. This restores the correct logical order without needing complex layout analysis of the original PDF.

## Summary

In summary, the system takes a raw PDF, cleans the text of corrupt data, feeds it in small pieces to an AI that adheres to a strict schema, and compiles the results into a clean, searchable spreadsheet. This approach prioritizes accuracy and stability over speed, ensuring that even difficult files like Matthews are processed correctly.
