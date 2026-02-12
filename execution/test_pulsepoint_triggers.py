import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient
import sys
sys.path.append('.')
from execution.monitor_companies_job import process_company_scan, CLIENT_STRATEGIES, fetch_client_strategies

# Load Env
load_dotenv('.env')
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def run_test():
    print("🚀 Starting PulsePoint Trigger Verification...")
    
    # Init Clients
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    apify_client = ApifyClient(APIFY_TOKEN)
    
    # Load Strategies
    fetch_client_strategies(supabase)
    
    # Target IDs
    target_ids = [
        '062199ee-59e0-43d8-91f5-0ea381a2d51b', # Mauge
        '9793f121-c701-427a-9849-1e158ec8a79d', # Bold Brand
        'a1e4da84-af71-44dc-bf38-f907d7b2e2fd'  # Colossus
    ]
    
    print(f"🎯 Targeted {len(target_ids)} companies for Deep Scan...")
    
    # Fetch details
    resp = supabase.table("triggered_companies").select("*").in_("id", target_ids).execute()
    companies = resp.data
    
    for comp in companies:
        print(f"\n==================================================")
        print(f"🏢 TESTING: {comp.get('company')}")
        print(f"==================================================")
        try:
            # FORCE RESCAN to ensure we see the full "New Content" logic
            # even if fingerprint exists
            process_company_scan(comp, apify_client, supabase, OPENAI_KEY, force_rescan=True)
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    run_test()
