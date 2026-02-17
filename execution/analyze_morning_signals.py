
import os
import json
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

# Load env from root
load_dotenv('.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def analyze():
    print("🔍 Analyzing Last 10 Signals from PulsePoint...")
    
    # 1. Fetch last 10 triggers
    # We look for 'triggered' or 'pending_approval' status
    response = supabase.table("triggered_companies")\
        .select("*")\
        .in_("monitoring_status", ["triggered", "pending_approval"])\
        .order("last_monitored_at", desc=True)\
        .limit(10)\
        .execute()
        
    triggers = response.data
    
    if not triggers:
        print("❌ No recent triggers found.")
        return

    print(f"found {len(triggers)} triggers.\n")

    for i, t in enumerate(triggers):
        print(f"--- SIGNAL #{i+1} ---")
        print(f"🏢 Company: {t.get('company')} ({t.get('website')})")
        print(f"⚡ Event: {t.get('event_title')}")
        print(f"🔗 Source: {t.get('event_source_url')}")
        print(f"🕒 Time: {t.get('last_monitored_at')}")
        print(f"📊 Status: {t.get('monitoring_status')}")
        
        # 2. Fetch Leads
        # Assuming PulsePoint Strategic for now, as that's the main context
        leads_resp = supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")\
            .select("*")\
            .eq("triggered_company_id", t['id'])\
            .execute()
            
        leads = leads_resp.data
        print(f"👥 Leads Found: {len(leads)}")
        for lead in leads[:3]: # Show top 3
            print(f"   - {lead.get('name')} ({lead.get('title')}) - {lead.get('email')}")
        if len(leads) > 3:
            print(f"   ... and {len(leads)-3} more.")
            
        # 3. Fetch Email Draft
        # Check pulsepoint_email_queue
        email_resp = supabase.table("pulsepoint_email_queue")\
            .select("*")\
            .eq("triggered_company_id", t['id'])\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
            
        if email_resp.data:
            draft = email_resp.data[0]
            print(f"✉️  Draft Email ({draft.get('status')}):")
            print(f"   Subject: {draft.get('email_subject')}")
            body = draft.get('email_body', '').replace('\n', '\n   ')
            print(f"   Body:\n   {body}")
        else:
            print("❌ No draft email found.")
            
        print("\n")

if __name__ == "__main__":
    analyze()
