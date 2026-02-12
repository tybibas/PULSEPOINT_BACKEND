
import os
import sys
import time
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient
from monitor_companies_job import process_company_scan  # Import the ACTUAL function

# Load env
load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
APIFY_KEY = os.environ.get("APIFY_API_KEY")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")

def main():
    print("🚀 Starting Batch Battle Test...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    apify_client = ApifyClient(APIFY_KEY)
    # 1. Fetch Due Companies (Dynamic) -> OVERRIDE for DEBUGging
    print("⏳ Fetching 10Fold for DEBUG scan...")
    
    resp = supabase.table("triggered_companies")\
        .select("*")\
        .ilike("company", "10Fold")\
        .execute()
        
    all_companies = resp.data
    companies_to_scan_data = all_companies
    
    print(f"🚀 Starting SINGLE SCAN for {len(companies_to_scan_data)} companies...")
    
    for i, comp in enumerate(companies_to_scan_data):
        print(f"\n[{i+1}/{len(companies_to_scan_data)}] Processing {comp.get('company')}...")
        try:
            process_company_scan(comp, apify_client, supabase, OPENAI_KEY)
            print(f"✅ Finished {comp.get('company')}")
        except Exception as e:
            print(f"❌ Error processing {comp.get('company')}: {e}")
            import traceback
            traceback.print_exc()
            
    print("\n✅ Batch Scan Complete.")

if __name__ == "__main__":
    main()
