
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

# Add execution dir to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from monitor_companies_job import get_supabase
except ImportError:
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from execution.monitor_companies_job import get_supabase
    except ImportError:
        print("Could not import get_supabase")
        sys.exit(1)

load_dotenv()

def analyze_last_scans():
    print("🔍 Auditing Last 3 Scans...")
    
    supabase = get_supabase()
    
    # Fetch last 3 logs
    try:
        logs = supabase.table("monitor_scan_log") \
            .select("*") \
            .order("completed_at", desc=True) \
            .limit(3) \
            .execute()
    except Exception as e:
        print(f"⚠️ Error fetching logs: {e}")
        return

    if not logs.data:
        print("No logs found.")
        return

    print(f"Found {len(logs.data)} logs.\n")

    for i, log in enumerate(logs.data):
        print(f"=== SCAN {i+1}: {log.get('company_name')} ===")
        print(f"Time: {log.get('started_at')} -> {log.get('completed_at')}")
        print(f"Status: {log.get('status')}")
        if log.get('error'):
            print(f"❌ ERROR: {log.get('error')}")
        
        # Efficiency
        apify = log.get('apify_calls', 0)
        llm = log.get('llm_calls', 0)
        pages = log.get('pages_fetched', 0)
        print(f"Efficiency: Apify={apify}, LLM={llm}, Pages={pages}")
        
        # Triggers
        trigger_found = log.get('trigger_found')
        trigger_type = log.get('trigger_type')
        print(f"Result: Trigger Found? {trigger_found} ({trigger_type})")
        
        # Relevance / Analysis Log
        analysis_log = log.get('analysis_log') or []
        print(f"Analysis Log ({len(analysis_log)} items):")
        
        for item in analysis_log:
            title = item.get('title', '')[:50]
            decision = item.get('decision')
            conf = item.get('confidence')
            model = item.get('model')
            reasoning = item.get('reasoning', 'N/A')
            
            icon = "✅" if decision in ['triggered', 'pass'] else "❌"
            print(f"  {icon} [{model}] {decision.upper()} (Conf: {conf})")
            print(f"     Title: {title}...")
            if reasoning != 'N/A':
                print(f"     Reasoning: {reasoning[:100]}...")
        print("-" * 40)

if __name__ == "__main__":
    analyze_last_scans()
