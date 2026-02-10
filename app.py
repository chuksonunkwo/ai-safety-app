import streamlit as st
import requests
import json
from fpdf import FPDF
import base64

# --- CONFIGURATION ---
st.set_page_config(
    page_title="HSE Incident Commander",
    page_icon="🦺",
    layout="wide"
)

# --- HELPER FUNCTIONS ---
def get_api_key():
    """
    Tries to get the API Key from the system (Secrets).
    If not found, asks the user to paste it.
    """
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    else:
        return st.sidebar.text_input("Enter Google API Key:", type="password")

def generate_pdf(text, report_type):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    # Header
    pdf.set_font("Arial", 'B', 14)
    title = "INVESTIGATION REPORT" if "Detailed" in report_type else "FLASH REPORT"
    pdf.cell(0, 10, f"HSE: {title}", 0, 1, 'C')
    pdf.ln(10)
    
    # Body
    pdf.set_font("Arial", size=10)
    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 5, clean_text)
    
    return pdf.output(dest='S').encode('latin-1')

# --- MAIN APP ---
st.title("🦺 AI Safety Incident Commander")

# 1. GET KEY
api_key = get_api_key()

# 2. SIDEBAR SETTINGS
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1042/1042390.png", width=80)
    st.markdown("### Settings")
    report_type = st.radio(
        "Report Depth:",
        ("Summarized (Flash Report)", "Detailed (Full Investigation)")
    )
    st.info("✅ System Online")

# 3. INPUT AREA
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Incident Input")
    scenario = st.text_area("Describe the event:", height=250, placeholder="Example: Night shift, drilling crew reported a kick...")
    generate_btn = st.button("Generate Report 🚀", use_container_width=True)

# 4. OUTPUT AREA
with col2:
    st.subheader("2. Generated Report")
    
    if generate_btn:
        if not api_key:
            st.error("⚠️ Please enter an API Key in the sidebar or add it to Secrets.")
        elif not scenario:
            st.warning("⚠️ Please describe the incident.")
        else:
            with st.spinner("Analyzing incident..."):
                try:
                    # A. FIND MODEL
                    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                    data = requests.get(list_url).json()
                    
                    if 'error' in data:
                        st.error(f"API Error: {data['error']['message']}")
                        st.stop()
                        
                    model_name = "models/gemini-1.5-flash"
                    for m in data.get('models', []):
                        if 'flash' in m['name']:
                            model_name = m['name']
                            break

                    # B. DEFINE PROMPT
                    if "Detailed" in report_type:
                        prompt = f"""Act as a Lead HSE Investigator. Write a **DETAILED Level 3 Incident Report**.
                        Scenario: "{scenario}"
                        Sections: INCIDENT HEADER, DETAILED NARRATIVE, BARRIER ANALYSIS, ROOT CAUSE (5 Whys), RECOMMENDATIONS."""
                    else:
                        prompt = f"""Act as a Safety Officer. Write a **SUMMARIZED Flash Report**.
                        Scenario: "{scenario}"
                        Sections: WHAT HAPPENED, IMMEDIATE CAUSE, ACTION TAKEN, RISK RATING."""

                    # C. CALL API
                    generate_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {"contents": [{"parts": [{"text": prompt}]}]}
                    
                    response = requests.post(generate_url, headers=headers, data=json.dumps(payload))
                    
                    if response.status_code == 200:
                        report_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                        
                        # Show Text
                        st.success("Report Generated!")
                        st.markdown(f'<div style="background-color:#f0f2f6; padding:15px; border-radius:10px;">{report_text}</div>', unsafe_allow_html=True)
                        
                        # Download Button
                        pdf_data = generate_pdf(report_text, report_type)
                        b64 = base64.b64encode(pdf_data).decode()
                        href = f'<a href="data:application/octet-stream;base64,{b64}" download="Incident_Report.pdf" style="text-decoration:none;">' \
                               f'<button style="width:100%; margin-top:10px; padding:10px; background-color:#28a745; color:white; border:none; border-radius:5px; cursor:pointer;">' \
                               f'📥 Download PDF</button></a>'
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.error(f"Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"Connection Failed: {e}")
