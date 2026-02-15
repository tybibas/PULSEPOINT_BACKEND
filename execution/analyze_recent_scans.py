import os
import sys
import json
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
execution_dir = os.path.join(parent_dir, 'execution')
if execution_dir not in sys.path:
    sys.path.append(execution_dir)

load_dotenv()

def get_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")
    return create_client(url, key)

def analyze_scans():
    supabase = get_supabase()
    
    print("📊 Fetching last 6 scan logs...")
    
    # Fetch last 10 to ensure we get 6 completed ones
    logs = supabase.table("monitor_scan_log")\
        .select("*")\
        .order("started_at", desc=True)\
        .limit(10)\
        .execute()
        
    if not logs.data:
        print("❌ No scan logs found.")
        return

    print(f"Found {len(logs.data)} logs. analyzing top 6...")
    
    for i, log in enumerate(logs.data[:6]):
        print(f"\n--- Scan {i+1} : {log.get('company_name')} ---")
        print(f"   ID: {log.get('id')}")
        print(f"   Status: {log.get('status')}")
        print(f"   Started: {log.get('started_at')}")
        print(f"   Duration: {log.get('duration_seconds')}s")
        
        # Parse counters
        counters = log.get('counters') or {}
        print(f"   Counters: {counters}")
        if isinstance(counters, str):
            try:
                counters = json.loads(counters)
            except:
                pass
        
        # Token usage estimate
        if isinstance(counters, dict):
            print(f"   Pages Fetched: {counters.get('pages_fetched', 0)}")
            print(f"   LLM Calls: {counters.get('llm_calls', 0)}")
            print(f"   Apify Calls: {counters.get('apify_calls', 0)}")
            
        # Check Trigger Status
        comp_id = log.get('company_id')
        if comp_id:
            comp_resp = supabase.table("triggered_companies").select("*").eq("id", comp_id).execute()
            if comp_resp.data:
                comp = comp_resp.data[0]
                print(f"   Current Status: {comp.get('monitoring_status')}")
                print(f"   Last Event: {comp.get('event_type')}")
                print(f"   Event Title: {comp.get('event_title')}")
                
                # Check Contacts
                contacts_resp = supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")\
                    .select("count", count="exact")\
                    .eq("triggered_company_id", comp_id)\
                    .execute()
                print(f"   Contacts Found: {contacts_resp.count}")
                
                # Check Drafts
                drafts_resp = supabase.table("pulsepoint_email_queue")\
                    .select("count", count="exact")\
                    .eq("triggered_company_id", comp_id)\
                    .execute()
                print(f"   Drafts Created: {drafts_resp.count}")
                
                # Score Factors
                if comp.get('score_factors'):
                    print(f"   Score Factors keys: {list(comp.get('score_factors').keys())}")
        
    print("\n✅ Analysis Complete.")
        
    print("\n✅ Analysis Complete.")

if __name__ == "__main__":
    import sys
    analyze_scans()
