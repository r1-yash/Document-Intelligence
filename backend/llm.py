import os
import google.generativeai as genai
from dotenv import load_dotenv
from backend.schemas import InsightsResponse

# Load env variables at module level, but we check and configure the API key dynamically
# in get_model to ensure updates to .env are hot-reloaded during local development.
load_dotenv(override=True)

def get_model(system_instruction: str = None) -> genai.GenerativeModel:
    """
    Initializes and retrieves a configured Gemini GenerativeModel instance.
    
    We pull the API key dynamically on model creation so that key changes in the .env 
    take effect immediately without requiring a full server reboot.
    """
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        raise ValueError(
            "GEMINI_API_KEY is not set or contains the default placeholder. "
            "Please configure a valid API key in your .env file."
        )
        
    genai.configure(api_key=gemini_key)
    
    return genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )

def generate_query_response(doc_text: str, question: str) -> str:
    """
    Answers a specific user question about the document context.
    
    Injects the entire document text within the prompt context and instructs the model
    to act as a zero-shot Q&A engine that refuses answers not verifiable by the text.
    """
    system_instruction = (
        "You are an expert document intelligence assistant. Your primary task is to answer "
        "questions about the provided document context. Answer the user's question accurately, "
        "concisely, and using ONLY information explicitly found or directly inferred from the document. "
        "If the answer cannot be found in the document, state clearly that you cannot answer "
        "based on the provided document context."
    )
    
    model = get_model(system_instruction=system_instruction)
    
    # We combine the context and question clearly so the model can distinguish query parameters.
    prompt = f"DOCUMENT CONTEXT:\n{doc_text}\n\nUSER QUESTION:\n{question}"
    
    response = model.generate_content(prompt)
    return response.text.strip()

def generate_insights(doc_text: str) -> InsightsResponse:
    """
    Extracts structured, categorized business insights from the document.
    
    Utilizes Gemini's Structured Output capability by passing our Pydantic schema
    (InsightsResponse) directly to the generation config. A low temperature of 0.1 is 
    specified to keep the analysis factual, analytical, and highly structured.
    """
    system_instruction = (
        "You are a meticulous business analyst. Your job is to extract high-value insights from the "
        "provided document and map them into the requested JSON schema. You must extract "
        "key facts, important figures/numbers, action items, and risks."
    )
    
    model = get_model(system_instruction=system_instruction)
    prompt = f"Analyze this document and extract structured insights:\n\n{doc_text}"
    
    # We pass the schema directly to response_schema. The Google AI SDK converts this Pydantic 
    # model to an OpenAPI-compliant JSON schema behind the scenes.
    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": InsightsResponse,
        "temperature": 0.1,  # Low temperature ensures high fidelity to the text
    }
    
    response = model.generate_content(prompt, generation_config=generation_config)
    
    # Deserialize the valid JSON returned by Gemini directly into our Pydantic model
    return InsightsResponse.model_validate_json(response.text)

def generate_report(doc_text: str) -> str:
    """
    Generates a formal markdown business summary report of the document.
    
    Outputs a clean, professional consultant-style document with predefined sections
    suitable for immediate business ingestion.
    """
    system_instruction = (
        "You are a professional corporate consultant. Your task is to generate a comprehensive, "
        "highly polished executive summary report based on the provided document.\n\n"
        "Your output must be structured as clean Markdown using these specific headers:\n"
        "1. Executive Summary: High-level business overview.\n"
        "2. Key Findings: Main discoveries and core takeaways.\n"
        "3. Numbers & Data: Categorized breakdown of metrics, financials, and statistics.\n"
        "4. Risks & Recommendations: Identified bottlenecks or concerns, followed by actionable steps."
    )
    
    model = get_model(system_instruction=system_instruction)
    prompt = f"Generate the consulting summary report for this document:\n\n{doc_text}"
    
    response = model.generate_content(prompt)
    return response.text.strip()
