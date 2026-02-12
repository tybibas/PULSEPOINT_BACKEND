import json
import os
import datetime
from apify_client import ApifyClient
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Inputs
INPUT_FILE = "ftse_constituents.json"
OUTPUT_FILE = "active_triggers.json"

# Configuration
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN") 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def verify_event(client, company, event_type, title, description):
    """
    Uses LLM to verify if the search result *actually* confirms the event.
    Returns True if verified, False otherwise.
    """
    prompt = f"""
    You are a financial news analyst.
    I found a search result for company "{company}" that might indicate a "{event_type}".
    
    Search Title: {title}
    Search Snippet: {description}
    
    Task: Is this a snippet confirming that "{company}" (not a competitor/broad market report) has explicitly announced or held this event RECENTLY (or is planning it)?
    If it mentions a different company, is an old report, or generic market commentary, say NO.
    
    Answer strictly with: YES or NO.
    """
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        answer = completion.choices[0].message.content.strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"  [Error during LLM verify]: {e}")
        return False # Fail safe

def check_events():
    if not APIFY_TOKEN:
        print("Error: APIFY_API_TOKEN not found.")
        return
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found.")
        return

    client = ApifyClient(APIFY_TOKEN)
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Load companies (FTSE + DAX)
    companies = []
    
    # 1. FTSE (Skipping for DAX focused run)
    # try:
    #     with open("ftse_constituents.json", 'r') as f:
    #         ftse = json.load(f)
    #         for c in ftse: c['index_name'] = 'FTSE'
    #         companies.extend(ftse)
    # except FileNotFoundError:
    #     print("Warning: ftse_constituents.json not found.")

    # 2. DAX
    try:
        with open("dax_constituents.json", 'r') as f:
            dax = json.load(f)
            for c in dax: c['index_name'] = 'DAX'
            companies.extend(dax)
    except FileNotFoundError:
        print("Warning: dax_constituents.json not found.")
        
    if not companies:
        print("No companies found to scan.")
        return

    active_triggers = []
    
    # Dynamic Date: 30 days ago
    today = datetime.date.today()
    thirty_days_ago = today - datetime.timedelta(days=30)
    date_str = thirty_days_ago.strftime("%Y-%m-%d")
    
    # Limit to 3 for testing -> expanding for production (or robust test)
    # For now, let's scan ALL companies.
    print(f"Scanning {len(companies)} companies for events after {date_str}...")
    
    for company in companies: 
        name = company.get("name")
        ticker = company.get("ticker")
        print(f"Checking {name} ({ticker})...")
        
        # Expanded query
        query = f'"{name}" ("CFO appointment" OR "Capital Markets Day" OR "Investor Conference" OR "Perception Study") after:{date_str}'
        
        run_input = {
            "queries": query, 
            "maxPagesPerQuery": 1,
            "resultsPerPage": 5,
            "mobileResults": False,
        }
        
        try:
            run = client.actor("apify/google-search-scraper").call(run_input=run_input)
            dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
            
            for item in dataset_items:
                organic = item.get("organicResults", [])
                for result in organic:
                    title = result.get("title", "")
                    description = result.get("description", "")
                    url = result.get("url", "")
                    
                    # 1. Keyword Match
                    trigger_found = False
                    trigger_type = ""
                    lower_text = (title + " " + description).lower()
                    
                    if "cfo" in lower_text and ("appoint" in lower_text or "new" in lower_text):
                        trigger_found = True
                        trigger_type = "CFO Appointment"
                    elif "capital markets day" in lower_text or "cmd" in lower_text:
                        trigger_found = True
                        trigger_type = "Capital Markets Day"
                    elif "conference" in lower_text:
                        trigger_found = True
                        trigger_type = "Investor Conference"
                    elif "perception" in lower_text and ("study" in lower_text or "report" in lower_text):
                        trigger_found = True
                        trigger_type = "Perception Report"
                        
                    if trigger_found:
                        print(f"  [?] Potential {trigger_type}. Verifying with LLM...")
                        
                        # 2. LLM Verification
                        is_verified = verify_event(openai_client, name, trigger_type, title, description)
                        
                        if is_verified:
                            print(f"  [✓] Verified {trigger_type} for {name}")
                            active_triggers.append({
                                "company": name,
                                "ticker": ticker,
                                "website": company.get("website", ""),
                                "sector": company.get("sector", ""),
                                "description": company.get("description", ""),
                                "index_name": company.get("index_name", "FTSE"),
                                "event_type": trigger_type,
                                "title": title,
                                "url": url,
                                "description": description,
                                "detected_at": datetime.datetime.now().isoformat()
                            })
                        else:
                            print(f"  [x] Rejected false positive.")
                        
        except Exception as e:
            print(f"Error checking {name}: {e}")

    # Deduplicate triggers by URL
    unique_triggers = {t['url']: t for t in active_triggers}.values()

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(list(unique_triggers), f, indent=2)
        
    print(f"Scan complete. Found {len(unique_triggers)} verified triggers. Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    check_events()
