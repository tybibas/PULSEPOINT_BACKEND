import argparse
import json
import os
import sys
from openai import OpenAI

def mock_data(ticker):
    """
    Returns mock Activism Risk data.
    """
    return {
        "ticker": ticker,
        "vulnerability_score": "High",
        "governance_gaps": ["Staggered Board (Mock)", "Poison Pill (Mock)"],
        "activist_history": "Peer 'CompetitorCorp' targeted 3 months ago (Mock).",
        "source": "FactSet SharkRepellent (Mock)"
    }

def check_risk_openai(ticker, client):
    """
    Uses OpenAI to analyze Governance/Activism risk based on training data (10-Ks, Proxy Statements).
    """
    prompt = f"""
    You are a Corporate Governance Expert.
    Analyze the governance structure of {ticker} for 'Activism Vulnerability'.
    Check for:
    1. Staggered Board vs. Declassified Board.
    2. Poison Pills (Shareholder Rights Plans).
    3. Dual-Class Share structures.
    
    Return JSON: 
    {{ 
      "vulnerability_score": "Low" | "Medium" | "High", 
      "governance_gaps": [string], 
      "summary": string 
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        data["ticker"] = ticker
        data["source"] = "Synthetic Analyst (OpenAI Knowledge)"
        return data
        
    except Exception as e:
        print(f"OpenAI Error: {e}", file=sys.stderr)
        return mock_data(ticker)

def check_risk(ticker):
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)
        return check_risk_openai(ticker, client)

    return mock_data(ticker)

def main():
    parser = argparse.ArgumentParser(description="Check for Governance Gaps (Synthetic Analyst).")
    parser.add_argument("--ticker", required=True, help="Stock ticker symbol.")
    args = parser.parse_args()

    try:
        data = check_risk(args.ticker)
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
