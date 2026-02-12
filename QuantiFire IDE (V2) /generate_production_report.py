import os
import sys

# WeasyPrint removed due to missing system libraries (libgobject).
# PDF generation is now handled by convert_BP_to_pdf.py (Playwright).

from scraper_service import scraper
from ai_analyst import analyst

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTREACH_DIR = os.path.join(BASE_DIR, 'outreach')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'assets', 'templates')
CSS_PATH = os.path.join(BASE_DIR, 'assets', 'css', 'report_theme.css')

def analyze_transcript_live(ticker):
    """
    Live Deep-Sync Logic: Scrape -> Analyze -> Report.
    """
    print(f"--- STARTING LIVE PIPELINE FOR {ticker} ---")
    
    # 1. Scrape
    quarter = "Q3" 
    year = "2024"
    
    url = scraper.find_transcript_url(ticker, quarter, year)
    if not url:
        print("E: Could not find transcript URL. Aborting.")
        return None
        
    content = scraper.scrape_content(url)
    if not content:
        print("E: Could not scrape content. Aborting.")
        return None
    
    print(f"I: Transcript acquired. Length: {len(content)} chars.")

    # 2. Competitor Context
    competitors = scraper.get_competitor_metrics(ticker)

    # 3. SYNTHESIS (AI Analyst)
    # Fetch Street Friction Context
    friction_context = scraper.fetch_street_friction(ticker)
    
    # Combine for Deep Intelligence
    full_context = f"{content}\n\n{friction_context}"
    
    print(f"I: Synthesizing with Deep Intelligence (Transcript + Friction)...")
    insights = analyst.analyze_transcript(ticker, full_context, competitors)
    
    if not insights:
        print("E: AI Analysis returned no insight. Aborting.")
        return None

    # 4. Map to Report Data Structure
    return {
        "company_name": ticker, 
        "ticker": ticker,
        "topic": "STRATEGIC DIAGNOSTIC",
        "quarter": f"{quarter} {year}",
        "target_score": insights.get('target_score', 5.0),
        "peer1_name": competitors[0]['name'].replace(f"{ticker}-", ""),
        "peer1_score": competitors[0]['score'],
        "peer2_name": competitors[1]['name'].replace(f"{ticker}-", ""),
        "peer2_score": competitors[1]['score'],
        "key_focus_areas": insights.get('key_focus_areas', '<p>Focus areas unavailable.</p>'),
        "risk_capsules_block": insights.get('risk_capsules_block', ''),
        # We omit broker_hook to match strict template, OR append it to focus areas if really needed.
    }

def get_color_class(score):
    if score >= 7.0: return "bar-green"
    if score >= 4.0: return "bar-amber"
    return "bar-red"

def generate_production_report(ticker):
    print(f"Starting Insight-Led HTML/PDF Report for {ticker}...")
    
    if not os.path.exists(TEMPLATE_DIR):
        print(f"Error: Template directory not found at {TEMPLATE_DIR}")
        return

    # 1. LIVE DATA
    data = analyze_transcript_live(ticker)
    if not data:
        print("ABORTING: Pipeline failed.")
        return

    # 2. TEMPLATE INJECTION
    template_path = os.path.join(TEMPLATE_DIR, 'elite_report_template.html')
    with open(template_path, 'r') as f:
        template_content = f.read()

    # Pre-calculate visual attributes
    injection_map = {
        "{{ company_name }}": data['company_name'],
        "{{ ticker }}": data['ticker'],
        "{{ topic }}": data['topic'],
        "{{ quarter }}": data['quarter'],
        
        "{{ target_score }}": str(data['target_score']),
        "{{ target_width }}": str((data['target_score'] / 10) * 100),
        "{{ target_color_class }}": get_color_class(data['target_score']),
        
        "{{ peer1_name }}": data['peer1_name'],
        "{{ peer1_score }}": str(data['peer1_score']),
        "{{ peer1_width }}": str((data['peer1_score'] / 10) * 100),
        "{{ peer1_color_class }}": get_color_class(data['peer1_score']),
        
        "{{ peer2_name }}": data['peer2_name'],
        "{{ peer2_score }}": str(data['peer2_score']),
        "{{ peer2_width }}": str((data['peer2_score'] / 10) * 100),
        "{{ peer2_color_class }}": get_color_class(data['peer2_score']),
        
        "{{ key_focus_areas }}": data['key_focus_areas'],
        "{{ risk_capsules_block }}": data['risk_capsules_block']
    }
    
    # Replace
    for key, value in injection_map.items():
        template_content = template_content.replace(key, str(value))
        
    # CSS Path Fix (We are generating deep in outreach/{ticker}, but we can use absolute or relative)
    # The simplest is to embed the CSS for the PDF generator to ensure weasyprint finds it easily,
    # OR assume the file structure.
    # elite_report_template.html uses "../css/report_theme.css"
    # If we save to outreach/BP/BP.html, "../css" goes to outreach/css (wrong).
    # We need "../../assets/css/report_theme.css"
    template_content = template_content.replace('../css/report_theme.css', '../../assets/css/report_theme.css')
    template_content = template_content.replace('../qf_logo_full_white.png', '../../assets/qf_logo_full_white.png')

    # Output Directory
    output_dir = os.path.join(OUTREACH_DIR, ticker)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    html_path = os.path.join(output_dir, f"{ticker}_Sentiment_Gap_Report.html")
    pdf_path = os.path.join(output_dir, f"{ticker}_Sentiment_Gap_Report.pdf")

    # Write HTML
    with open(html_path, 'w') as f:
        f.write(template_content)
    print(f"Generated HTML: {html_path}")

    # 3. NOTIFY
    print(f"Success: HTML Generated at {html_path}")
    print(f"To convert to PDF, run: python3 convert_html_to_pdf.py \"{html_path}\" \"{pdf_path}\"")

if __name__ == "__main__":
    generate_production_report("BP")
