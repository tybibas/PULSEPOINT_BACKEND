import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_client_context():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("❌ Missing Supabase credentials")
        return

    supabase = create_client(url, key)

    print("🔍 Checking for 'pulsepoint_strategic' rows...")
    
    # Check count before
    res_before = supabase.table("triggered_companies")\
        .select("*", count="exact")\
        .eq("client_context", "pulsepoint_strategic")\
        .execute()
        
    count_before = res_before.count if res_before.count is not None else len(res_before.data)
    print(f"   Found {count_before} rows to update.")

    if count_before > 0:
        print("🔄 Executing update to 'quantifire'...")
        
        # Supabase update requires explicit update
        # Note: If there are many rows, we might need to verify the update took effect
        # treating 'eq' as the filter
        update_res = supabase.table("triggered_companies")\
            .update({"client_context": "quantifire"})\
            .eq("client_context", "pulsepoint_strategic")\
            .execute()
            
        print(f"   Updated {len(update_res.data)} rows.")

        # Verify
        res_after = supabase.table("triggered_companies")\
            .select("*", count="exact")\
            .eq("client_context", "pulsepoint_strategic")\
            .execute()
            
        count_after = res_after.count if res_after.count is not None else len(res_after.data)
        
        if count_after == 0:
            print("✅ Success: All rows updated to 'quantifire'.")
        else:
            print(f"⚠️ Warning: {count_after} rows still remain.")
    else:
        print("✅ No rows needed updating.")

if __name__ == "__main__":
    fix_client_context()
