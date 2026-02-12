import os
import sys
import asyncio
from dotenv import load_dotenv
from supabase import create_client

# Add execution path
import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient

# Add execution path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from execution.monitor_companies_job import process_company_scan

load_dotenv()

def test_pulsepoint_pipeline():
    print("🚀 Starting PulsePoint Battle Test...")
    
    # Mock specific companies for testing (Real data structure)
    test_targets = [
        # {
        #     "id": "test_york_ie_001",
        #     "company": "York IE", # Function expects 'company' key not 'name'
        #     "website": "york.ie",
        #     "monitoring_status": "active",
        #     "client_context": "pulsepoint_strategic",
        #     # Add other potential keys expected by the function
        #     "monitoring_frequency": "weekly",
        #     "last_monitored_at": "2023-01-01T00:00:00Z"
        # },
        {
            "id": "test_10fold_001",
            "company": "10Fold",
            "website": "10fold.com",
            "monitoring_status": "active",
            "client_context": "pulsepoint_strategic",
            "monitoring_frequency": "weekly",
            "last_monitored_at": "2023-01-01T00:00:00Z"
        }
    ]

    # Initialize Clients
    supabase = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    apify_client = ApifyClient(os.environ["APIFY_API_KEY"])
    openai_key = os.environ["OPENAI_API_KEY"]
    
    for company in test_targets:
        print(f"\n--------------------------------------------------")
        print(f"🏢 Testing Target: {company['company']} ({company['website']})")
        print(f"--------------------------------------------------")
        
        try:
            # Check if record exists in DB to avoid FK errors if logic tries to insert related items
            # For this test, we might get errors if DB integrity is strict. 
            # Ideally we pick a REAL company ID. 
            # Let's try to fetch a REAL company ID for York IE if possible.
            resp = supabase.table("triggered_companies").select("id").eq("company", company['company']).execute()
            if resp.data:
                company['id'] = resp.data[0]['id']
                print(f"   [Clean Test] Found existing ID: {company['id']}")
            else:
                print(f"   [Warning] Using potentially fake ID: {company['id']}")

            process_company_scan(company, apify_client, supabase, openai_key)
            
            print(f"✅ Scanning complete for {company['company']}")
            
        except Exception as e:
            print(f"❌ Error testing {company['company']}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_pulsepoint_pipeline()
