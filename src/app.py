import streamlit as st
import tempfile
import pandas as pd
import os
import json
from fpdf import FPDF

# --- HELPER: PDF GENERATOR ---
def generate_pdf_report(audit_data):
    """Constructs a professional PDF report from the AI's JSON output."""
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Header
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Sentinel-India: Forensic Governance Report", ln=True, align="C")
    pdf.ln(5)
    
    # 2. Key Metrics
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, f"Compliance Score: {audit_data.get('compliance_score', 'N/A')}/100", ln=True)
    pdf.cell(0, 8, f"Risk Level: {audit_data.get('risk_level', 'UNKNOWN')}", ln=True)
    
    exposure = audit_data.get('financial_exposure', '0')
    if not isinstance(exposure, (dict, list)):
        pdf.cell(0, 8, f"Financial Exposure: {exposure}", ln=True)
    
    pdf.ln(10)
    
    # 3. Red Flags Section
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Detected Governance Red Flags:", ln=True)
    pdf.set_font("Helvetica", size=11)
    
    flags = audit_data.get('red_flags', [])
    if not flags:
        pdf.cell(0, 8, "No material red flags detected during this audit cycle.", ln=True)
    else:
        for flag in flags:
            pdf.ln(4)
            # FAULT TOLERANCE: Check if the AI actually returned a dictionary
            if isinstance(flag, dict):
                pdf.set_font("Helvetica", "B", 11)
                pdf.cell(0, 8, f"Issue: {flag.get('issue', 'Unknown')} [{flag.get('severity', 'UNKNOWN')} RISK]", ln=True)
                
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 6, f"Regulation: {flag.get('regulation', 'N/A')}")
                pdf.multi_cell(0, 6, f"Evidence: {flag.get('evidence', 'N/A')}")
            else:
                # If the AI hallucinated a string, just print the string safely
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 6, f"Flag Note: {str(flag)}")
                
    return bytes(pdf.output())

# Import the graph
from sentinel_engine import app_graph

st.set_page_config(page_title="Sentinel-India | V1.0", layout="wide")

# --- CUSTOM CSS FOR STATUS BADGES ---
# --- CUSTOM CSS FOR STATUS BADGES & METRICS ---
st.markdown("""
<style>
    /* Sleek, theme-aware metric cards */
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05); /* Transparent white overlay */
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Dark-mode friendly success/error banners */
    .success-box {
        padding: 12px;
        background-color: rgba(40, 167, 69, 0.15); /* Tinted dark green */
        color: #75fca0; /* Bright neon green text */
        border-radius: 5px;
        margin-bottom: 10px;
        border: 1px solid rgba(40, 167, 69, 0.3);
    }
    .error-box {
        padding: 12px;
        background-color: rgba(220, 53, 69, 0.15); /* Tinted dark red */
        color: #ff8795; /* Bright neon red text */
        border-radius: 5px;
        margin-bottom: 10px;
        border: 1px solid rgba(220, 53, 69, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🛡️ Sentinel-India: Governance Auditor")
    st.caption("Powered by LangGraph & GPT-4o | SEBI LODR Compliance Engine")
with c2:
    st.header("🛡️")  # Using a standard emoji instead of an external image
#with c2:
#    st.image("[https://cdn-icons-png.flaticon.com/512/2910/2910795.png](https://cdn-icons-png.flaticon.com/512/2910/2910795.png)", width=50) # Generic shield icon

# --- SIDEBAR LOGS ---
st.sidebar.header("⚙️ System Monitor")
status_placeholder = st.sidebar.empty()
log_placeholder = st.sidebar.empty()

def update_log(message):
    log_placeholder.code(message)

# --- FILE UPLOAD ---
uploaded_file = st.file_uploader("Upload Annual Report (PDF)", type="pdf")

if uploaded_file:
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    if st.button("🚀 Run Forensic Audit"):
        
        # 1. INGESTION PHASE
        status_placeholder.info("Status: 🔵 Ingesting PDF...")
        update_log(f"Reading: {uploaded_file.name}\nSize: {uploaded_file.size / 1024:.2f} KB")
        
        # Prepare State
        initial_state = {
            "file_path": tmp_path, 
            "raw_text": "", 
            "rpt_section": "", 
            "analysis_result": {}, 
            "redacted_report": ""
        }
        
        # 2. EXECUTION PHASE
        try:
            # Run the Graph
            result = app_graph.invoke(initial_state)
            data = result['analysis_result']
            meta = data.get('metadata', {})
            
            # Check for API Success
            if meta.get('status') == "Success":
                status_placeholder.success("Status: 🟢 Audit Complete")
                st.markdown(f'<div class="success-box">✅ <b>API Connection Established:</b> Analysis performed by {meta.get("model")} in {meta.get("latency")}</div>', unsafe_allow_html=True)
            else:
                status_placeholder.error("Status: 🔴 Analysis Failed")
                st.markdown(f'<div class="error-box">❌ <b>API Error:</b> {meta.get("error_msg", "Unknown Error")}</div>', unsafe_allow_html=True)
            
            # 3. DASHBOARD DISPLAY
            # Helper: Safely format the exposure value
            exposure_raw = data.get('financial_exposure', '0')
            if isinstance(exposure_raw, (dict, list)):
                # If AI returns a complex object, show a placeholder
                display_exposure = "See Details ⬇"
            else:
                # If it's a string/number, show it
                display_exposure = str(exposure_raw)

            # Top Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Compliance Score", f"{data.get('compliance_score', 'N/A')}/100")
            m2.metric("Risk Level", data.get('risk_level', 'UNKNOWN'))
            m3.metric("Financial Exposure", display_exposure) # Using the safe variable
            m4.metric("AI Latency", meta.get('latency', '0s'))
            
            st.divider()

            # --- NEW: EXPORT ACTIONS ---
            st.markdown("### 📥 Export Artifacts")
            export_col1, export_col2, _ = st.columns([1, 1, 3])
            
            with export_col1:
                # Button 1: Download PDF
                pdf_bytes = generate_pdf_report(data)
                st.download_button(
                    label="📄 Download Official PDF Report",
                    data=pdf_bytes,
                    file_name="Sentinel_Audit_Report.pdf",
                    mime="application/pdf"
                )
                
            with export_col2:
                # Button 2: Download Raw JSON (for tech integration)
                json_str = json.dumps(data, indent=4)
                st.download_button(
                    label="🧑‍💻 Download Raw JSON",
                    data=json_str,
                    file_name="raw_audit_data.json",
                    mime="application/json"
                )
            st.divider()

            # Split View: Evidence vs Technicals
            tab1, tab2 = st.tabs(["🚩 Governance Red Flags", "🔍 Forensic Evidence"])
            
            with tab1:
                flags = data.get('red_flags', [])
                if flags:
                    df = pd.DataFrame(flags)
                    st.dataframe(
                        df, 
                        column_config={
                            "severity": st.column_config.TextColumn("Severity", width="small"),
                            "issue": st.column_config.TextColumn("Issue Detected", width="medium"),
                            "evidence": st.column_config.TextColumn("Source Text", width="large"),
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.success("Clean Report: No material red flags detected.")

            with tab2:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("Extracted Context (Input)")
                    st.text_area("What the AI read:", value=result.get('rpt_section', '')[:2000] + "...", height=300)
                with col_b:
                    st.subheader("Raw API Response (Output)")
                    st.json(data)

        except Exception as e:
            st.error(f"Critical System Failure: {e}")
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.remove(tmp_path)



