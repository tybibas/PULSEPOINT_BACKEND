import yfinance as yf
import pandas as pd
import os
import ssl

# Fix for macOS SSL certificate issues
ssl._create_default_https_context = ssl._create_unverified_context

# Constants
MIN_MARKET_CAP_EU_GBP = 8_000_000_000  # Approx £8B (safety margin for $10B)
MIN_MARKET_CAP_EU_EUR = 9_000_000_000  # Approx €9B (safety margin for $10B)
MIN_MARKET_CAP_US_USD = 15_000_000_000 # $15B

# Mapping indices to Wikipedia URLs for constituent scraping (most reliable free method)
INDICES = {
    "FTSE 100": "https://en.wikipedia.org/wiki/FTSE_100_Index",
    "FTSE 250": "https://en.wikipedia.org/wiki/FTSE_250_Index",
    "DAX 40": "https://en.wikipedia.org/wiki/DAX",
    "CAC 40": "https://en.wikipedia.org/wiki/CAC_40",
    "EURO STOXX 50": "https://en.wikipedia.org/wiki/EURO_STOXX_50"
}

import requests
from io import StringIO

def get_constituents(index_name):
    url = INDICES.get(index_name)
    if not url:
        return []
    
    print(f"Fetching {index_name} from {url}...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, verify=False) # verify=False because of the SSL issue
        
        tables = pd.read_html(StringIO(response.text))
        
        # Heuristics to find the right table
        df = None
        for table in tables:
            # Look for common column names
            if any(col in table.columns for col in ['Ticker', 'Symbol', 'Company', 'Constituent']):
                df = table
                break
        
        if df is None:
            print(f"Could not find table for {index_name}")
            return []

        tickers = []
        if index_name == "FTSE 100" or index_name == "FTSE 250":
            # FTSE tickers often on Wiki don't have .L suffix or have dot instead of dummy
            # Usually column is 'Ticker'
            if 'Ticker' in df.columns:
                tickers = df['Ticker'].tolist()
            elif 'EPIC' in df.columns: # Sometimes called EPIC
                tickers = df['EPIC'].tolist()
            
            # Corrections for Yahoo Finance
            cleaned = []
            for t in tickers:
                if t.endswith('.'): t = t[:-1] # Remove trailing dot
                if not t.endswith('.L'): t = f"{t}.L"
                cleaned.append(t)
            return cleaned

        elif index_name == "DAX 40":
            # DAX tickers often need .DE suffix
            # Table usually has 'Ticker symbol' or similar
            col = next((c for c in df.columns if 'Ticker' in c), None)
            if col:
                tickers = df[col].tolist()
                return [f"{t}.DE" if not t.endswith('.DE') else t for t in tickers]
        
        elif index_name == "CAC 40":
            # CAC tickers often need .PA suffix
            col = next((c for c in df.columns if 'Ticker' in c), None)
            if col:
                tickers = df[col].tolist()
                return [f"{t}.PA" if not t.endswith('.PA') else t for t in tickers]
            
        elif index_name == "EURO STOXX 50":
             col = next((c for c in df.columns if 'Ticker' in c), None)
             if col:
                # EURO STOXX is mixed exchanges, hard to generalize without looking at specific table
                # For now, pass raw and rely on search or skip complex logic for MVP
                # A lot of them might be .DE, .PA, .AS etc.
                # Let's try to infer from 'Ticker' column if it exists
                return df[col].tolist()

        return []
    except Exception as e:
        print(f"Error fetching {index_name}: {e}")
        return []

def get_market_data(tickers):
    if not tickers:
        return pd.DataFrame()
    
    # Process in chunks to avoid URL too long errors
    chunk_size = 20
    all_data = []
    
    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i+chunk_size]
        try:
            tickers_str = " ".join(chunk)
            print(f"Fetching data for chunk: {tickers_str}")
            data = yf.Tickers(tickers_str)
            
            for ticker_symbol in chunk:
                try:
                    info = data.tickers[ticker_symbol].info
                    # Extract relevant fields
                    mcap = info.get('marketCap')
                    name = info.get('longName') or info.get('shortName')
                    currency = info.get('currency')
                    exchange = info.get('exchange')
                    
                    if mcap and name:
                        all_data.append({
                            'Ticker': ticker_symbol,
                            'Name': name,
                            'MarketCap': mcap,
                            'Currency': currency,
                            'Exchange': exchange
                        })
                except Exception as e:
                    print(f"Error processing {ticker_symbol}: {e}")
        except Exception as e:
             print(f"Error creating Tickers object for chunk: {e}")

    return pd.DataFrame(all_data)

def filter_candidates(df):
    qualified = []
    
    for _, row in df.iterrows():
        cap = row['MarketCap']
        curr = row['Currency']
        
        # Simple Currency Conversion Heuristics (Static for MVP)
        usd_cap = 0
        if curr == 'GBP':
            usd_cap = cap * 1.27
        elif curr == 'EUR':
            usd_cap = cap * 1.09
        elif curr == 'USD':
            usd_cap = cap
        else:
            # Skip weird currencies or assume 1:1 if unsure (conservative)
            usd_cap = cap 
            
        # Regional Thresholds from Directive
        # UK/EU: > $10B
        # US: > $15B (Assuming we identified US stocks, though we are mostly fetching EU indices here)
        
        # Since we are scraping EU indices primarily:
        if usd_cap >= 10_000_000_000:
            qualified.append(row)
            
    return pd.DataFrame(qualified)

def main():
    if not os.path.exists('.tmp'):
        os.makedirs('.tmp')

    all_tickers = []
    for index in INDICES:
        print(f"\n--- Processing {index} ---")
        tickers = get_constituents(index)
        print(f"Found {len(tickers)} tickers.")
        all_tickers.extend(tickers)
    
    # deduplicate
    all_tickers = list(set(all_tickers))
    print(f"\nTotal unique tickers to fetch: {len(all_tickers)}")
    
    # For MVP verification speed, let's just slice the first 10 if list is huge
    # In production remove this slice
    # all_tickers = all_tickers[:10] 
    
    df = get_market_data(all_tickers)
    print(f"Fetched data for {len(df)} companies.")
    
    qualified_df = filter_candidates(df)
    print(f"Qualified {len(qualified_df)} candidates > $10B.")
    
    output_path = '.tmp/candidates_raw.csv'
    qualified_df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    main()
