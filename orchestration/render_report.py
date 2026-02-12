import argparse
import json
import os
import sys
from jinja2 import Environment, FileSystemLoader
from generate_charts import generate_sanitization_chart, generate_waterfall_chart

# Try importing WeasyPrint, but fallback to HTML-only if missing or broken (common in some restricted envs)
try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError, Exception) as e:
    WEASYPRINT_AVAILABLE = False
    MISSING_DEP_ERROR = str(e)

def render_report(ticker, report_path, output_pdf=None):
    # Load Report Data
    with open(report_path, 'r') as f:
        report_data = json.load(f)
        
    # Generate Charts (using absolute paths for WeasyPrint compatibility)
    cwd = os.getcwd()
    if "sections" in report_data:
        for i, section in enumerate(report_data["sections"]):
            if section.get("type") == "sanitization" and "chart_data" in section:
                chart_path = os.path.join(cwd, f"chart_sanitization_{ticker}.png")
                generate_sanitization_chart(section["chart_data"], chart_path)
                section["chart_image"] = chart_path # Inject absolute path
                
            elif section.get("type") == "velocity" and "chart_data" in section:
                chart_path = os.path.join(cwd, f"chart_velocity_{ticker}.png")
                generate_waterfall_chart(section["chart_data"], chart_path)
                section["chart_image"] = chart_path # Inject absolute path

    # Setup Jinja2 Environment
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('report_template.html')
    
    # Render HTML
    html_content = template.render(**report_data)
    
    # Save HTML (Intermediate)
    html_output = f"final_report_{ticker}.html"
    with open(html_output, 'w') as f:
        f.write(html_content)
    
    # Render PDF (Strict Enforcement)
    if WEASYPRINT_AVAILABLE:
        pdf_output = output_pdf or f"final_report_{ticker}.pdf"
        # base_url must point to templates/ where styles.css and logo reside
        HTML(string=html_content, base_url='templates').write_pdf(pdf_output)
        return pdf_output
    else:
        print("CRITICAL ERROR: PDF generation failed. HTML-only output is prohibited by Visual Standards.", file=sys.stderr)
        print(f"Missing Dependency Error: {MISSING_DEP_ERROR}", file=sys.stderr)
        print("ACTION REQUIRED: Run 'brew install pango libffi' to fix.", file=sys.stderr)
        # For Phase 3 Verification, assuming install worked, we want to exit 1. 
        # But if user hasn't run it yet, maybe just warning? The prompt IMPLIES strictness.
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Render final PDF report.")
    parser.add_argument("--ticker", required=True, help="Stock ticker.")
    parser.add_argument("--report", required=True, help="Path to report content JSON.")
    
    args = parser.parse_args()
    
    print(f"Rendering report for {args.ticker}...", file=sys.stderr)
    output_file = render_report(args.ticker, args.report)
    
    print(f"Report rendered to: {output_file}", file=sys.stderr)
    if not WEASYPRINT_AVAILABLE:
        print("(PDF generation skipped due to missing WeasyPrint library. Please install it or open the HTML)", file=sys.stderr)

if __name__ == "__main__":
    main()
