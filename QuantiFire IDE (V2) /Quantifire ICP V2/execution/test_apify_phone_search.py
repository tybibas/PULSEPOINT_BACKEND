
import os
from apify_client import ApifyClient
from dotenv import load_dotenv
import re

load_dotenv()

token = os.getenv("APIFY_API_TOKEN")

def extract_phone(text):
    # Regex for US/UK phone numbers
    # Matches: +44 20 7123 4567, (555) 123-4567, etc.
    phone_pattern = r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
    matches = re.findall(phone_pattern, text)
    valid = []
    for m in matches:
        full = "".join(m).strip()
        if len(re.sub(r'\D', '', full)) >= 10:
             valid.append(full)
    return valid

if not token:
    print("No APIFY_API_TOKEN")
else:
    client = ApifyClient(token)
    
    # Test Query: Specific person public number or IR number
    # Trying a known IR contact or just general query
    queries = [
        "Microsoft Investor Relations phone number",
        "Amy Hood Microsoft CFO phone number"
    ]
    
    for q in queries:
        print(f"--- Searching: {q} ---")
        run = client.actor("apify/google-search-scraper").call(run_input={
            "queries": q, 
            "maxPagesPerQuery": 1, 
            "resultsPerPage": 5
        })
        
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        found = False
        if items and items[0].get("organicResults"):
            for res in items[0]["organicResults"]:
                title = res.get("title", "")
                desc = res.get("description", "")
                text = f"{title} {desc}"
                
                phones = extract_phone(text)
                if phones:
                    print(f"  [Found Candidate] {phones} in '{title}'")
                    found = True
        
        if not found:
            print("  No phone numbers found in snippets.")
