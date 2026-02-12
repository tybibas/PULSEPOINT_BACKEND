import os
import json
from supabase import create_client

# Load .env manually
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# SUPABASE CONNECTION
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY")
    exit(1)

supabase = create_client(url, key)

def test_fetch():
    print("🚀 Testing Strategy Fetch...")
    
    # Simulate the logic in monitor_companies_job.py
    CLIENT_STRATEGIES = {}
    
    try:
        resp = supabase.table("client_strategies").select("*").execute()
        if resp.data:
            for row in resp.data:
                slug = row.get("slug")
                config = row.get("config", {})
                CLIENT_STRATEGIES[slug] = config
            print(f"   ✅ Loaded {len(CLIENT_STRATEGIES)} strategies: {list(CLIENT_STRATEGIES.keys())}")
            
            # Verify specific content (e.g., Mike Ecker prompt)
            mike = CLIENT_STRATEGIES.get("mike_ecker", {})
            if "Groundbreaking" in str(mike):
                print("   ✅ Mike Ecker config looks correct.")
            else:
                print("   ⚠️ Mike Ecker config might be missing data.")
                
            # Verify PulsePoint
            pp = CLIENT_STRATEGIES.get("pulsepoint_strategic", {})
            if "Golden Hire" in str(pp):
                print("   ✅ PulsePoint Strategic config looks correct.")
        else:
            print("   ❌ No strategies found in DB!")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_fetch()
