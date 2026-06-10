import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load local environment configuration
load_dotenv(override=True)

# Configure Streamlit page layout and metadata
st.set_page_config(
    page_title="Document Intelligence Portal",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL pointing to the FastAPI service
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Custom CSS styling injection
# We inject custom CSS to override Streamlit's default light/dark themes
# and force a premium dark glassmorphic styling with smooth drop shadows and gradients.
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    /* Apply clean font family throughout the app elements */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Add a rich radial gradient background */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 50% 0%, #1e1e38 0%, #0c0c14 100%) !important;
    }
    
    /* Sleek sidebar container styling */
    [data-testid="stSidebar"] {
        background-color: #0f0f1b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Gradient text helper */
    .gradient-text {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -0.05em;
    }
    
    .hero-container {
        text-align: center;
        padding: 40px 0;
        margin-bottom: 20px;
    }
    
    /* Glassmorphic card definitions with hover transition animations */
    .glass-card {
        background: rgba(25, 25, 45, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
    }
    
    /* Dynamic left borders for specific card categories */
    .fact-card {
        border-left: 4px solid #6366f1 !important;
    }
    
    .number-card {
        border-left: 4px solid #fbbf24 !important;
    }
    
    .action-card {
        border-left: 4px solid #10b981 !important;
    }
    
    .risk-card {
        border-left: 4px solid #f43f5e !important;
    }
    
    /* Custom message bubble overrides */
    [data-testid="stChatMessage"] {
        background-color: rgba(20, 20, 35, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
    }
    
    /* Custom style overrides for the Streamlit Tabs widget */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        color: #94a3b8;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 8px 16px;
        font-weight: 500;
        transition: all 0.2s;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #ffffff;
        background-color: rgba(99, 102, 241, 0.1);
        border-color: rgba(99, 102, 241, 0.3);
    }

    .stTabs [aria-selected="true"] {
        background-color: rgba(99, 102, 241, 0.2) !important;
        border-color: rgba(99, 102, 241, 0.5) !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    
    /* Professional button gradient styling */
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 14px 0 rgba(99, 102, 241, 0.3) !important;
        transition: all 0.2s !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px 0 rgba(99, 102, 241, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize persistent Streamlit session states across user interactions
session_defaults = {
    "doc_id": None,
    "filename": None,
    "char_count": 0,
    "insights": None,
    "report": None,
    "chat_history": []
}

for key, default_value in session_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

def clear_active_session():
    """
    Clears all active session cache details when discarding a document.
    """
    for key, val in session_defaults.items():
        st.session_state[key] = val

# --- Sidebar Component Layout ---
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0; text-align: center;">
        <h2 style="margin: 0; font-size: 1.8rem; font-weight: 800; color: white;">
            <span class="gradient-text">DocIntel API</span>
        </h2>
        <p style="color: #64748b; font-size: 0.85rem; margin-top: 4px;">Enterprise Document Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("### 📥 Load Business Document")
    uploaded_file = st.file_uploader(
        "Upload document (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        label_visibility="collapsed"
    )
    
    # Trigger processing only when a new file is uploaded
    if uploaded_file is not None and st.session_state.filename != uploaded_file.name:
        with st.spinner("Parsing & analyzing document structure..."):
            try:
                # Prepare payload and post to the FastAPI parser service
                upload_payload = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                upload_response = requests.post(f"{BACKEND_URL}/upload", files=upload_payload)
                
                if upload_response.status_code == 200:
                    parsed_metadata = upload_response.json()
                    st.session_state.doc_id = parsed_metadata["doc_id"]
                    st.session_state.filename = parsed_metadata["filename"]
                    st.session_state.char_count = parsed_metadata["char_count"]
                    
                    # Auto-extract structured insights instantly upon successful upload
                    insights_response = requests.post(
                        f"{BACKEND_URL}/insights", 
                        json={"doc_id": st.session_state.doc_id}
                    )
                    if insights_response.status_code == 200:
                        st.session_state.insights = insights_response.json()
                    else:
                        st.session_state.insights = None
                    
                    # Reset chat history and reports for the new file session
                    st.session_state.chat_history = []
                    st.session_state.report = None
                    st.rerun()
                else:
                    error_detail = upload_response.json().get("detail", "Unknown backend parsing error.")
                    st.error(f"Upload failed: {error_detail}")
                    
            except requests.exceptions.ConnectionError:
                st.error(
                    "Unable to connect to the backend server. "
                    "Please verify that the FastAPI backend is running and matches the configured BACKEND_URL."
                )
            except Exception as e:
                st.error(f"An unexpected setup error occurred: {str(e)}")
                
    # Display document info card if a document is successfully loaded
    if st.session_state.doc_id:
        st.divider()
        st.markdown("### 📄 Active File Metadata")
        st.markdown(f"**Filename:** `{st.session_state.filename}`")
        st.markdown(f"**Document ID:** `{st.session_state.doc_id[:8]}...`")
        st.markdown(f"**Extracted Size:** `{st.session_state.char_count} characters`")
        
        if st.button("Discard Document", use_container_width=True):
            clear_active_session()
            st.rerun()

# --- Main App Layout ---
if not st.session_state.doc_id:
    # Render landing/hero interface when idle
    st.markdown("""
    <div class="hero-container">
        <h1 style="font-size: 3.5rem; font-weight: 800; margin: 0;">
            Turn Documents into <span class="gradient-text">Structured Insights</span>
        </h1>
        <p style="color: #94a3b8; font-size: 1.25rem; max-width: 800px; margin: 20px auto 0 auto; line-height: 1.6;">
            A production-ready platform that extracts key metrics, flags risks, and allows 
            contextual natural language interaction with PDF, Word, and text files using Gemini 2.0 Flash.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    columns = st.columns(3)
    
    with columns[0]:
        st.markdown("""
        <div class="glass-card fact-card">
            <h3 style="color: #6366f1; margin-top: 0; font-size: 1.3rem;">📊 Automatic Extraction</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin: 0;">
                Instantly parse structures, tables, and paragraphs to extract key facts, important figures, and core values under a structured JSON schema.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with columns[1]:
        st.markdown("""
        <div class="glass-card action-card">
            <h3 style="color: #10b981; margin-top: 0; font-size: 1.3rem;">💬 Contextual QA Chat</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin: 0;">
                Interact natively with your document context. Ask custom business questions and get responses verified only against the document text.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    with columns[2]:
        st.markdown("""
        <div class="glass-card risk-card">
            <h3 style="color: #f43f5e; margin-top: 0; font-size: 1.3rem;">📝 Executive Summaries</h3>
            <p style="color: #94a3b8; font-size: 0.95rem; line-height: 1.6; margin: 0;">
                Draft complete analytical markdown reports with structured breakdowns of numbers, key discoveries, vulnerabilities, and consultant recommendations.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <p style="color: #64748b; font-size: 0.95rem;">👈 Get started by uploading a business document in the sidebar panel.</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # Render active document workspaces
    st.markdown(f"""
    <div style="padding: 20px 0 10px 0;">
        <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800; color: white;">
            Analyzing: <span class="gradient-text">{st.session_state.filename}</span>
        </h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Responsive split view structure
    left_column, right_column = st.columns([1.1, 0.9], gap="large")
    
    with left_column:
        st.markdown("### 📊 Document Intelligence Insights")
        
        if st.session_state.insights:
            insights = st.session_state.insights
            
            def render_insights_group(title: str, items: list, card_class: str, emoji: str):
                """
                Generates a clean HTML card populated with bulleted list items.
                """
                bullet_points = "".join(
                    f"<li style='margin-bottom: 8px;'>{item}</li>" for item in items
                ) if items else "<li>No specific insights detected.</li>"
                
                st.markdown(f"""
                <div class="glass-card {card_class}">
                    <h4 style="margin: 0 0 12px 0; color: #f8fafc; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                        <span style="font-size: 1.2rem;">{emoji}</span>
                        <span>{title}</span>
                    </h4>
                    <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 0.95rem; line-height: 1.5;">
                        {bullet_points}
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Display the four primary insight categories
            render_insights_group("Key Facts", insights.get("key_facts", []), "fact-card", "💡")
            render_insights_group("Important Numbers", insights.get("important_numbers", []), "number-card", "🔢")
            render_insights_group("Action Items", insights.get("action_items", []), "action-card", "🎯")
            render_insights_group("Risk Analysis", insights.get("risks", []), "risk-card", "⚠️")
        else:
            st.warning("⚠️ Structured insights could not be auto-extracted (API rate limits).")
            if st.button("🔄 Try Extracting Insights Again", use_container_width=True):
                with st.spinner("Extracting insights..."):
                    try:
                        insights_res = requests.post(
                            f"{BACKEND_URL}/insights", 
                            json={"doc_id": st.session_state.doc_id}
                        )
                        if insights_res.status_code == 200:
                            st.session_state.insights = insights_res.json()
                            st.rerun()
                        else:
                            err = insights_res.json().get("detail", "")
                            if "quota" in err.lower() or "429" in err:
                                st.error("⚠️ Gemini API Rate Limit Exceeded (429). Please wait 30 seconds and retry.")
                            else:
                                st.error(f"Failed: {err}")
                    except Exception as e:
                        st.error(f"Failed to connect: {str(e)}")
            
    with right_column:
        workspace_tabs = st.tabs(["💬 Interactive Q&A Chat", "📝 Executive Summary Report"])
        
        # TAB 1: Real-time contextual document chat
        with workspace_tabs[0]:
            st.markdown("### Contextual Q&A")
            
            # Print history messages
            for message in st.session_state.chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Chat input listener
            if chat_prompt := st.chat_input("Ask a question about this document..."):
                with st.chat_message("user"):
                    st.write(chat_prompt)
                st.session_state.chat_history.append({"role": "user", "content": chat_prompt})
                
                # Retrieve contextual response from API
                with st.spinner("Scanning document context..."):
                    try:
                        query_payload = {
                            "doc_id": st.session_state.doc_id,
                            "question": chat_prompt
                        }
                        query_response = requests.post(f"{BACKEND_URL}/query", json=query_payload)
                        if query_response.status_code == 200:
                            api_answer = query_response.json()["answer"]
                            with st.chat_message("assistant"):
                                st.write(api_answer)
                            st.session_state.chat_history.append({"role": "assistant", "content": api_answer})
                        else:
                            error_detail = query_response.json().get("detail", "Unknown backend error.")
                            if "quota" in error_detail.lower() or "429" in error_detail:
                                st.error("⚠️ Gemini API Rate Limit Exceeded (429). Please wait a few seconds before asking again.")
                            else:
                                st.error(f"Failed to query backend: {error_detail}")
                    except Exception as e:
                        st.error(f"Error communicating with backend: {str(e)}")
                        
        # TAB 2: Consulting document generation
        with workspace_tabs[1]:
            st.markdown("### Corporate Summary Report")
            
            if st.session_state.report:
                # Render generated report markdown
                st.markdown(st.session_state.report)
                st.divider()
                st.download_button(
                    label="Download Report (Markdown)",
                    data=st.session_state.report,
                    file_name=f"Report_{st.session_state.filename.split('.')[0]}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            else:
                st.markdown("""
                <div style="text-align: center; padding: 40px 0;">
                    <p style="color: #64748b; margin-bottom: 20px;">
                        Generate a comprehensive corporate summary report with key findings, data audits, and consultant recommendations.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button("Generate Executive Report", use_container_width=True):
                    with st.spinner("Drafting professional report..."):
                        try:
                            report_response = requests.post(
                                f"{BACKEND_URL}/report",
                                json={"doc_id": st.session_state.doc_id}
                            )
                            if report_response.status_code == 200:
                                st.session_state.report = report_response.json()["report"]
                                st.rerun()
                            else:
                                error_detail = report_response.json().get("detail", "Unknown backend error.")
                                if "quota" in error_detail.lower() or "429" in error_detail:
                                    st.error("⚠️ Gemini API Rate Limit Exceeded (429). Please wait a minute and retry.")
                                else:
                                    st.error(f"Failed to generate report: {error_detail}")
                        except Exception as e:
                            st.error(f"Error generating report: {str(e)}")
