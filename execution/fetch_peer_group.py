import argparse
import json
import os
import sys
from openai import OpenAI

def mock_data(ticker):
    """
    Returns mock peer group.
    """
    return [
        {"ticker": "COMP1", "name": "Competitor One", "reason": "Mock Data"},
        {"ticker": "COMP2", "name": "Competitor Two", "reason": "Mock Data"}
    ]

def fetch_peers_openai(ticker, client):
    """
    Uses OpenAI to identify the most relevant direct competitors.
    """
    prompt = f"""
    Identify 3-5 direct publicly traded competitors for {ticker}.
    Focus on companies with similar business models and market cap.
    Return ONLY a valid JSON array of objects. Each object must have:
    - "ticker": Stock ticker.
    - "name": Company name.
    - "reason": Brief 1-sentence explanation of why they are a competitor.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        if "competitors" in data:
            return data["competitors"]
        if isinstance(data, list):
            return data
        return data
        
    except Exception as e:
        print(f"OpenAI Error: {e}", file=sys.stderr)
        return mock_data(ticker)

def fetch_peers(ticker):
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        return fetch_peers_openai(ticker, client)

    return mock_data(ticker)

def main():
    parser = argparse.ArgumentParser(description="Identify direct competitors (Synthetic Analyst via OpenAI).")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol (e.g., AAPL).")
    args = parser.parse_args()

    try:
        data = fetch_peers(args.ticker)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
