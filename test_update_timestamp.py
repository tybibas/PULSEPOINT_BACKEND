import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def test_update():
    company_name = "10Fold"
    print(f"🔄 Fetching {company_name}...")
    
    resp = supabase.table("triggered_companies").select("*").ilike("company", company_name).execute()
    if not resp.data:
        print("❌ Company not found")
        return

    comp = resp.data[0]
    print(f"✅ Found {comp['company']} (ID: {comp['id']})")
    print(f"   Current last_monitored_at: {comp.get('last_monitored_at')}")
    
    print("🚀 Attempting update...")
    try:
        # Update to current time
        update_resp = supabase.table("triggered_companies")\
            .update({"last_monitored_at": "now()"})\
            .eq("id", comp['id'])\
            .execute()
            
        print("✅ Update command sent.")
        print(f"data: {update_resp.data}")
        
    except Exception as e:
        print(f"❌ Update failed: {e}")

if __name__ == "__main__":
    test_update()
