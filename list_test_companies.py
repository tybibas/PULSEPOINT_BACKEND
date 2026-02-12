
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

resp = supabase.table("triggered_companies").select("id, company, website, client_context").limit(50).execute()

print(f"{'Company':<30} | {'Website':<30} | {'Client Context'}")
print("-" * 80)
for c in resp.data:
    company = c.get('company') or "Unknown"
    website = c.get('website') or "N/A"
    context = c.get('client_context') or "Unknown"
    print(f"{company[:30]:<30} | {website[:30]:<30} | {context}")
