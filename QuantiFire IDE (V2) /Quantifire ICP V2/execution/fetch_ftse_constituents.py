import requests
from bs4 import BeautifulSoup
import json
import time
import os

# Configuration
import requests
from bs4 import BeautifulSoup
import json
import os

OUTPUT_FILE = "ftse_constituents.json"

SOURCES = [
    {
        "url": "https://en.wikipedia.org/wiki/FTSE_100_Index",
        "table_id": "constituents"
    },
    {
        "url": "https://en.wikipedia.org/wiki/FTSE_250_Index",
        "table_id": "constituents"
    }
]

import yfinance as yf
import time

def fetch_from_wikipedia():
    companies = []
    
    for source in SOURCES:
        print(f"Fetching {source['url']}...")
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(source['url'], headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch {source['url']}: Status {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', id=source['table_id'])
            
            if not table:
                print(f"Could not find table with id {source['table_id']} in {source['url']}")
                continue
                
            rows = table.find_all('tr')[1:]
            
            print(f"Found {len(rows)} rows in table. extracting...")
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    company_name = cols[0].get_text(strip=True)
                    ticker = cols[1].get_text(strip=True)
                    
                    if company_name and ticker:
                        companies.append({
                            "name": company_name,
                            "ticker": ticker
                        })
            
            print(f"Extracted {len(companies)} total companies so far...")

        except Exception as e:
            print(f"Error fetching {source['url']}: {e}")

    # Deduplicate
    unique_companies = {c['ticker']: c for c in companies}.values()
    print(f"Refining data for {len(unique_companies)} unique companies via yfinance...")
    
    enriched_companies = []
    count = 0
    total = len(unique_companies)
    
    # Batch processing or just sequential?
    # Sequential is fine for 350 items, might take a few minutes.
    
    for c in unique_companies:
        count += 1
        raw_ticker = c['ticker']
        # Cleanup ticker if needed. valid tickers for yfinance needs suffix .L for London
        # Wikipedia might have "AZN" or "AZN."
        clean_ticker = raw_ticker.replace(".", "") # Remove existing dot if any unusual case, but usually strip to base
        # Actually Wikipedia mostly has "AZN". 
        # But some might be "BT.A" -> "BT-A.L" or "BT.A.L"?
        # Let's simple append .L first.
        yf_ticker_symbol = f"{clean_ticker}.L"
        
        print(f"[{count}/{total}] Enriching {c['name']} ({yf_ticker_symbol})...")
        
        try:
            ticker_obj = yf.Ticker(yf_ticker_symbol)
            info = ticker_obj.info
            
            # If we get no info, yfinance often returns a dict with mostly None or just 'regularMarketPrice'
            # We check if we got a valid 'longName' or 'sector'
            
            if info and 'longName' in info:
                enriched_data = {
                    "ticker": c['ticker'], # Keep original
                    "yf_ticker": yf_ticker_symbol,
                    "name": info.get("longName", c['name']), # Prefer official name
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A"),
                    "website": info.get("website", ""),
                    "description": info.get("longBusinessSummary", ""),
                    "market_cap": info.get("marketCap", 0),
                    "logo_url": info.get("logo_url", ""), # yfinance sometimes has this
                    "fifty_two_week_change": info.get("52WeekChange", 0),
                    "current_price": info.get("currentPrice", 0),
                    "currency": info.get("currency", "GBP")
                }
                
                # Try to get YTD Return explicitly if not in info
                # info.get('ytdReturn') is usually for funds. 
                # We can approximate or just use 52WeekChange which is robust.
                # Let's stick to 52WeekChange for speed, as history() calls are slow.
                
                enriched_companies.append(enriched_data)
            else:
                print(f"  Warning: No data found for {yf_ticker_symbol}, keeping basic info.")
                c["sector"] = "Unknown"
                c["website"] = ""
                c["description"] = "No data available"
                enriched_companies.append(c)
                
        except Exception as e:
            print(f"  Error enriching {c['name']}: {e}")
            c["sector"] = "Unknown"
            enriched_companies.append(c)
            
        # Rate limit friendly?
        # yfinance/Yahoo is usually lenient but let's be safe.
        # time.sleep(0.1) 

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_companies, f, indent=2)
        
    print(f"Total Enriched Companies: {len(enriched_companies)}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_from_wikipedia()
