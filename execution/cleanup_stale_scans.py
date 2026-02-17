
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load env from root
load_dotenv('.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def cleanup():
    print("🧹 Cleaning up Stale Scans (>30 minutes old)...")
    
    # Define "Stale" as > 45 mins old to be super safe
    # Current time (UTC)
    now = datetime.utcnow()
    cutoff = (now - timedelta(minutes=45)).isoformat()
    
    # 1. Fetch stale 'running' scans
    response = supabase.table("monitor_scan_log")\
        .update({
            "status": "stale_timeout",
            "completed_at": "now()",
            "error": "Manual cleanup: Scan exceeded 45m timeout."
        })\
        .eq("status", "running")\
        .lt("started_at", cutoff)\
        .execute()
        
    cleaned = response.data
    
    if not cleaned:
        print("✅ No stale scans found to clean.")
    else:
        print(f"✅ Cleaned up {len(cleaned)} stale scans.")
        for s in cleaned:
            print(f"   - Cleaned ID: {s.get('id')} (Started: {s.get('started_at')})")

if __name__ == "__main__":
    cleanup()
