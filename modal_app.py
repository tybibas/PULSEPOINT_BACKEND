import modal
from modal.mount import Mount
from fastapi.responses import Response, JSONResponse
import sys
import subprocess
import os
import json
import datetime
from pathlib import Path

# Helper to verify paths to ignore
def should_ignore(path):
    # Ignore hidden files/dirs (like .git, .env, .venv)
    if path.name.startswith("."):
        return True
    # Ignore venv explicitly if not caught by dot
    if "venv" in path.name:
        return True
    return False

# Define the image with necessary system and python dependencies
# WeasyPrint requires Pango/Cairo system libraries
image = (
    modal.Image.debian_slim()
    .apt_install("libpango-1.0-0", "libpangoft2-1.0-0", "libcairo2")
    .pip_install(
        "openai",
        "pandas",
        "requests",
        "weasyprint",
        "matplotlib",
        "numpy",
        "jinja2",
        "fastapi"
    )
    .add_local_dir(
        Path(__file__).parent,
        remote_path="/root",
        ignore=should_ignore
    )
)

# Initialize the App
app = modal.App("quantifire-report-agent")

@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()], # Loads keys from your local .env automatically
    timeout=600 # 10 minutes max for report generation
)
def generate_report(ticker: str):
    """
    Executes the DOE pipeline for the given ticker.
    1. Orchestrate (Data Gathering)
    2. Synthesize (Narrative)
    3. Render (PDF)
    
    Returns a dictionary with raw data and PDF bytes:
    {
        "pdf": b"...",
        "report_json": {...}, 
        "dossier_json": {...}
    }
    """
    print(f"🚀 [Remote] Starting Strategic Diagnostic for {ticker}...")
    
    # Ensure we are in /root
    os.chdir("/root")
    
    # Files
    dossier_path = f"dossier_{ticker}.json"
    report_path = f"report_content_{ticker}.json"
    pdf_path = f"final_report_{ticker}.pdf"

    # 1. Orchestrate
    print(f"[1/3] Gathering Intelligence...")
    cmd_1 = [
        "python3", "orchestration/orchestrate_dossier.py",
        "--ticker", ticker,
        "--output", dossier_path
    ]
    subprocess.check_call(cmd_1)
    
    # 2. Synthesize
    print(f"[2/3] Synthesizing Strategic Narrative...")
    cmd_2 = [
        "python3", "orchestration/synthesize_report.py",
        "--ticker", ticker,
        "--dossier", dossier_path,
        "--output", report_path
    ]
    subprocess.check_call(cmd_2)
    
    # 3. Render
    print(f"[3/3] Rendering Final PDF...")
    cmd_3 = [
        "python3", "orchestration/render_report.py",
        "--ticker", ticker,
        "--report", report_path
    ]
    subprocess.check_call(cmd_3)
    
    print(f"✅ DONE. PDF generated at {pdf_path}")
    
    # Read outputs
    result = {}
    
    with open(pdf_path, "rb") as f:
        result["pdf"] = f.read()

    with open(report_path, "r") as f:
        result["report_json"] = json.load(f)

    with open(dossier_path, "r") as f:
        result["dossier_json"] = json.load(f)
        
    return result

def transform_to_frontend_schema(ticker, report_data, dossier_data):
    """
    Maps the internal report structure to the Frontend Dashboard JSON schema.
    """
    meta = report_data.get("meta", {})
    sections = report_data.get("sections", [])
    
    # Extract Stock Details from Valuation Gap if available
    val_data = dossier_data.get("data", {}).get("valuation_gap", {})
    stock_price = val_data.get("trading_price", "N/A")
    if stock_price != "N/A":
        stock_price = f"${stock_price:.2f}"
    
    # Mapping Function for Section Types
    def map_section_type(internal_type):
        mapping = {
            "strategy": "analysis",
            "sanitization": "key_finding",
            "velocity": "analysis",
            "governance": "risk",
            "valuation": "analysis"
        }
        return mapping.get(internal_type, "analysis")

    # Build Frontend Sections
    frontend_sections = []
    
    # 1. Executive Summary
    exec_summary = report_data.get("executive_summary", {})
    if exec_summary:
        frontend_sections.append({
            "id": "exec-summary",
            "title": exec_summary.get("headline", "Executive Summary"),
            "content": exec_summary.get("content", ""),
            "type": "executive_summary",
            "order": 0
        })

    # 2. Main Sections
    for idx, section in enumerate(sections, start=1):
        frontend_sections.append({
            "id": f"section-{idx}",
            "title": section.get("title", "Untitled Section"),
            "content": section.get("content", section.get("insight", "")), # Fallback to insight if content missing
            "type": map_section_type(section.get("type")),
            "order": idx
        })

    # 3. Recommendations (Prescriptions)
    prescriptions = report_data.get("prescriptions", [])
    if prescriptions:
        rec_content = "### Key Strategic Initiatives\n\n"
        for p in prescriptions:
            rec_content += f"**{p.get('initiative')}**\n"
            rec_content += f"*Evidence: {p.get('evidence')}*\n"
            rec_content += f"Action: {p.get('action')}\n\n"
            
        frontend_sections.append({
            "id": "recommendations",
            "title": "Strategic Recommendations",
            "content": rec_content,
            "type": "recommendation",
            "order": len(frontend_sections)
        })

    # Construct Final JSON
    return {
        "id": f"report-{ticker}-{datetime.datetime.now().timestamp()}",
        "ticker": ticker,
        "companyName": ticker, # Placeholder until we have name data
        "generatedAt": meta.get("date", datetime.datetime.now().isoformat()),
        "sections": frontend_sections,
        "metadata": {
            "stockPrice": stock_price,
            "marketCap": "N/A", # Placeholder
            "sector": "N/A",    # Placeholder
            "industry": "N/A"   # Placeholder
        }
    }

@app.function(image=image)
@modal.web_endpoint(method="POST")
def trigger_report(item: dict):
    """
    Web Endpoint accessible via URL.
    Expects JSON body: {"ticker": "MSFT", "format": "json" (optional)}
    """
    ticker = item.get("ticker")
    fmt = item.get("format", "pdf") # Default to PDF
    
    if not ticker:
        return JSONResponse(status_code=400, content={"error": "Ticker is required"})
        
    print(f"Received trigger for {ticker} [Format: {fmt}]")
    
    # Call the heavy-lifting function
    try:
        data = generate_report.remote(ticker)
        
        if fmt == "json":
            # Transform and return JSON
            report_json = data["report_json"]
            dossier_json = data["dossier_json"]
            frontend_payload = transform_to_frontend_schema(ticker, report_json, dossier_json)
            return JSONResponse(content=frontend_payload)
            
        else:
            # Return PDF (Legacy/Default)
            pdf_bytes = data["pdf"]
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=report_{ticker}.pdf"
                }
            )
            
    except Exception as e:
        print(f"Error generating report: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
