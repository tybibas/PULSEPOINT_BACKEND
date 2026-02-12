import requests
from bs4 import BeautifulSoup
import json
import time
import os
import yfinance as yf

# Configuration
OUTPUT_FILE = "ibex_constituents.json"
IBEX_URL = "https://en.wikipedia.org/wiki/IBEX_35"

def fetch_ibex_from_wikipedia():
    companies = []
    
    print(f"Fetching {IBEX_URL}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(IBEX_URL, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {IBEX_URL}: Status {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table with Ticker in header
        tables = soup.find_all('table')
        target_table = None
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 0:
                header_text = [th.get_text(strip=True) for th in rows[0].find_all('th')]
                if 'Ticker' in header_text and 'Company' in header_text:
                    target_table = table
                    break
        
        if not target_table:
            print(f"Could not find table with Ticker/Company in {IBEX_URL}")
            return
            
        rows = target_table.find_all('tr')[1:]
        
        print(f"Found {len(rows)} rows in table. Extracting...")
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                # Column 0: Ticker (e.g., ACS.MC)
                # Column 1: Company (e.g., ACS)
                
                ticker = cols[0].get_text(strip=True)
                company_name = cols[1].get_text(strip=True)
                
                if company_name and ticker:
                    companies.append({
                        "name": company_name,
                        "ticker": ticker
                    })
        
        print(f"Extracted {len(companies)} total companies.")

    except Exception as e:
        print(f"Error fetching {IBEX_URL}: {e}")
        return

    # Deduplicate
    unique_companies = {c['ticker']: c for c in companies}.values()
    print(f"Refining data for {len(unique_companies)} unique companies via yfinance...")
    
    enriched_companies = []
    count = 0
    total = len(unique_companies)
    
    for c in unique_companies:
        count += 1
        clean_ticker = c['ticker'].strip()
        
        # Ensure it has .MC suffix if missing (Wikipedia usually has it)
        # But verify.
        if not clean_ticker.endswith('.MC'):
             # Some might accept other suffixes, but for IBEX usually .MC
             clean_ticker = f"{clean_ticker}.MC"
             
        yf_ticker_symbol = clean_ticker
        
        print(f"[{count}/{total}] Enriching {c['name']} ({yf_ticker_symbol})...")
        
        try:
            ticker_obj = yf.Ticker(yf_ticker_symbol)
            info = ticker_obj.info
            
            if info and 'longName' in info:
                enriched_data = {
                    "ticker": c['ticker'], 
                    "yf_ticker": yf_ticker_symbol,
                    "name": info.get("longName", c['name']), 
                    "sector": info.get("sector", "N/A"),
                    "industry": info.get("industry", "N/A"),
                    "website": info.get("website", ""),
                    "description": info.get("longBusinessSummary", ""),
                    "market_cap": info.get("marketCap", 0),
                    "logo_url": info.get("logo_url", ""),
                    "fifty_two_week_change": info.get("52WeekChange", 0),
                    "current_price": info.get("currentPrice", 0),
                    "currency": info.get("currency", "EUR")
                }
                enriched_companies.append(enriched_data)
            else:
                print(f"  Warning: No data found for {yf_ticker_symbol}, keeping basic info.")
                c["sector"] = "Unknown"
                c["website"] = ""
                enriched_companies.append(c)
                
        except Exception as e:
            print(f"  Error enriching {c['name']}: {e}")
            c["sector"] = "Unknown"
            enriched_companies.append(c)
            
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_companies, f, indent=2)
        
    print(f"Total Enriched Companies: {len(enriched_companies)}")
    print(f"Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_ibex_from_wikipedia()
