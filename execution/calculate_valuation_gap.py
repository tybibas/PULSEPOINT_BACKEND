import argparse
import json
import os
import sys
import requests
from openai import OpenAI

def mock_data(ticker, budget_assumption):
    """
    Returns mock Valuation Gap.
    """
    current_price = 150.00
    implied_price = 185.00
    gap_per_share = implied_price - current_price

    return {
        "ticker": ticker,
        "trading_price": current_price,
        "implied_price": implied_price,
        "narrative_gap_per_share": round(gap_per_share, 2),
        "narrative_gap_total_mm": round(gap_per_share * 100, 2),
        "assumption_used": budget_assumption,
        "source": "Canalyst (Mock)"
    }

def calculate_gap_live(ticker, assumption, openai_key, fmp_key=None):
    """
    Live Analysis:
    1. Fetch real price/PE data from FMP (if key exists) or continue with placeholders.
    2. Use OpenAI to simulate the 'What-If'.
    """
    current_price = 150.00
    pe_ratio = 25.0
    
    if fmp_key:
        try:
            # Simple call to FMP for Quote
            url = f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={fmp_key}"
            r = requests.get(url)
            if r.status_code == 200 and r.json():
                quote = r.json()[0]
                current_price = quote.get("price", 150.00)
                pe_ratio = quote.get("pe", 25.0)
        except Exception as e:
            print(f"FMP Error: {e}", file=sys.stderr)

    # Use OpenAI to "Redrive" the valuation
    client = OpenAI(api_key=openai_key)
    prompt = f"""
    You are a Valuation Expert using the 'Driver-Based Modeling' method.
    
    Target: {ticker}
    Current Price: ${current_price}
    Current P/E: {pe_ratio}
    
    Management Assumption: "{assumption}" (e.g., '10% Growth', 'Margin Expansion 200bps').
    
    Task: Estimate the 'Implied Price' if the market fully credited this assumption. 
    (Use a standard 10-15x multiple or peer average logic).
    
    Return JSON: {{ "implied_price": float, "methodology": string }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        implied_price = data.get("implied_price", current_price)
        
        return {
            "ticker": ticker,
            "trading_price": current_price,
            "implied_price": implied_price,
            "narrative_gap_per_share": round(implied_price - current_price, 2),
            "assumption_used": assumption,
            "methodology": data.get("methodology", "Synthetic Analysis"),
            "source": "Synthetic Analyst (OpenAI + FMP)"
        }
        
    except Exception as e:
        print(f"OpenAI Error: {e}", file=sys.stderr)
        return mock_data(ticker, assumption)

def calculate_gap(ticker, assumption):
    openai_key = os.getenv("OPENAI_API_KEY")
    fmp_key = os.getenv("FMP_API_KEY") # Optional free key
    
    if openai_key:
        return calculate_gap_live(ticker, assumption, openai_key, fmp_key)

    return mock_data(ticker, assumption)

def main():
    parser = argparse.ArgumentParser(description="Calculate Valuation Gap (Synthetic Analyst).")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol.")
    parser.add_argument("--assumption", required=True, help="Management budget assumption (e.g., '10% Growth').")
    args = parser.parse_args()

    try:
        data = calculate_gap(args.ticker, args.assumption)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
