import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta, timezone

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def main():
    print("🔍 Scan Progress Monitor (Last 10 Minutes)...")
    
    now = datetime.now(timezone.utc)
    ten_mins_ago = now - timedelta(minutes=10)
    
    resp = supabase.table("triggered_companies")\
        .select("company, last_monitored_at, monitoring_status")\
        .eq("monitoring_status", "active")\
        .eq("client_context", "pulsepoint_strategic")\
        .gt("last_monitored_at", ten_mins_ago.isoformat())\
        .execute()
        
    updated = resp.data
    updated.sort(key=lambda x: x.get('last_monitored_at'), reverse=True)
    
    print(f"🚀 Companies Scanned in Last 10 Mins: {len(updated)}")
    for comp in updated[:15]:
        print(f"   ✅ {comp['company']} ({comp['last_monitored_at']})")
        
    # Check for TRIGGERS
    print("\n🔎 Checking for Recent Triggers...")
    triggers = supabase.table("triggered_companies")\
        .select("company, event_title, event_type, last_monitored_at")\
        .eq("monitoring_status", "triggered")\
        .gt("last_monitored_at", ten_mins_ago.isoformat())\
        .execute()
        
    print(f"🎉 TRIGGERS FOUND: {len(triggers.data)}")
    for t in triggers.data:
        print(f"   🔥 {t['company']}: {t['event_title']} ({t['event_type']})")

    # Check for CONTEXT ANCHORS (Evergreen)
    print("\n🌲 Checking for Context Anchors...")
    anchors = supabase.table("triggered_companies")\
        .select("company, event_title, event_type, last_monitored_at")\
        .eq("monitoring_status", "triggered")\
        .eq("event_type", "CONTEXT_ANCHOR")\
        .gt("last_monitored_at", ten_mins_ago.isoformat())\
        .execute()
        
    print(f"⚓️ CONTEXT ANCHORS FOUND: {len(anchors.data)}")
    for a in anchors.data:
        print(f"   💎 {a['company']}: {a['event_title']}")

if __name__ == "__main__":
    main()
