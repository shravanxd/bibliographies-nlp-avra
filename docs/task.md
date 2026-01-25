# Task: Transform Bibliographies to Structured Data [/]

## Preparation
- [x] Explore directory and verify files <!-- id: 0 -->
- [x] Check available OCR tools (pdftotext, tesseract, python libs) <!-- id: 1 -->
- [x] Check and Install python libraries (poppler, pdf2image) <!-- id: 2 -->
- [x] Create implementation plan <!-- id: 3 -->

## Execution
- [x] OCR: Convert `kaplan.pdf` to text (Fast `pdftotext`) <!-- id: 4 -->
- [x] OCR: Convert `matthews.pdf` to text (Fast `pdftotext`) <!-- id: 5 -->
- [x] OCR: Convert `briscoe.pdf` to text (Fast `pdftotext`) <!-- id: 6 -->
- [x] Re-process text to fix column layout <!-- id: 7 -->
- [x] Process `kaplan.txt` with LLM to extract structured data (Completed 197 chunks) <!-- id: 8 -->
- [x] Process `matthews.txt` with LLM to extract structured data (Completed 83/83) <!-- id: 9 -->
    - [x] Analyze `matthews.txt` for encoding/corruption issues (Header identified as issue) <!-- id: 18 -->
    - [x] Create modular `scripts/extract_matthews.py` with rigorous sanitization (Done & Verified) <!-- id: 21 -->
    - [x] Test aggressive text cleaning/sanitization (Verified working on Chunk 1) <!-- id: 19 -->
    - [-] Fallback to OCR (Replaced by faster sanitization fix) <!-- id: 20 -->
- [x] Create `pipeline.md` documentation (Done) <!-- id: 22 -->
- [x] Process `briscoe.txt` with LLM to extract structured data (Completed 197/197 chunks) <!-- id: 10 -->
- [x] Generate Excel/CSV for `kaplan` (Verified Complete) <!-- id: 11 -->
- [x] Generate Excel/CSV for `matthews` (Done) <!-- id: 12 -->
- [x] Generate Excel/CSV for `briscoe` (Done) <!-- id: 13 -->

## Verification
- [x] Verify output columns match requirements (Verified in CSVs) <!-- id: 14 -->
- [x] Verify data quality (spot check) (Kaplan/Briscoe valid, Matthews blocked) <!-- id: 15 -->

## Maintenance
- [x] Restructure directory (data, scripts, output) <!-- id: 16 -->
- [x] Update scripts to support new structure <!-- id: 17 -->

## Phase 2: Additional Bibliographies
- [x] Process `stuhr-rommerein_1980.pdf` <!-- id: 23 -->
    - [x] Extract text (pdftotext) <!-- id: 24 -->
    - [x] Extract data (LLM) (Completed ~01:32 AM) <!-- id: 25 -->
- [x] Process `sturh iwabuchi.pdf` <!-- id: 26 -->
    - [x] Extract text (pdftotext) <!-- id: 27 -->
    - [x] Extract data (LLM) (Completed 292 chunks) <!-- id: 28 -->

## Phase 3: Accuracy Improvement (Unstructured API)
- [x] Process `briscoe.pdf` with Unstructured API <!-- id: 29 -->
- [x] Process `kaplan.pdf` with Unstructured API <!-- id: 30 -->
- [x] Process `matthews.pdf` with Unstructured API <!-- id: 31 -->
- [x] Verify improvement in text quality <!-- id: 32 -->

## Phase 4: Final High-Accuracy Extraction
- [/] Extract Data from `kaplan_uAPI.txt` -> `kaplan_UPI.csv` (~21% done) <!-- id: 34 -->
- [/] Extract Data from `briscoe_uAPI.txt` -> `briscoe_UPI.csv` (~17.5% done) <!-- id: 33 -->
- [/] Extract Data from `matthews_uAPI.txt` -> `matthews_UPI.csv` (~26% done) <!-- id: 35 -->
