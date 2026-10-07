# Automated Question Bank Generation System

This project is a Flask-based web application that ingests educational PDF/textbook content, extracts text, applies NLP-based keyword extraction, classifies the topic, generates question sets, estimates difficulty, checks quality, removes duplicates, and stores everything in SQLite for search, filtering, and export.

## Project Description

The application demonstrates a complete prototype workflow for educational assessment generation. It accepts PDF files, extracts readable content, falls back to OCR when needed, identifies keywords and topic categories, creates evaluation questions, and stores them in a question bank.

The design is intentionally simple and explainable, which makes it ideal for a final-year college project and viva presentation. It is usable offline and does not depend on external transformer models.

## Features

- PDF upload and validation
- PDF text extraction using pypdf
- OCR fallback through pytesseract and pdf2image
- NLP keyword extraction
- Topic classification for Database, Operating Systems, Computer Networks, Machine Learning, Data Structures, IoT, Programming, and General
- Question generation for MCQ, Short Answer, Numerical/Application, and Case-based types
- Difficulty estimation: Easy, Medium, Hard
- Prototype quality score from 0 to 100
- Duplicate detection using SequenceMatcher
- SQLite database storage
- Search and filtering by topic, difficulty, question type, and keyword
- CSV and JSON export
- REST-style API endpoints
- Dashboard with summary cards and visual pipeline

## Technology Stack

- Backend: Python, Flask
- Frontend: HTML5, CSS3, Bootstrap 5, JavaScript
- Database: SQLite
- NLP: spaCy, NLTK
- PDF: pypdf, pdf2image, pytesseract, Pillow
- Data handling: pandas
- ML utilities: scikit-learn (structural support)

## Folder Structure

```text
automated_question_bank/
├── app.py
├── config.py
├── database.py
├── requirements.txt
├── README.md
├── .gitignore
├── services/
│   ├── __init__.py
│   ├── pdf_service.py
│   ├── ocr_service.py
│   ├── nlp_service.py
│   ├── topic_service.py
│   ├── question_service.py
│   ├── difficulty_service.py
│   ├── quality_service.py
│   └── duplicate_service.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── results.html
│   ├── questions.html
│   └── error.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/
├── exports/
├── instance/
│   └── question_bank.db
└── tests/
    └── test_core.py
```

## Installation

### 1. Create a virtual environment

```bash
cd automated_question_bank
python -m venv venv
```

### 2. Activate the environment

Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Download spaCy model

```bash
python -m spacy download en_core_web_sm
```

### 5. OCR installation notes

If OCR is needed for scanned PDFs, install Tesseract and Poppler:

- Windows: install Tesseract OCR from the official installer and add it to PATH.
- For Poppler: install a Windows binary from the Poppler project and ensure the `bin` folder is included in PATH.
- If OCR dependencies are not installed, the app will show a clear message instead of crashing.

## How to Run

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## How to Upload a PDF

1. Open the home page.
2. Click “Upload PDF”.
3. Select a PDF file.
4. Choose the count and question types.
5. Select difficulty or use Auto.
6. Click “Upload & Generate Questions”.

The system extracts text and generates the question bank automatically.

## How to Generate Questions

The generation pipeline works as follows:

1. PDF is saved in the uploads folder.
2. Text is extracted.
3. If text is empty, OCR is attempted.
4. Keywords are extracted.
5. Topic is classified.
6. Questions are generated using a rule-based template engine.
7. Difficulty and quality are estimated.
8. Duplicate questions are removed.
9. Questions are stored in SQLite.

## How to Search and Filter

Open the Question Bank page and use:

- Search box
- Topic filter
- Difficulty filter
- Question type filter
- Keyword search

Use “Reset” to clear the filters.

## How to Export

- CSV: /export/csv
- JSON: /export/json

Files download automatically from the browser.

## API Endpoints

- GET /api/questions
- GET /api/questions/<id>

These endpoints return JSON data for the stored question bank.

## Troubleshooting

- If no text is extracted, upload a digital PDF or install OCR dependencies.
- If the PDF is corrupted, the app shows a friendly error.
- If the question bank is empty, generate questions from a valid PDF first.
- If the spaCy model is missing, a fallback keyword extraction method is used automatically.
- If OCR packages are not installed, the system does not crash and indicates the issue clearly.

## Demo Steps

1. Run the application.
2. Upload a sample textbook PDF or use a document with topics like Operating Systems, Database, or Machine Learning.
3. Choose the desired question types and count.
4. Review the generated results.
5. Open the Question Bank page to filter, search, and export.
6. Open the API endpoints to preview JSON data.

## Viva Explanation

This project is relevant because it solves a real educational challenge: creating reusable assessment questions from teaching material. The system reduces manual effort, improves consistency, and supports digital classrooms.

The novelty of the project is the unified workflow that combines:

- PDF ingestion
- text extraction
- OCR fallback
- keyword extraction
- topic classification
- hybrid rule-based question generation
- difficulty estimation
- quality checking
- duplicate removal
- SQLite storage
- search and filtering
- export capabilities

This presents a complete automated question bank pipeline rather than a single isolated feature.

## Test Plan

1. Homepage load
2. PDF upload
3. PDF text extraction
4. OCR fallback
5. Keyword extraction
6. Topic classification
7. Short-answer generation
8. MCQ generation
9. Numerical generation
10. Case-based generation
11. Difficulty estimation
12. Quality scoring
13. Duplicate detection
14. SQLite storage
15. Search
16. Topic filter
17. Difficulty filter
18. Question type filter
19. CSV export
20. JSON export
21. REST API
22. Invalid PDF
23. Empty upload
24. Invalid file extension

## Notes

The current project uses a reliable local rule-based generation approach so the prototype works fully offline. The structure is modular enough to allow future transformer or LLM-based generation without rewriting the complete system.
