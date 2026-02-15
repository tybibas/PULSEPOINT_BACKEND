
import sys
import os
# Add execution dir to path
sys.path.append(os.path.join(os.getcwd(), "execution"))

from monitor_companies_job import get_supabase
from dotenv import load_dotenv

load_dotenv()

def run():
    supabase = get_supabase()
    logs = supabase.table("monitor_scan_log").select("analysis_log").limit(10).order("completed_at", desc=True).execute()
    
    found = False
    for row in logs.data:
        if row.get('analysis_log'):
            import json
            print(json.dumps(row['analysis_log'], indent=2))
            found = True
            break
    
    if not found:
        print("No analysis log found in last 10 scans.")

if __name__ == "__main__":
    run()
