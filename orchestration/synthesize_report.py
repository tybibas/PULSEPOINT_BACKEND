#!/usr/bin/env python3
import argparse
import json
import os
import sys
from openai import OpenAI

def flatten_dossier_str(dossier):
    """
    Converts the complex dossier JSON into a simplified string for the LLM context window.
    """
    return json.dumps(dossier, indent=2)

def synthesize_report(ticker, dossier_path):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found.", file=sys.stderr)
        sys.exit(1)
        
    client = OpenAI(api_key=api_key)
    
    with open(dossier_path, 'r') as f:
        dossier = json.load(f)
        
    context_data = flatten_dossier_str(dossier)
    
    prompt = f"""
    You are the QuantiFire Synthetic Analyst, a forensic specialist in investor sentiment (Governance Blindspot Auditor).
    Your goal is to perform a 'Governance Blindspot Audit' for {ticker}.
    
    INPUT DATA (Dossier):
    {context_data}
    
    TONE & PERSONA (Strict Enforcement):
    - Role: Clinical, Urgent, Fiduciary. You are alerting the CFO to a hidden risk.
    - Ban: Passive, polite, or generic language (e.g., "We recommend...", "Consider...").
    - Enforce: Direct warnings (e.g., "The Broker Filter is masking...", "This disconnect traps value...").
    - Concept: "Strategic Anxiety". The report must reveal that their current feedback loop is broken.
    
    CRITICAL ANALYSIS REQUIREMENTS:
    1. **Narrative Gap**: Explicitly contrast Management's Scripted View vs. Unvarnished Reality.
    2. **Valuation Cost**: You MUST cite the specific "Valuation Gap" amount (e.g. "$15.00") in the text as "Trapped Value".
    3. **Prescription**: The ONLY solution is "Unfiltered Buy-Side Monitoring" to bypass the Broker Filter.
    
    OUTPUT FORMAT (JSON):
    Return a valid JSON object with this EXACT structure:
    {{
      "meta": {{ "ticker": "{ticker}", "date": "Today" }},
      "executive_summary": {{
        "headline": "Urgent Action Title identifying the primary Blindspot.",
        "content": "3-4 sentences summarizing the 'Narrative Gap'. Must cite the 'NCS' drop and 'Trapped Value' amount."
      }},
      "sections": [
        {{
            "type": "strategy",
            "title": "Management's Scripted Reality.",
            "content": "Detailed 2-paragraph analysis of what management believes/projects (The 'Script'). Explain their stated strategy and confidence level in depth."
        }},
        {{
          "type": "sanitization",
          "title": "The Broker Filter is Sanitizing Feedback.",
          "chart_data": {{ 
              "category": ["Sell-Side Consensus", "Internal Sentiment (OSINT)"],
              "values": [0.8, -0.4],
              "colors": ["#FF6B00", "#B0B0B0"] 
          }},
          "insight": "Explain in detail how the sell-side is masking the internal toxicity/risk, citing specific disconnects."
        }},
        {{
          "type": "velocity",
          "title": "Q&A Sentiment Drop Reveals Credibility Risk.",
          "chart_data": {{ 
              "stages": ["Prepared Remarks", "Operational Friction", "Guidance Uncertainty", "Q&A"],
              "values": [0.9, -0.2, -0.15, 0.55],
              "is_waterfall": true
          }},
          "insight": "Specific comment on the drop. Cite the 'Credibility Gap' and analyze the implications of the Q&A erosion."
        }},
        {{
          "type": "governance",
          "title": "Governance Mechanisms fail to capture Dissent.",
          "content": "Comprehensive explanation of why the board isn't seeing this risk (blindspot). Discuss the failure of current listening posts."
        }},
        {{
          "type": "valuation",
          "title": "This Blindspot is Trapping Shareholder Value.",
          "content": "In-depth analysis of the cost of this gap. Quantify the impact on the multiple and future growth potential.",
          "data": {{ "current": float, "implied": float, "gap": float }}
        }}
      ],
    4.  **Specific Narrative Requirements**:
        -   **Sanitization Section**: You MUST include this exact sentence in the 'insight' field: "This divergence yields a Sanitization Score of 0.85, indicating that broker channels are filtering out critical negative signal."
        -   **Prescriptions**: One of the prescriptions MUST be:
            -   Initiative: "Broker Filter Bypass" (or similar)
            -   Action: "Implement Direct-to-Buy-Side surveillance to bypass the Broker Filter and detect sentiment divergences before they impact valuation."
      "prescriptions": [
         {{
            "initiative": "Deploy Unfiltered Monitoring",
            "evidence": "Broker Filter Sanitization Score (High Distortion)",
            "action": "Immediate adoption of buy-side sentiment monitoring to bypass sell-side filtering."
         }},
         {{
            "initiative": "Close The Narrative Gap",
            "evidence": "NCS Drop during Q&A",
            "action": "Address the specific unscripted friction points (identified above) in the next earnings call."
         }}
      ]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content)
        
    except Exception as e:
        print(f"Synthesis Error: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Synthesize intelligence dossier into a narrative report.")
    parser.add_argument("--ticker", required=True, help="Stock ticker.")
    parser.add_argument("--dossier", required=True, help="Path to dossier JSON.")
    parser.add_argument("--output", help="Output path for report JSON.")
    
    args = parser.parse_args()
    
    print(f"Synthesizing report for {args.ticker}...", file=sys.stderr)
    report_data = synthesize_report(args.ticker, args.dossier)
    
    # Force dynamic date
    import datetime
    report_data["meta"]["date"] = datetime.datetime.now().strftime("%B %d, %Y")
    
    output_path = args.output or f"report_content_{args.ticker}.json"
    with open(output_path, "w") as f:
        json.dump(report_data, f, indent=2)
        
    print(f"Report content saved to {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
