import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
import json
import time
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = '.tmp/candidates_raw.csv'
OUTPUT_FILE = '.tmp/candidates_enriched.json'

def find_ir_url_apify(client, company_name):
    query = f"{company_name} investor relations"
    print(f"Searching via Apify for: {query}")
    
    run_input = {
        "queries": query, # Changed from [query] to query (string)
        "maxPagesPerQuery": 1,
        "resultsPerPage": 1,
        "countryCode": "gb", # Default to GB for FTSE, but works broadly
    }
    
    try:
        # Run the Actor and wait for it to finish
        run = client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        # Fetch results
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        if dataset_items:
            organic = dataset_items[0].get('organicResults', [])
            if organic:
                return organic[0].get('url')
        return None
    except Exception as e:
        print(f"Apify Search error for {company_name}: {e}")
        return None

def scrape_text(url):
    print(f"Scraping: {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove scripts, styles, etc.
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        return text[:5000]
    except Exception as e:
        print(f"Scrape error for {url}: {e}")
        return ""

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found. Run 1_identify_candidates.py first.")
        return

    api_key = os.getenv("APIFY_API_KEY")
    if not api_key:
        print("APIFY_API_KEY not found in .env")
        return
        
    client = ApifyClient(api_key)

    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} candidates.")

    # Limit to 5 for testing/MVP execution as requested
    companies_to_process = df.head(5) 
    
    enriched_data = []
    
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    for _, row in companies_to_process.iterrows():
        company_name = row['Name']
        ticker = row['Ticker']
        
        print(f"Processing {company_name} ({ticker})...")
        ir_url = find_ir_url_apify(client, company_name)
        print(f"Found URL: {ir_url}")
        
        scraped_content = ""
        if ir_url:
            scraped_content = scrape_text(ir_url)
            
        enriched_data.append({
            'Company': company_name,
            'Ticker': ticker,
            'MarketCap': row['MarketCap'],
            'Exchange': row['Exchange'],
            'IR_URL': ir_url,
            'Scraped_Content': scraped_content
        })
        
        # Be polite
        time.sleep(1)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_data, f, indent=2)
    
    print(f"Saved enriched data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
