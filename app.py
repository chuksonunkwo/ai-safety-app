import streamlit as st
import requests
import json
from fpdf import FPDF
import base64
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AI HSE Incident Report",
    page_icon="🛡️",
    layout="wide"
)

# --- 2. PROFESSIONAL STYLING (CSS) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f8fafc; }
    
    /* Title Styling */
    .main-header { 
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; 
        color: #1e293b; 
        font-size: 2.2rem; 
        font-weight: 700; 
        margin-bottom: 0px;
    }
    .sub-header { 
        font-family: 'Helvetica', sans-serif; 
        color: #64748b; 
        font-size: 1rem; 
        margin-bottom: 20px;
    }
    
    /* BUTTON STYLING - FIXED HOVER */
    div.stButton > button {
        background-color: #2563eb; /* Primary Blue */
        color: white;
        font-weight: bold;
        border: none;
        padding: 15px 32px;
        font-size: 16px;
        transition: background-color 0.3s ease;
        width: 100%;
        border-radius: 8px;
    }
    div.stButton > button:hover {
        background-color: #1d4ed8; /* Darker Blue on Hover */
        color: white;
        border: 1px solid #1e40af;
    }
    div.stButton > button:active {
        background-color: #1e40af;
        transform: translateY(2px);
    }

    /* Report Box Styling */
    .report-container { 
        background-color: white; 
        padding: 40px; 
        border-radius: 8px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); 
        border-top: 5px solid #2563eb;
        font-family: 'Georgia', serif; /* Serif for reading */
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. TIER 1 PDF ENGINE (UPDATED TO REMOVE **) ---
class ConsultReport(FPDF):
    def header(self):
        if self.page_no() > 1: # No header on title page
            self.set_font('Arial', 'B', 9)
            self.set_text_color(100, 116, 139) # Slate Gray
            self.cell(0, 10, 'CONFIDENTIAL INVESTIGATION REPORT', 0, 0, 'L')
            self.cell(0, 10, f'Ref: HSE-{datetime.now().strftime("%Y%m%d")}', 0, 1, 'R')
            self.line(10, 20, 200, 20) # Header Line
            self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, f'Page {self.page_no()} | AI HSE Incident Report v1.0', 0, 0, 'C')

    def chapter_body(self, body):
        self.set_font('Times', '', 11) # Serif font for professional body text
        self.set_text_color(30, 41, 59) # Dark Slate
        
        # --- THE FIX: REMOVE MARKDOWN ASTERISKS ---
        clean_text = body.replace('**', '').replace('__', '')
        
        clean_body = clean_text.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 6, clean_body)
        self.ln(5)

def create_tier1_pdf(report_text, incident_type):
    pdf = ConsultReport()
    
    # --- PAGE 1: TITLE PAGE ---
    pdf.add_page()
    pdf.set_margins(25, 25, 25)
    
    # Logo / Company Name
    pdf.ln(60)
    pdf.set_font('Arial', 'B', 24)
    pdf.set_text_color(30, 58, 138)
    pdf.cell(0, 15, "INCIDENT INVESTIGATION", 0, 1, 'C')
    pdf.cell(0, 15, "REPORT", 0, 1, 'C')
    
    pdf.ln(20)
    pdf.set_font('Arial', '', 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, f"Type: {incident_type}", 0, 1, 'C')
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%B %d, %Y')}", 0, 1, 'C')
    
    pdf.ln(50)
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Strictly Confidential | Internal Distribution Only", 0, 1, 'C')
    
    # --- PAGE 2: THE REPORT ---
    pdf.add_page()
    pdf.chapter_body(report_text)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. AI ENGINE ---
def get_consultant_report(api_key, scenario, depth):
    if not api_key:
        return None, "⚠️ API Key missing."
    
    try:
        # Connect
        list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        data = requests.get(list_url).json()
        
        if 'error' in data:
            return None, f"API Error: {data['error']['message']}"
            
        model_name = "models/gemini-1.5-flash"
        for m in data.get('models', []):
            if 'flash' in m['name']:
                model_name = m['name']
                break

        # Prompt
        if depth == "Strategic (Deep Dive)":
            prompt = f"""
            Act as a Senior Partner at a Tier 1 HSE Consultancy.
            SCENARIO: "{scenario}"
            
            TASK: Write a formal Root Cause Analysis Report.
            TONE: Executive, precise, authoritative.
            
            STRUCTURE:
            1. EXECUTIVE SUMMARY (Bold, concise).
            2. SEQUENCE OF EVENTS (Reconstructed timeline).
            3. BARRIER FAILURE ANALYSIS (Swiss Cheese Model).
            4. ROOT CAUSE (5 Whys methodology).
            5. STRATEGIC RECOMMENDATIONS (Immediate & Systemic).
            
            Format the output with clear headers using markdown (**Header**).
            """
        else:
            prompt = f"""
            Act as a Site Safety Lead. Write a Flash Incident Notification.
            SCENARIO: "{scenario}"
            STRUCTURE: 
            1. WHAT HAPPENED
            2. IMMEDIATE ACTIONS
            3. RISK RATING
            """

        # Call
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

# --- 5. THE UI LAYOUT ---
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # SECURE API KEY HANDLING
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
        st.success("✅ Enterprise License Active")
    else:
        api_key = st.text_input("Enter API Key", type="password")

    report_depth = st.radio(
        "Report Depth:",
        ("Operational (Flash Report)", "Strategic (Deep Dive)")
    )
    
    st.markdown("---")
    st.markdown("**Version:** 1.0 (Production)")

# HEADER
st.markdown('<div class="main-header">AI HSE Incident Report</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Root Cause Analysis & Reporting Engine</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown("### 1. Incident Details")
    scenario = st.text_area("Event Description:", height=300, placeholder="e.g., During lifting operations on the main deck, the crane load cell failed...")
    
    # This button now has the specific CSS class to highlight blue
    generate_btn = st.button("GENERATE REPORT")

with col2:
    st.markdown("### 2. Analysis Output")
    
    if generate_btn:
        if not scenario:
            st.warning("⚠️ Please input event details.")
        else:
            with st.spinner("Analyzing Root Causes..."):
                report_text, error = get_consultant_report(api_key, scenario, report_depth)
                
                if error:
                    st.error(error)
                else:
                    # Render Report
                    st.markdown(f'<div class="report-container">{report_text}</div>', unsafe_allow_html=True)
                    
                    # PDF Download
                    pdf_data = create_tier1_pdf(report_text, report_depth)
                    b64 = base64.b64encode(pdf_data).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="HSE_Incident_Report_v1.pdf" style="text-decoration:none;">' \
                           f'<button style="width:100%; margin-top:20px; padding:15px; background-color:#10b981; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">' \
                           f'📥 DOWNLOAD OFFICIAL PDF</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
