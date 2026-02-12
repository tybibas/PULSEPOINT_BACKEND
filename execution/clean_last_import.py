import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def clean_recent_imports():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)

    print("Checking for recent pulsepoint_strategic imports to clean...")
    
    # Delete where client_context=pulsepoint_strategic and event_type=ICP_MATCH
    # This avoids deleting the demo/hardcoded leads
    res = supabase.table("triggered_companies")\
        .delete()\
        .eq("client_context", "pulsepoint_strategic")\
        .eq("event_type", "ICP_MATCH")\
        .execute()
        
    print(f"Deleted {len(res.data)} rows.")

if __name__ == "__main__":
    clean_recent_imports()
