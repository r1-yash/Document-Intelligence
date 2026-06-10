import os
import uuid
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.parser import parse_document
from backend.schemas import (
    UploadResponse,
    QueryRequest,
    QueryResponse,
    InsightsResponse,
    DocumentRequest,
    ReportResponse,
)
from backend.llm import generate_query_response, generate_insights, generate_report

# Configure basic logging for debugging server activities
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("document-intelligence")

load_dotenv(override=True)

app = FastAPI(
    title="Document Intelligence API",
    description="Enterprise-grade FastAPI backend for parsing business documents and extracting structured insights via Gemini 2.0.",
    version="1.0.0",
)

# Enable CORS for standard deployment configurations (e.g. cross-port streamlit requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight, thread-safe (conceptually) in-memory storage dictionary.
# Keys are document UUIDs; values are dicts containing 'filename' and raw parsed 'text'.
# Note: Restarts will purge this cache.
documents_db = {}

@app.get("/health", status_code=200)
async def health_check():
    """
    Service health check endpoint.
    """
    return {"status": "healthy"}

@app.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Uploads a PDF, DOCX, or TXT file, parses its text content,
    and indexes it in the in-memory document database.
    """
    if not file.filename:
        logger.warning("Upload rejected: missing filename.")
        raise HTTPException(status_code=400, detail="Invalid file: missing filename.")
    
    logger.info(f"Incoming upload request for: {file.filename}")
    
    try:
        # Read raw binary data from upload stream
        file_bytes = await file.read()
        
        # Parse the document using specialized extensions parsers
        parsed_text = parse_document(file.filename, file_bytes)
        
        if not parsed_text.strip():
            logger.warning(f"Extracted content empty for: {file.filename}")
            raise HTTPException(
                status_code=422, 
                detail="Document parsing succeeded, but no readable text could be extracted."
            )
        
        # Generate a unique tracking index for this session document
        doc_id = str(uuid.uuid4())
        documents_db[doc_id] = {
            "filename": file.filename,
            "text": parsed_text,
        }
        
        logger.info(f"Successfully processed {file.filename} (ID: {doc_id}, Chars: {len(parsed_text)})")
        
        return UploadResponse(
            doc_id=doc_id,
            filename=file.filename,
            char_count=len(parsed_text),
        )
        
    except ValueError as e:
        # Handle unsupported file extensions or decode failures gracefully
        logger.error(f"Validation failure for upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Log system/parser crashes and return a 500 error code
        logger.exception(f"Unexpected error parsing document {file.filename}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_document(request: QueryRequest):
    """
    Accepts a question along with a doc_id, looks up the cached document text,
    and returns a factual response compiled by Gemini 2.0.
    """
    document = documents_db.get(request.doc_id)
    if not document:
        logger.warning(f"Query request failed: doc_id {request.doc_id} not found.")
        raise HTTPException(status_code=404, detail="Document not found or session expired.")
    
    logger.info(f"Processing query for document ID: {request.doc_id}")
    
    try:
        answer = generate_query_response(document["text"], request.question)
        return QueryResponse(answer=answer)
    except Exception as e:
        logger.exception(f"LLM query run failed for document: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"LLM query processing failed: {str(e)}")

@app.post("/insights", response_model=InsightsResponse)
async def get_insights(request: DocumentRequest):
    """
    Performs an automatic deep business audit of the document, return a structured 
    list of facts, metrics, tasks, and risks formatted in JSON.
    """
    document = documents_db.get(request.doc_id)
    if not document:
        logger.warning(f"Insights request failed: doc_id {request.doc_id} not found.")
        raise HTTPException(status_code=404, detail="Document not found or session expired.")
    
    logger.info(f"Extracting structured insights for document ID: {request.doc_id}")
    
    try:
        insights = generate_insights(document["text"])
        return insights
    except Exception as e:
        logger.exception(f"LLM insights extraction failed for document: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"LLM insights extraction failed: {str(e)}")

@app.post("/report", response_model=ReportResponse)
async def get_report(request: DocumentRequest):
    """
    Generates a full Markdown business report containing structured sections
    for Executive Summary, Key Findings, Numbers & Data, and Risks & Recommendations.
    """
    document = documents_db.get(request.doc_id)
    if not document:
        logger.warning(f"Report request failed: doc_id {request.doc_id} not found.")
        raise HTTPException(status_code=404, detail="Document not found or session expired.")
    
    logger.info(f"Compiling executive report for document ID: {request.doc_id}")
    
    try:
        report_markdown = generate_report(document["text"])
        return ReportResponse(report=report_markdown)
    except Exception as e:
        logger.exception(f"LLM report compilation failed for document: {request.doc_id}")
        raise HTTPException(status_code=500, detail=f"LLM report generation failed: {str(e)}")

# CLI server entrypoint using standard Uvicorn runs
if __name__ == "__main__":
    import uvicorn
    host_ip = os.getenv("HOST", "127.0.0.1")
    port_number = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting API server on {host_ip}:{port_number}")
    uvicorn.run("backend.main:app", host=host_ip, port=port_number, reload=True)
