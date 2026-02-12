import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = '.tmp/candidates_enriched.json'
OUTPUT_FILE = '.tmp/qualified_targets.json'

DIRECTIVE_RUBRIC = """
Role Definition (Non-Negotiable)
You are operating as a Senior Investor Relations Intelligence Analyst.
Your objective is to qualify public companies for QuantiFire.

Qualification Scoring (Mandatory):
Every company must be scored on (0-5 scale):
1. Narrative Density
2. Interpretation Risk
3. Institutional Ownership Importance
4. IR Sophistication
5. Alignment with QuantiFire's Feedback Intelligence Value

Only surface companies with:
- Minimum average score >= 4.0
- No individual category < 3

Output Requirements:
For each qualified company, provide:
- Core Strategic Narrative (1-2 sentences)
- Primary Interpretation Risk (1 sentence)
- Why This Company Is a Strong QuantiFire Fit (1 sentence)
- Confidence Score (1-10)
"""

def score_company(client, company_data):
    content = company_data.get('Scraped_Content', '')
    if len(content) < 500:
        print(f"Skipping {company_data['Company']} - insufficient content.")
        return None

    prompt = f"""
    Analyze the following Investor Relations content for {company_data['Company']} ({company_data['Ticker']}).
    
    Content:
    {content[:3000]}...

    Based on the following rubric, score this company and determine if they are a fit.
    
    Rubric:
    {DIRECTIVE_RUBRIC}

    Return the response in strictly valid JSON format with the following keys:
    {{
        "scores": {{
            "Narrative_Density": int,
            "Interpretation_Risk": int,
            "Institutional_Ownership_Importance": int,
            "IR_Sophistication": int,
            "Alignment": int
        }},
        "average_score": float,
        "qualified": boolean,
        "narrative": string,
        "risk": string,
        "fit_reason": string,
        "confidence": int
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Using a strong model for reasoning
            messages=[
                {"role": "system", "content": "You are a Senior IR Analyst."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error scoring {company_data['Company']}: {e}")
        return None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found.")
        return

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env")
        return

    # Initialize client
    client = OpenAI(api_key=api_key)

    with open(INPUT_FILE, 'r') as f:
        candidates = json.load(f)

    qualified_targets = []

    print(f"Scoring {len(candidates)} candidates...")
    for candidate in candidates:
        print(f"Scoring {candidate['Company']}...")
        result = score_company(client, candidate)
        
        if result and result.get('qualified') and result.get('average_score', 0) >= 4.0:
            # Check individual scores
            scores = result.get('scores', {})
            if all(s >= 3 for s in scores.values()):
                # Merge original data with analysis
                candidate.update({
                    'Scores': scores,
                    'Core_Strategic_Narrative': result.get('narrative'),
                    'Primary_Interpretation_Risk': result.get('risk'),
                    'Why_Fits': result.get('fit_reason'),
                    'Confidence_Score': result.get('confidence')
                })
                qualified_targets.append(candidate)
                print(f"*** QUALIFIED: {candidate['Company']} (Avg: {result['average_score']}) ***")
            else:
                print(f"Disqualified {candidate['Company']} due to low individual score.")
        else:
             print(f"Disqualified {candidate['Company']} (Avg: {result.get('average_score') if result else 'N/A'})")

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(qualified_targets, f, indent=2)
    
    print(f"Saved {len(qualified_targets)} qualified targets to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
