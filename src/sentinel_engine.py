import fitz  # PyMuPDF
import re
import json
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import time  


# --- 1. STATE SCHEMA (The "Folder" passed between agents) ---
class AgentState(TypedDict):
    file_path: str          # Input PDF path
    raw_text: str           # Full extracted text
    rpt_section: str        # Focused 'Related Party' text
    analysis_result: Dict   # The Audit Outcome (JSON)
    redacted_report: str    # Safe Output (String)


# --- 2. HELPER: Indian Currency Parser ---
def parse_indian_currency(text_snippet):
    """
    Normalizes 'Rs. 50.5 Lakhs' or '100 Crores' into standard floats.
    Essential for math checks in the next phase.
    """
    multipliers = {'lakh': 10**5, 'lakhs': 10**5, 'crore': 10**7, 'crores': 10**7}
    pattern = r"([\d\.]+)\s*(Lakh|Lakhs|Crore|Crores)"
    matches = re.findall(pattern, text_snippet, re.IGNORECASE)
    
    normalized_values = []
    for amount, unit in matches:
        val = float(amount) * multipliers[unit.lower()]
        normalized_values.append(val)
    return normalized_values


# --- 3. NODE A: Ingestion Agent (The Scanner) ---
def ingestion_node(state: AgentState):
    print("--- 🔵 Ingestion Agent: Intelligent Scanning ---")
    doc = fitz.open(state['file_path'])
    
    relevant_pages = []
    
    # 1. Define High-Value Keywords for RPTs
    # We look for pages that have a COMBINATION of these terms
    primary_keywords = ["Related Party Disclosures", "Note 32", "Section 188"]
    secondary_keywords = ["Key Management Personnel", "KMP", "Subsidiary", "Associate", "Joint Venture"]
    
    for page in doc:
        text = page.get_text()
        
        # 2. Scoring Logic: Does this page look like an RPT table?
        score = 0
        if any(k.lower() in text.lower() for k in primary_keywords):
            score += 3  # High value for title
        if any(k.lower() in text.lower() for k in secondary_keywords):
            score += 1  # Add points for context
            
        # 3. Threshold: If score > 3, it's likely the right page
        if score >= 3:
            relevant_pages.append(f"--- PAGE {page.number} ---\n{text}")
            
    # 4. Concatenate found pages (limit to 30k chars to save tokens)
    extracted_content = "\n".join(relevant_pages)
    
    # Fallback: If nothing found, take the first 10 pages (Executive Summary)
    if not extracted_content:
        print("⚠️ Warning: No specific RPT section found. Using start of file.")
        extracted_content = ""
        for i in range(min(10, len(doc))):
            extracted_content += doc[i].get_text()
    
    print(f"Found {len(extracted_content)} characters of RPT data")
    return {"raw_text": "", "rpt_section": extracted_content[:30000]}


# --- 4. NODE B: Auditor Agent (The CA) ---
def auditor_node(state: AgentState):
    print("--- 🟠 Auditor Agent: Initiating AI Analysis ---")
    start_time = time.time()
    
    # 1. SETUP
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)    # changed from gpt-4o to gpt-4o-mini
    
    # 2. PROMPT (Keep your existing system prompt here)
    system_prompt = """
    ROLE: Senior Forensic Auditor (Sentinel-CA).
    TASK: Audit the extracted text for SEBI LODR & Companies Act violations.
    OUTPUT: JSON format with compliance_score, risk_level, red_flags, financial_exposure.
    IMPORTANT: If text is empty or irrelevant, return score 100 and note 'Insufficient Data'.
    """
    
    # Check if we actually have text to analyze
    rpt_context = state.get('rpt_section', '')
    if len(rpt_context) < 100:
        return {
            "analysis_result": {
                "compliance_score": 0,
                "risk_level": "ERROR",
                "red_flags": [{"issue": "Extraction Failed", "evidence": "No text found in PDF", "severity": "HIGH"}],
                "metadata": {"source": "System", "status": "Failed", "model": "None"}
            }
        }

    # 3. EXECUTION
    try:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this text:\n\n{rpt_context[:25000]}") # Increased limit
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Clean Markdown wrappers
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1]
            
        analysis_json = json.loads(content)
        
        # ADD METADATA FOR UI
        analysis_json['metadata'] = {
            "source": "OpenAI API",
            "status": "Success", 
            "model": "gpt-4o",
            "latency": f"{round(time.time() - start_time, 2)}s"
        }
        
    except Exception as e:
        print(f"❌ AI Error: {e}")
        analysis_json = {
            "compliance_score": 0,
            "risk_level": "API_ERROR",
            "red_flags": [{"issue": "AI Generation Failed", "evidence": str(e), "severity": "CRITICAL"}],
            "financial_exposure": "Unknown",
            "metadata": {"source": "Fallback", "status": "Error", "error_msg": str(e)}
        }

    return {"analysis_result": analysis_json}


# --- 5. NODE C: Governance Shield (The Redactor) ---
def redactor_node(state: AgentState):
    print("--- 🟢 Governance Shield: Masking PII ---")
    
    analysis_str = json.dumps(state['analysis_result'], indent=2)
    
    # Regex to hide Indian PII (PAN Cards and Aadhaar)
    pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
    aadhaar_pattern = r"\d{4}\s\d{4}\s\d{4}"
    
    redacted_text = re.sub(pan_pattern, "[REDACTED_PAN]", analysis_str)
    redacted_text = re.sub(aadhaar_pattern, "[REDACTED_UID]", redacted_text)
    
    return {"redacted_report": redacted_text}


# --- 6. GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

workflow.add_node("ingest", ingestion_node)
workflow.add_node("audit", auditor_node)
workflow.add_node("redact", redactor_node)

workflow.set_entry_point("ingest")
workflow.add_edge("ingest", "audit")
workflow.add_edge("audit", "redact")
workflow.add_edge("redact", END)

app_graph = workflow.compile()