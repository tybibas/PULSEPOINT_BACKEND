import requests
from bs4 import BeautifulSoup
import json
import time
import os
import yfinance as yf

# Configuration
OUTPUT_FILE = "dax_constituents.json"
DAX_URL = "https://en.wikipedia.org/wiki/DAX"
TABLE_ID = "constituents"

def fetch_dax_from_wikipedia():
    companies = []
    
    print(f"Fetching {DAX_URL}...")
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(DAX_URL, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {DAX_URL}: Status {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', id=TABLE_ID)
        
        if not table:
            print(f"Could not find table with id {TABLE_ID} in {DAX_URL}")
            return
            
        rows = table.find_all('tr')[1:]
        
        print(f"Found {len(rows)} rows in table. extracting...")
        
        # DEBUG: Print first row to verify columns
        if len(rows) > 0:
            first_cols = [c.get_text(strip=True) for c in rows[0].find_all('td')]
            print(f"DEBUG: First row columns: {first_cols}")
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 3: # Need at least 3-4 cols
                # Wikipedia DAX table structure varies.
                # Usually: Company, Prime Standard Sector, Ticker symbol, Index weighting...
                
                # Check based on debug output. 
                # If Col 0 is "Adidas", that's Name.
                # If Col 2 is "ADS", that's Ticker.
                # If I got them swapped, let's verify.
                
                # DEBUG: First row columns: ['ADS.DE', '', 'Adidas', 'Apparel', '2.5', '062,035 (2024)', '1924']
                # Col 0: Ticker
                # Col 2: Name
                
                ticker = cols[0].get_text(strip=True)
                company_name = cols[2].get_text(strip=True)
                
                if company_name and ticker:
                    companies.append({
                        "name": company_name,
                        "ticker": ticker
                    })
        
        print(f"Extracted {len(companies)} total companies.")

    except Exception as e:
        print(f"Error fetching {DAX_URL}: {e}")
        return

    # Deduplicate
    unique_companies = {c['ticker']: c for c in companies}.values()
    print(f"Refining data for {len(unique_companies)} unique companies via yfinance...")
    
    enriched_companies = []
    count = 0
    total = len(unique_companies)
    
    for c in unique_companies:
        count += 1
        raw_ticker = c['ticker']
        # DAX tickers on Wikipedia often look like "ADS" (Adidas).
        # yfinance needs "ADS.DE" (Xetra).
        # Sometimes wiki has "ADS.DE" already? Usually just the code.
        
        clean_ticker = raw_ticker.replace(" ", "")
        
        # Handle cases like "AIR.PA" -> We want "AIR.DE" for consistency in DAX context
        # or maybe the user wants the primary listing? 
        # But for "DAX Universe", Xetra prices are best.
        if "." in clean_ticker and ".DE" not in clean_ticker:
             clean_ticker = clean_ticker.split(".")[0]
        
        # Check if already has suffix
        if ".DE" in clean_ticker:
            yf_ticker_symbol = clean_ticker
        else:
            yf_ticker_symbol = f"{clean_ticker}.DE"
            
        # Siemens Energy example: ENR. But wait, Siemens Energy is ENR.DE
        # SAP is SAP.DE
        
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
    fetch_dax_from_wikipedia()
