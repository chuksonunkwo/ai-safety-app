import streamlit as st
import requests
import json
from fpdf import FPDF
import base64
from datetime import datetime

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="HSE Incident Commander | Enterprise Edition",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS for that "Consultant" look
st.markdown("""
<style>
    .main-header { font-family: 'Helvetica', sans-serif; color: #0f172a; font-size: 2.5rem; font-weight: 700; }
    .sub-header { font-family: 'Helvetica', sans-serif; color: #64748b; font-size: 1.2rem; }
    .report-container { 
        background-color: white; 
        padding: 40px; 
        border-radius: 5px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        border-top: 5px solid #1e3a8a;
    }
    .stButton>button { 
        background-color: #1e3a8a; 
        color: white; 
        font-weight: bold; 
        border: none; 
        height: 50px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. PROFESSIONAL PDF ENGINE ---
class PDF(FPDF):
    def header(self):
        # Logo placeholder (Text for now)
        self.set_font('Arial', 'B', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'HSE ADVISORY SERVICES | CONFIDENTIAL', 0, 0, 'L')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d")}', 0, 1, 'R')
        self.ln(5)
        # Line break
        self.set_draw_color(200, 200, 200)
        self.line(10, 25, 200, 25)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()} | Internal Use Only', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font('Arial', 'B', 12)
        self.set_text_color(30, 58, 138) # Dark Blue
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(2)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        # Encode strictly to latin-1 to avoid font errors
        clean_body = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, clean_body)
        self.ln()

def create_professional_pdf(report_text, incident_type):
    pdf = PDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"INCIDENT INVESTIGATION REPORT: {incident_type.upper()}", 0, 1, 'C')
    pdf.ln(10)
    
    # Process the text (We assume the AI returns markdown-style headers with **)
    # For a simple PDF, we just dump the text, but formatted cleanly
    pdf.chapter_body(report_text)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 3. THE "TIER 1" AI LOGIC ---
def get_consultant_report(api_key, scenario, depth):
    if not api_key:
        return None, "⚠️ Security Alert: API Key missing."
    
    try:
        # A. Connection Setup
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        data = requests.get(list_url).json()
        
        if 'error' in data:
            return None, f"API Error: {data['error']['message']}"
            
        model_name = "models/gemini-1.5-flash"
        for m in data.get('models', []):
            if 'flash' in m['name']:
                model_name = m['name']
                break

        # B. "Tier 1 Consultant" Prompt Engineering
        if depth == "Strategic (Deep Dive)":
            prompt = f"""
            Act as a Senior Partner at a Tier 1 HSE Consultancy (like ERM or McKinsey).
            
            CLIENT SCENARIO: "{scenario}"
            
            TASK: 
            Draft a high-level **Root Cause Analysis & Strategic Advisory Report**.
            Tone: Professional, Objective, Authoritative. No fluff.
            
            REQUIRED STRUCTURE:
            
            1. EXECUTIVE SUMMARY
            (A concise 3-sentence overview of the failure and its impact.)
            
            2. INCIDENT CHRONOLOGY & FACTS
            (Reconstruct the likely timeline based on the scenario.)
            
            3. BARRIER FAILURE ANALYSIS (Swiss Cheese Model)
            * **Hardware Failure:** (What equipment failed?)
            * **Human Error:** (What action was missed?)
            * **Systemic Failure:** (What organizational process was broken?)
            
            4. ROOT CAUSE (The 5 Whys)
            (Drill down to the management system failure.)
            
            5. RISK CLASSIFICATION (IOGP Matrix)
            * **Actual Severity:**
            * **Potential Severity:**
            
            6. STRATEGIC RECOMMENDATIONS
            * **Immediate Containment:** (Do this now)
            * **Systemic Correction:** (Fix the process)
            * **Preventative Strategy:** (Long term culture change)
            """
        else:
            prompt = f"""
            Act as a Site Safety Lead. Write a **Flash Incident Notification**.
            Scenario: "{scenario}"
            Focus: Just the facts, immediate cause, and immediate barrier actions.
            Format: Professional Bullet Points.
            """

        # C. Execution
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

# --- 4. THE UI ---
# Sidebar
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    # API Key Handling (Check secrets first, then input)
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Enterprise License Active")
    else:
        api_key = st.text_input("Enter API Key", type="password")
        st.caption("Enter your Google Gemini Key to activate.")

    report_depth = st.radio(
        "Analysis Depth:",
        ("Operational (Flash Report)", "Strategic (Deep Dive)")
    )
    
    st.markdown("---")
    st.markdown("**Version:** 2.4.0 (Enterprise)")

# Main Area
st.markdown('<div class="main-header">HSE Incident Commander</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Root Cause Analysis & Reporting Engine</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Incident Intake")
    st.info("Describe the event below. Include time, equipment, and observed conditions.")
    scenario = st.text_area("Event Description:", height=300, placeholder="e.g., During routine pressure testing on the Skid B manifold...")
    
    generate_btn = st.button("GENERATE REPORT", use_container_width=True)

with col2:
    st.markdown("### 2. Analysis Output")
    
    if generate_btn:
        if not scenario:
            st.warning("⚠️ Please input event details.")
        else:
            with st.spinner("Consulting Knowledge Base..."):
                report_text, error = get_consultant_report(api_key, scenario, report_depth)
                
                if error:
                    st.error(error)
                else:
                    # Render the report nicely in a "Paper" look
                    st.markdown(f'<div class="report-container">{report_text}</div>', unsafe_allow_html=True)
                    
                    # Create Download Button
                    pdf_data = create_professional_pdf(report_text, "Investigation")
                    b64 = base64.b64encode(pdf_data).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="Professional_HSE_Report.pdf" style="text-decoration:none;">' \
                           f'<button style="width:100%; margin-top:20px; padding:15px; background-color:#22c55e; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">' \
                           f'📥 DOWNLOAD OFFICIAL PDF</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
