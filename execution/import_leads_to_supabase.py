import os
import json
import uuid
import argparse
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

def import_leads(json_path: str, context_override: str = None):
    print(f"🚀 Importing leads from {json_path}...")
    
    if not os.path.exists(json_path):
        print(f"❌ File not found: {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Use override if provided, else from JSON, else default
    client_context = context_override or data.get("client_context", "pulsepoint_strategic")
    
    # Ensure it is exactly what user asked for if they passed the flag
    if context_override:
        client_context = context_override

    companies = data.get("companies", [])
    print(f"   Found {len(companies)} companies. Context: {client_context}")

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase = create_client(url, key)

    success_count = 0
    
    for comp in companies:
        company_name = comp.get("name")
        if not company_name: continue

        # Generate UUID for company
        cid = str(uuid.uuid4())

        payload = {
            "id": cid,
            "company": company_name,
            # Event fields should be NULL until the monitoring job detects a REAL trigger
            "event_type": None,
            "event_title": None,
            "event_context": None,
            "event_source_url": None,
            "client_context": client_context,
            "monitoring_status": "active",
            "created_at": "now()",
            "last_monitored_at": None  # Don't mark as monitored yet so the job will pick it up
        }

        try:
            # Upsert based on company name? OR just insert. 
            # Ideally we check if company exists to avoid dupes, but Supabase might have unique constraint on name? 
            # The SQL script used ON CONFLICT (id) DO NOTHING.
            # We don't have constraints on name typically, but let's check if it exists first to be safe.
            
            existing = supabase.table("triggered_companies").select("id").eq("company", company_name).execute()
            if existing.data:
                print(f"   ⚠️ Skipping {company_name} (already exists)")
                continue

            supabase.table("triggered_companies").insert(payload).execute()
            print(f"   ✅ Imported {company_name}")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to import {company_name}: {e}")

    print(f"\n✅ Finished. Imported {success_count}/{len(companies)} companies.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import leads to Supabase")
    parser.add_argument("--input", required=True, help="Path to JSON leads file")
    parser.add_argument("--context", help="Override client_context (e.g. 'pulsepoint_strategic')")
    args = parser.parse_args()
    
    import_leads(args.input, args.context)
