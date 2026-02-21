# 🛡️ Sentinel-India: Agentic AI for Financial Corporate Governance

**Sentinel-India** is a Multi-Agent workflow built with LangGraph and OpenAI to automate the detection of Corporate Governance red flags in Indian financial filings (Annual Reports, AOC-4, MGT-7).

Designed to simulate the workflow of a Forensic Chartered Accountant, it cross-references "Notes to Accounts" and "Related Party Transactions" against SEBI LODR Regulation 23 and the Companies Act, 2013.

## 🚀 The Architecture
The system utilizes a 3-node LangGraph architecture:
1. **The Ingestion Agent:** Uses PyMuPDF heuristics to surgically extract "Related Party" disclosures from 400+ page PDFs, bypassing standard text noise. Includes a custom parser for Indian numbering formats (Lakhs/Crores).
2. **The Auditor Agent:** Powered by GPT-4o-mini. Prompt-engineered to act as a Forensic CA, outputting structured JSON risk assessments based on SEBI materiality thresholds.
3. **The Governance Shield:** A Regex-powered PII redactor ensuring DPDP Act compliance by masking PAN/Aadhaar data before output generation.

## 🛠️ Tech Stack
* **Orchestration:** LangGraph, LangChain
* **LLM:** OpenAI (GPT-4o-mini)
* **Document Parsing:** PyMuPDF (fitz)
* **Frontend:** Streamlit
* **Reporting:** FPDF2 (In-memory PDF generation)

## 🏃‍♂️ How to Run Locally
1. Clone the repo: `git clone [YOUR_REPO_LINK]`
2. Create virtual env: `python -m venv .venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Export API Key: `export OPENAI_API_KEY="sk-..."`
5. Run the dashboard: `streamlit run src/app.py`
