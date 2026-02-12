```python
import os
import sys
from playwright.sync_api import sync_playwright

def convert_report_to_pdf():
    # Setup paths
    if len(sys.argv) < 3:
        print("Usage: python3 convert_html_to_pdf.py <input_html> <output_pdf>")
        # Fallback default for dev speed (optional, or just exit)
        # sys.exit(1)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        HTML_PATH = os.path.join(BASE_DIR, "outreach", "BP", "BP_Sentiment_Gap_Report.html")
        PDF_PATH = os.path.join(BASE_DIR, "reports", "report_latest.pdf")
    else:
        HTML_PATH = sys.argv[1]
        PDF_PATH = sys.argv[2]

    print(f"Generating PDF with Playwright...")
    print(f"Source: {HTML_PATH}")
    print(f"Destination: {PDF_PATH}")

    if not os.path.exists(HTML_PATH):
        print(f"Error: HTML file not found at {HTML_PATH}")
        sys.exit(1)

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Load local HTML file
        # Convert path to file URI if it's not already
        if not HTML_PATH.startswith("file://"):
            file_uri = f"file://{os.path.abspath(HTML_PATH)}"
        else:
            file_uri = HTML_PATH
            
        page.goto(file_uri)
        
        # Determine height from content or use standard A4
        page.pdf(path=PDF_PATH, format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        
        browser.close()
        print(f"Success: PDF saved to {PDF_PATH}")

if __name__ == "__main__":
    convert_report_to_pdf()
