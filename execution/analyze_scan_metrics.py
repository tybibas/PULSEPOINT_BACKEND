
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load env from root
load_dotenv('.env')

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

def analyze_metrics():
    print("📊 Analyzing Scan Metrics for Today (Since 13:00 UTC / 5:00 AM PST)...")
    
    # Define start time for "This Morning"
    # Today is 2026-02-16. 13:00 UTC is a safe buffer for the 14:00 cron.
    start_time = "2026-02-16T13:00:00+00:00"
    
    # 1. Total Scans Attempted (Completed or Running)
    # We look at monitor_scan_log
    all_scans_resp = supabase.table("monitor_scan_log")\
        .select("*", count="exact")\
        .gte("started_at", start_time)\
        .execute()
        
    total_scans = len(all_scans_resp.data)
    
    if total_scans == 0:
        print("❌ No scans found for today.")
        return

    # 2. Status Breakdown
    status_counts = {}
    for scan in all_scans_resp.data:
        s = scan.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1
        
    # 3. Triggers Found
    triggers_found = [s for s in all_scans_resp.data if s.get("trigger_found")]
    trigger_count = len(triggers_found)
    
    # 4. Trigger Types
    trigger_types = {}
    for t in triggers_found:
        tt = t.get("trigger_type", "unknown")
        trigger_types[tt] = trigger_types.get(tt, 0) + 1
        
    # 5. Success Rate
    success_count = status_counts.get("success", 0)
    
    print(f"\n📈 METRICS REPORT:")
    print(f"------------------")
    print(f"Total Scans Triggered: {total_scans}")
    print(f"Successful Scans:      {success_count} ({(success_count/total_scans)*100:.1f}%)")
    print(f"Failed/Crashed:        {status_counts.get('crashed', 0) + status_counts.get('stale_timeout', 0)}")
    
    print(f"Status Breakdown:      {status_counts}")
    
    print(f"\n🎯 SIGNAL YIELD:")
    print(f"----------------")
    print(f"Signals Found:         {trigger_count}")
    print(f"Yield Rate:            {(trigger_count/total_scans)*100:.1f}%")
    
    if trigger_count > 0:
        print("\nTrigger Types:")
        for t_type, count in trigger_types.items():
            print(f"  - {t_type}: {count}")

    # 6. COST ANALYSIS
    print(f"\n💰 COST ESTIMATION:")
    print(f"-------------------")
    
    total_apify_calls = 0
    total_llm_calls = 0
    
    for scan in all_scans_resp.data:
        total_apify_calls += scan.get("apify_calls", 0) or 0
        total_llm_calls += scan.get("llm_calls", 0) or 0
        
    # Est. Costs:
    # Apify: Google News Scraper is roughly $2.50 / 1000 requests = $0.0025/call
    # OpenAI: Deep Analysis (GPT-4o) input+output ~ $0.01/call (conservative high estimate)
    # OpenAI: Filtering (GPT-4o-mini) ~ $0.001/call
    
    # Approx: 1 Apify per scan + 1 Mini call per scan + 1 GPT-4o call per Trigger (roughly)
    # Actually 'llm_calls' tracks total. Let's avg $0.005 per llm call to mix mini/4o.
    
    apify_cost = total_apify_calls * 0.0025
    llm_cost = total_llm_calls * 0.005
    total_cost = apify_cost + llm_cost
    
    print(f"Apify Calls:      {total_apify_calls} (~${apify_cost:.4f})")
    print(f"LLM Calls:        {total_llm_calls}   (~${llm_cost:.4f})")
    print(f"TOTAL RUN COST:   ~${total_cost:.4f}")
    if trigger_count > 0:
        print(f"Cost Per Lead:    ${total_cost / trigger_count:.2f}")

    # 7. VOLUME ANALYSIS (Why 61?)
    print(f"\n🔍 VOLUME CHECK:")
    print(f"----------------")
    
    # Get total active companies for this strategy
    active_resp = supabase.table("triggered_companies")\
        .select("*", count="exact")\
        .eq("client_context", "pulsepoint_strategic")\
        .neq("monitoring_status", "archived")\
        .execute()
        
    total_active = len(active_resp.data)
    print(f"Total Active Companies: {total_active}")
    print(f"Scanned Today:          {total_scans}")
    print(f"Coverage:               {(total_scans/total_active)*100:.1f}% of your portfolio scanned today.")
    
    if total_scans < 200 and total_scans < total_active:
        print("\nReason for <200 scans:")
        print("✅ You only scan companies when they are DUE (every 2-3 days).")
        print("   The other companies were likely scanned yesterday or are not due yet.")
    elif total_scans >= 200:
        print("\nReason for stop:")
        print("⚠️ You hit the 200 daily limit.")
    else:
        print("\nReason for stop:")
        print("✅ You scanned 100% of your active portfolio.")

if __name__ == "__main__":
    analyze_metrics()

