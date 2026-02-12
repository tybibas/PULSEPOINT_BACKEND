import argparse
import json
import os
import sys
from openai import OpenAI

def mock_data(ticker):
    """
    Returns mock strategic pillars as fallback.
    """
    return [
        {
            "pillar": "Margin Expansion (Mock)",
            "source": f"{ticker} IR Landing Page",
            "description": "Targeting 200bps improvement via operational efficiency."
        },
        {
            "pillar": "Cloud Transition (Mock)",
            "source": f"{ticker} Q3 Prepared Remarks",
            "description": "Accelerating migration of legacy workloads to the cloud."
        },
        {
            "pillar": "ESG Leadership (Mock)",
            "source": f"{ticker} Annual Report",
            "description": "Commitment to carbon neutrality by 2030."
        }
    ]

def fetch_strategy_openai(ticker, client):
    """
    Uses OpenAI to extract strategic pillars from its internal knowledge 
    (or potentially scraped text if we add that later).
    """
    prompt = f"""
    You are a Senior Equity Research Analyst. 
    Identify the top 3-5 'Strategic Pillars' or key strategic initiatives for {ticker} based on their latest investor presentations and earnings calls.
    Return ONLY a valid JSON array of objects. Each object must have:
    - "pillar": Short title of the strategy.
    - "description": Brief 1-sentence explanation.
    - "source": Likely source (e.g., "2024 Annual Report", "Q3 Earnings Call").
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        # Ensure we parse the JSON wrapper if GPT returns { "pillars": [...] } or just [...]
        data = json.loads(content)
        if "pillars" in data:
            return data["pillars"]
        if isinstance(data, list):
            return data
        return data # Fallback
        
    except Exception as e:
        print(f"OpenAI Error: {e}", file=sys.stderr)
        return mock_data(ticker)

def fetch_strategy(ticker):
    """
    Main fetch logic. Tries OpenAI first, then falls back to Mock.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        return fetch_strategy_openai(ticker, client)

    return mock_data(ticker)

def main():
    parser = argparse.ArgumentParser(description="Extract 'Strategic Pillars' using OpenAI (Synthetic Analyst).")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol (e.g., AAPL).")
    args = parser.parse_args()

    try:
        data = fetch_strategy(args.ticker)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
