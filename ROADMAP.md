# 🗺️ Sentinel-India: Future Enhancements (V2 & V3)

### 1. Advanced RAG (Retrieval-Augmented Generation)
* **Current State:** Heuristic keyword scanning via PyMuPDF.
* **Enhancement:** Indian corporate PDFs often contain scanned images instead of text. Implement **LlamaParse** or **Unstructured.io** for complex table extraction, paired with **ChromaDB/FAISS** for semantic vector search across the entire document.

### 2. Multi-Modal Table Reading (Vision)
* **Current State:** LLM reads flattened table text.
* **Enhancement:** Pass the actual image of the "Related Party Transaction" tables to `gpt-4o` (Vision) to prevent hallucination caused by bad PDF column parsing.

### 3. Agentic Self-Correction (Reflection Node)
* **Current State:** Basic `try/except` block for JSON parsing.
* **Enhancement:** Add a 4th LangGraph node: **The Critic**. If the LLM hallucinates the output schema, the Critic node catches the error, feeds the error back to the Auditor Agent, and forces it to correct its own JSON before showing it to the user.

### 4. Expanded Compliance Frameworks
* **Current State:** SEBI LODR Reg 23 & Companies Act Sec 186/188.
* **Enhancement:** Integrate CARO 2020 (specifically targeting disputed statutory dues) and RBI Master Directions for NBFCs.

### 5. Cloud Deployment (Containerization)
* **Current State:** Local Streamlit deployment.
* **Enhancement:** Write a `Dockerfile` and deploy the app to AWS Fargate or Google Cloud Run to allow public URL access without sharing local API keys.
