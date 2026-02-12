import os
import sys
from supabase import create_client, Client
from tabulate import tabulate
from datetime import datetime, timedelta

# Load env
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials in .env (Expected SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_cost_report(days=7):
    print(f"💰 Generatng Cost Report for last {days} days...")
    
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Fetch logs
    try:
        resp = supabase.table("monitor_scan_log").select("*").gte("started_at", cutoff).execute()
        logs = resp.data
    except Exception as e:
        print(f"Error fetching logs: {e}")
        return

    if not logs:
        print("No logs found.")
        return

    total_scans = len(logs)
    total_apify = sum(l.get('apify_calls', 0) or 0 for l in logs)
    total_llm = sum(l.get('llm_calls', 0) or 0 for l in logs)
    total_triggers = sum(1 for l in logs if l.get('trigger_found'))
    
    # Cost Assumptions
    COST_PER_APIFY_CALL = 0.03 # Avg cost for SERP + Crawl
    COST_PER_LLM_CALL = 0.04   # GPT-4o Input + Output avg
    
    est_apify_cost = total_apify * COST_PER_APIFY_CALL
    est_llm_cost = total_llm * COST_PER_LLM_CALL
    total_cost = est_apify_cost + est_llm_cost
    
    avg_cost_per_scan = total_cost / total_scans if total_scans else 0
    
    data = [
        ["Total Scans", total_scans],
        ["Triggers Found", total_triggers],
        ["Apify Calls", total_apify],
        ["LLM Calls", total_llm],
        ["Est. Apify Cost", f"${est_apify_cost:.2f}"],
        ["Est. LLM Cost", f"${est_llm_cost:.2f}"],
        ["TOTAL COST", f"${total_cost:.2f}"],
        ["Avg Cost / Scan", f"${avg_cost_per_scan:.2f}"]
    ]
    
    print(tabulate(data, headers=["Metric", "Value"], tablefmt="grid"))
    
    # Breakdown by Status
    status_counts = {}
    for l in logs:
        s = l.get('status')
        status_counts[s] = status_counts.get(s, 0) + 1
        
    print("\n📊 Status Breakdown:")
    for s, c in status_counts.items():
        print(f"  {s}: {c}")

if __name__ == "__main__":
    generate_cost_report()
