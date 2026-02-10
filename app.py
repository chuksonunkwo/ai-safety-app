import streamlit as st
import requests
import json
from fpdf import FPDF
import base64

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="HSE Incident Commander",
    page_icon="🦺",
    layout="wide"
)

# --- 2. THE AI ENGINE ---
def get_ai_response(api_key, prompt, model_type="flash"):
    """Connects to Google Gemini API"""
    try:
        # Auto-detect model version
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        data = requests.get(list_url).json()
        
        if 'error' in data:
            return None, f"API Error: {data['error']['message']}"
            
        model_name = "models/gemini-1.5-flash" # Fallback
        for m in data.get('models', []):
            if 'flash' in m['name']:
                model_name = m['name']
                break
        
        # Call API
        generate_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        response = requests.post(generate_url, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'], None
        else:
            return None, f"Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return None, f"Connection Failed: {str(e)}"

# --- 3. PDF GENERATOR ---
def create_pdf(text, report_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header
    pdf.set_font("Arial", 'B', 14)
    title = "INVESTIGATION REPORT" if "Detailed" in report_type else "FLASH REPORT"
    pdf.cell(0, 10, f"HSE: {title}", 0, 1, 'C')
    pdf.ln(10)
    
    # Content
    pdf.set_font("Arial", size=10)
    # Sanitize text for PDF (latin-1 encoding handles most standard text)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_text)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. USER INTERFACE ---
st.markdown("""
<style>
    .main-header { font-size: 2rem; font-weight: bold; color: #0E1117; }
    .report-container { background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1042/1042390.png", width=80)
st.sidebar.title("Settings")

# API Key Input (Secure Password Field)
api_key = st.sidebar.text_input("Enter Google API Key", type="password")
st.sidebar.caption("Get a key from aistudio.google.com")

# Report Toggle
report_type = st.sidebar.radio(
    "Report Depth:",
    ("Summarized (Flash Report)", "Detailed (Full Investigation)")
)

st.title("🦺 AI Incident Commander")
st.markdown("Enter an incident description below. The AI will generate a standardized HSE report.")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Input")
    scenario = st.text_area("Describe the event:", height=250, placeholder="Example: At 23:00, the night shift drilling crew reported a kick...")
    generate_btn = st.button("Generate Report 🚀", use_container_width=True)

with col2:
    st.subheader("Output")
    
    if generate_btn:
        if not api_key:
            st.error("Please enter your API Key in the sidebar.")
        elif not scenario:
            st.warning("Please describe the incident.")
        else:
            with st.spinner("Analyzing incident..."):
                # Define Prompt
                if "Detailed" in report_type:
                    prompt = f"""Act as a Lead HSE Investigator. Write a **DETAILED Level 3 Incident Report**.
                    Scenario: "{scenario}"
                    Sections: 1. INCIDENT HEADER, 2. DETAILED NARRATIVE, 3. BARRIER ANALYSIS, 4. ROOT CAUSE (5 Whys), 5. RECOMMENDATIONS."""
                else:
                    prompt = f"""Act as a Safety Officer. Write a **SUMMARIZED Flash Report**.
                    Scenario: "{scenario}"
                    Sections: 1. WHAT HAPPENED, 2. IMMEDIATE CAUSE, 3. ACTION TAKEN, 4. RISK RATING."""

                # Run AI
                report_text, error = get_ai_response(api_key, prompt)
                
                if error:
                    st.error(error)
                else:
                    st.markdown(f'<div class="report-container">{report_text}</div>', unsafe_allow_html=True)
                    
                    # PDF Download
                    pdf_data = create_pdf(report_text, report_type)
                    b64 = base64.b64encode(pdf_data).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="Incident_Report.pdf" style="text-decoration:none;">' \
                           f'<button style="width:100%; margin-top:10px; padding:10px; background-color:#28a745; color:white; border:none; border-radius:5px; cursor:pointer;">' \
                           f'📥 Download PDF</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
