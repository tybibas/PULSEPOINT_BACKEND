#!/usr/bin/env python3
"""
Verify: Check if the battle test updated the database.
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import time

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🔍 Verifying Battle Test Results...")
    print("=" * 50)
    
    # Wait for async job to complete
    print("\n⏳ Waiting 15 seconds for async job to complete...")
    time.sleep(15)
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Check the test company
    test_company_id = "a70f9c3d-efc8-438b-892a-9a7be95e2641"
    
    print(f"\n1️⃣ Checking company: {test_company_id[:8]}...")
    resp = supabase.table("triggered_companies").select("company, last_monitored_at, event_type, event_title").eq("id", test_company_id).execute()
    
    if resp.data:
        company = resp.data[0]
        print(f"   Company: {company['company']}")
        print(f"   Last Monitored: {company.get('last_monitored_at', 'NOT UPDATED')}")
        print(f"   Event Type: {company.get('event_type', 'None')}")
        print(f"   Event Title: {company.get('event_title', 'None')}")
        
        if company.get('last_monitored_at'):
            print("   ✅ last_monitored_at WAS UPDATED!")
        else:
            print("   ⚠️ last_monitored_at not updated yet (job may still be running)")
    
    # Check for new drafts
    print(f"\n2️⃣ Checking for new drafts...")
    drafts = supabase.table("pulsepoint_email_queue").select("*").eq("status", "draft").order("created_at", desc=True).limit(5).execute()
    
    if drafts.data:
        print(f"   ✅ Found {len(drafts.data)} draft(s)!")
        for d in drafts.data:
            print(f"      - To: {d.get('email_to')} | Subject: {d.get('email_subject', 'N/A')[:40]}...")
    else:
        print("   (No drafts found - trigger may not have been detected for this company)")
    
    # Check contacts exist for this company
    print(f"\n3️⃣ Checking contacts for this company...")
    contacts = supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").select("name, email").eq("triggered_company_id", test_company_id).execute()
    
    if contacts.data:
        print(f"   ✅ Found {len(contacts.data)} contact(s)")
        for c in contacts.data:
            print(f"      - {c.get('name', 'Unknown')}: {c.get('email', 'No email')}")
    else:
        print("   ⚠️ No contacts linked to this company")
        print("   --> Draft generation requires contacts in PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")
    
    print("\n" + "=" * 50)
    print("🔍 VERIFICATION COMPLETE")
    
if __name__ == "__main__":
    main()
