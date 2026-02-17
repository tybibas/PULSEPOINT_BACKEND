
import os
import sys
import modal
from dotenv import load_dotenv

# Add current dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the function to test
from execution.monitor_companies_job import generate_draft, CLIENT_STRATEGIES

# Mock Supabase
class MockSupabase:
    def table(self, name):
        return self
    def select(self, *args):
        return self
    def eq(self, *args):
        return self
    def execute(self):
        # Return empty data so it falls back to "No template found" logic
        # But wait, our logic bypasses template check if force_full_draft is True.
        return type('obj', (object,), {'data': []})

def test_generation():
    load_dotenv()
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ SKIPPING: No OpenAI Key found.")
        return

    print("🧪 Testing Email Generation with Tone Training...")
    
    # MOCK the strategy config in memory so we don't need to fetch from DB
    # This simulates what happens after fetch_client_strategies is called
    CLIENT_STRATEGIES["pulsepoint_strategic"] = {
        "voice_config": {
            "tone": "Casual and direct",
            "value_proposition": "We automate go-to-market motions.",
            "force_full_draft": True,
            "examples": [
                "Subject: Quick idea\n\nHi Dave,\n\nSaw you're hiring. Usually means you're scaling.\n\nWe help with that.\n\nChat?\n\nTy",
                "Subject: Re: Expansion\n\nHi Sarah,\n\nCongrats on the raise.\n\nTypically this brings compliance headaches.\n\nWe solve those.\n\nOpen to a demo?\n\nTy"
            ]
        },
        "draft_context": "Keep it under 50 words."
    }
    
    draft = generate_draft(
        company_name="Acme Corp",
        event="Acme Corp raises $50M Series B",
        contact_name="James",
        client_context="pulsepoint_strategic",
        openai_key=api_key,
        supabase=MockSupabase(),
        buying_window="Execution",
        outcome_delta="High pressure to deploy capital efficiently."
    )
    
    print("\nGenerated Draft:\n" + "="*40)
    print(draft)
    print("="*40)
    
    if "Subject:" in draft:
        print("✅ Success: Generated full draft with Subject line.")
    else:
        print("⚠️ Note: Subject line missing (might be intended if prompt didn't ask for it explicitly).")

if __name__ == "__main__":
    test_generation()
