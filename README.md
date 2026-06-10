# Document Intelligence Portal

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)](https://streamlit.io)
[![Gemini 2.0 Flash](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google)](https://deepmind.google/technologies/gemini/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python)](https://python.org)

An enterprise-ready, production-style business intelligence tool that extracts structured data, runs context-aware Q&A, and generates consulting-quality summaries from business documents (PDFs, DOCX, and TXT).

---

## Architecture Overview

```mermaid
graph TD
    A[Client Web App - Streamlit] -->|1. File Upload| B(FastAPI Backend)
    B -->|2. Extract Raw Text| C[Document Parsers]
    C -->|pdfplumber / python-docx / txt| B
    B -->|3. Store in Memory| D[(In-Memory Cache)]
    
    A -->|4. Automated Insight Request| B
    B -->|5. Structured Generation Prompt| E(Google Gemini 2.0 API)
    E -->|Structured JSON Response| B
    B -->|6. Insights Schema| A
    
    A -->|7. Contextual Chat / Report Requests| B
    B -->|8. Full Context Prompts| E
    E -->|Markdown / QA Answers| B
    B -->|9. Interactive Rendering| A
```

---

## Features

- **Robust Document Parsing**: 
  - Extracts paragraph text and structured tabular data in order from Word (`.docx`) files.
  - Page-by-page text parsing from PDF (`.pdf`) documents.
  - Multi-encoding fallback support for standard text (`.txt`) documents.
- **Structured Insights Extraction**: Auto-extracts Key Facts, Important Numbers, Action Items, and Risk Analyses using Gemini 2.0 structured schema compilation.
- **Contextual Q&A**: Real-time interactive document chat verified strictly against parsed document text context.
- **Corporate Report Engine**: Generates comprehensive executive summary drafts formatted in clean Markdown, ready for copy-paste or immediate download.
- **Modern User Experience**: Minimalist design styled with dark glassmorphic cards, custom animations, responsive grid columns, and dynamic metric badges.

---

## File Structure

```text
document-intelligence-tool/
├── backend/
│   ├── main.py              # FastAPI server, endpoints, and in-memory DB
│   ├── parser.py            # Word, PDF, and Text parsing engines
│   ├── llm.py               # Gemini 2.0 integration & prompt templates
│   └── schemas.py           # Pydantic validation models
├── frontend/
│   └── app.py               # Streamlit responsive application
├── requirements.txt         # Core python dependencies
├── .env.example             # Configuration setup template
└── README.md                # Project documentation
```

---

## Getting Started

### 1. Clone & Set Up Directory
Navigate to the root project folder:
```bash
cd document-intelligence-tool
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure your API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
HOST=127.0.0.1
```

### 3. Install Dependencies
It is highly recommended to run this inside a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run the Backend API
Start the FastAPI server using Uvicorn:
```bash
uvicorn backend.main:app --reload --port 8000
```
The interactive Swagger API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 5. Run the Streamlit Interface
In a separate terminal tab or window, activate your virtual environment and run the frontend:
```bash
streamlit run frontend/app.py
```
The application will open automatically in your browser at [http://localhost:8501](http://localhost:8501).

---

## API Specification

| Endpoint | Method | Payload | Response | Description |
|---|---|---|---|---|
| `/upload` | `POST` | `multipart/form-data` | `UploadResponse` | Uploads and parses doc, returns `doc_id` and character count. |
| `/insights` | `POST` | `DocumentRequest` | `InsightsResponse` | Triggers structured JSON insights (facts, numbers, actions, risks). |
| `/query` | `POST` | `QueryRequest` | `QueryResponse` | Answers user questions verified strictly against the document text. |
| `/report` | `POST` | `DocumentRequest` | `ReportResponse` | Compiles a full corporate consulting report in Markdown. |
