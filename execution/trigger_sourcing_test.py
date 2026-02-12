import requests
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Webhook URL from deployment output
WEBHOOK_URL = "https://ty-1239--pulsepoint-monitor-worker-source-accounts-trigger.modal.run"

def trigger_sourcing():
    print("🚀 Triggering Automated Sourcing via Modal Webhook...")
    
    # 1. Get PulsePoint Strategy ID
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    client = create_client(url, key)
    
    resp = client.table("client_strategies").select("id").eq("slug", "pulsepoint_strategic").execute()
    if not resp.data:
        print("❌ PulsePoint strategy not found!")
        return
        
    strat_id = resp.data[0]['id']
    print(f"   Strategy ID: {strat_id}")
    
    # 2. Call Webhook
    payload = {"strategy_id": strat_id}
    try:
        r = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"   Status Code: {r.status_code}")
        print(f"   Response: {r.text}")
    except Exception as e:
        print(f"❌ Webhook Call Failed: {e}")

if __name__ == "__main__":
    trigger_sourcing()
