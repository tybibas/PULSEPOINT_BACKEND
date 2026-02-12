import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")

class AIAnalyst:
    def __init__(self):
        if not OPENAI_KEY:
            self.client = None
            print("⚠️ WARNING: OPENAI_API_KEY not found. Synthesis will fail.")
        else:
            self.client = OpenAI(api_key=OPENAI_KEY)

    def analyze_transcript(self, ticker, content, peers):
        """
        Synthesizes the transcript content into the 'Insight-Led' Report Format.
        """
        if not self.client or not content:
            print("E: AI Analyst: Missing client or content.")
            return None

        # Truncate content if too large (simulated max token safety)
        safe_content = content[:15000] 

        prompt = f"""
        ROLE: Senior Strategic Investor Relations Consultant (The "Anti-Broker").
        TASK: Diagnose the "Say-Do Gap" in the earnings call transcript for {ticker}.
        GOAL: Produce a board-level risk audit that exposes what the market *doesn't* believe.
        
        CONTEXT:
        The text below is a raw transcript scrape.
        
        METHODOLOGY (THE "UNDER THE HOOD" AUDIT):
        1. **The Q&A Delta**: Analyze the Sentiment Drop-off.
            - Compare the "Prepared Remarks" (Scripted Optimism) vs the "Q&A" (Unscripted Friction).
            - Did the CEO stumble when pressed? Did they walk back a promise?
            - **Calculated Metric**: "Confidentiality Delta" (High/Medium/Low).
        2. **Multi-Quarter Drift**: Compare [CURRENT] vs [PREVIOUS]. "Say-Do Gap".
        3. **Diagnostic Metrics**:
            - **Linguistic Friction**: Spot "Defensive Markers" in the Q&A (e.g. "It's complex", "We aren't guiding").
            - **Valuation Gap**: What "Value Driver" are analysts obsessed with that management is avoiding? (e.g. FCF vs Stores).
        4. **Governance Discount**: If they are opaque compared to peers, label it "Narrative Cession".

        REQUIREMENTS:
        1. **Zero-Generic Policy**: Citations must be specific.
        2. **Psychological Escalation**: Use terms: "Credibility Gap", "Sentiment Delta", "Narrative Cession".
        3. **Format**: Return a JSON object strictly matching the schema below.
        
        SCHEMA:
        {{
            "target_score": <float 0-10>,
            "sentiment_delta": "<string: 'Low', 'Medium', 'High'>",
            "ai_audit_block": "<HTML string of the 'Deep-Sync' snippet>",
            "key_focus_areas": "<HTML string list of focus areas>",
            "risk_capsules_block": "<HTML string of two content capsules (High Risk & Medium Risk)>",
            "broker_hook": "<HTML string for the broker contrast element>"
        }}

        OUTPUT INSTRUCTIONS:
        - 'sentiment_delta': "High" means big drop-off (Bearish). "Low" means consistent (Bullish).
        - 'ai_audit_block': "Our analysis detects a [High/Low] Sentiment Delta. While the script emphasized [X], the Q&A revealed friction around [Y]..."
        - 'risk_capsules_block': 
            <div class="capsule high-risk">
                <div class="capsule-title">Q&A DIVERGENCE (or similar)</div>
                <div class="capsule-body">...analysis of the stumble... <strong>$XX Impact</strong>.</div>
            </div>
            
        RAW TRANSCRIPT START:
        {safe_content}
        RAW TRANSCRIPT END
        """

        try:
            print(f"I: sending analysis request for {ticker} (Length: {len(safe_content)} chars)...")
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview", # Use smart model for deep synthesis
                messages=[
                    {"role": "system", "content": "You are a specialized IR Intelligence AI. Output strictly valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"} # Ensure JSON
            )
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)

        except Exception as e:
            print(f"E: AI Analyst Synthesis failed: {e}")
            return None

analyst = AIAnalyst()
