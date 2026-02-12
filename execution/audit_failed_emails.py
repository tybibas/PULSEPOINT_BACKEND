import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Check for failed emails
result = supabase.table("pulsepoint_email_queue").select("id, email_to, status, last_error, created_at").eq("status", "failed").execute()

print(f"=== Failed Emails: {len(result.data)} ===")
for row in result.data:
    email = row.get("email_to", "unknown")
    error = str(row.get("last_error", "None"))[:100]
    created = row.get("created_at", "unknown")
    print(f"To: {email}")
    print(f"Error: {error}...")
    print(f"Created: {created}")
    print()
