#!/usr/bin/env python3
"""
Battle Test: PulsePoint Monitoring Backend
This script tests the deployed Modal webhook.
"""
import os
import requests
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
WEBHOOK_URL = "https://ty-1239--pulsepoint-monitor-worker-manual-scan-trigger.modal.run"

def main():
    print("🧪 Battle Testing Monitoring Backend...")
    print("=" * 50)
    
    # 1. Connect to Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 2. Find an active company to test
    print("\n1️⃣ Finding active test company...")
    resp = supabase.table("triggered_companies").select("id, company, monitoring_status, last_monitored_at").eq("monitoring_status", "active").limit(1).execute()
    
    if not resp.data:
        # No active companies, let's check for any company
        print("   No active companies. Checking for ANY company...")
        resp = supabase.table("triggered_companies").select("id, company, monitoring_status, last_monitored_at").limit(1).execute()
        
        if not resp.data:
            print("   ❌ No companies in database. Cannot test.")
            print("   --> Please import some companies via the Dashboard first.")
            return
    
    test_company = resp.data[0]
    print(f"   ✅ Found: {test_company['company']} (ID: {test_company['id'][:8]}...)")
    print(f"   Status: {test_company['monitoring_status']}")
    print(f"   Last Monitored: {test_company.get('last_monitored_at', 'Never')}")
    
    # 3. Trigger the webhook
    print(f"\n2️⃣ Triggering webhook...")
    print(f"   URL: {WEBHOOK_URL}")
    
    payload = {"company_id": test_company['id']}
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        if response.status_code == 200:
            print("   ✅ Webhook triggered successfully!")
        else:
            print("   ❌ Webhook returned error")
            return
            
    except Exception as e:
        print(f"   ❌ Webhook call failed: {e}")
        return
    
    # 4. Wait and check for results
    print(f"\n3️⃣ Webhook runs async. Check Modal logs for scan progress.")
    print(f"   Modal Dashboard: https://modal.com/apps/ty-1239/main/deployed/pulsepoint-monitor-worker")
    
    print("\n" + "=" * 50)
    print("🧪 BATTLE TEST COMPLETE")
    print("=" * 50)
    print("\nNext steps to verify:")
    print("  1. Check Modal logs for 'Now scanning: ...' output")
    print("  2. Query Supabase to see if last_monitored_at updated")
    print("  3. If trigger found: check pulsepoint_email_queue for new draft")
    
if __name__ == "__main__":
    main()
