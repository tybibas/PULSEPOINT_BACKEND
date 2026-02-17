
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load env from root
load_dotenv('.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def inspect_stale():
    print("🔍 Inspecting 'Running' Scans...")
    
    # Fetch all 'running' scans
    response = supabase.table("monitor_scan_log")\
        .select("*")\
        .eq("status", "running")\
        .execute()
        
    stale = response.data
    
    if not stale:
        print("✅ No stuck scans found.")
        return

    print(f"⚠️ Found {len(stale)} stuck scans:")
    for s in stale:
        started = s.get("started_at")
        comp_id = s.get("company_id")
        
        # Try to get company name
        c_resp = supabase.table("triggered_companies").select("company").eq("id", comp_id).execute()
        comp_name = c_resp.data[0]['company'] if c_resp.data else "Unknown"
        
        print(f"   - {comp_name} (Started: {started})")

if __name__ == "__main__":
    inspect_stale()
