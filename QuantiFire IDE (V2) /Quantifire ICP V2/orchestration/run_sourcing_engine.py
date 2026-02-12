import os
import sys

def run_step(script_name):
    print(f"\n--- Running {script_name} ---")
    ret = os.system(f"python3 execution/{script_name}")
    if ret != 0:
        print(f"Error running {script_name}. Aborting.")
        sys.exit(1)

def main():
    print("Starting Just-in-Time Lead Sourcing Engine...")
    
    # 1. Update master list
    # We might skip this if the list is recent, but for now we always run it.
    # 1. Update master list
    # We might skip this if the list is recent, but for now we always run it.
    run_step("fetch_ftse_constituents.py")
    
    # 2. Fetch DAX Universe
    run_step("fetch_dax_constituents.py")
    
    # 3. Check events
    run_step("check_company_events.py")
    
    # 3. Enrich
    run_step("enrich_lead.py")
    
    # 4. Sync to Google Sheets
    run_step("sync_to_gsheet.py")
    
    print("\n--- Workflow Complete ---")
    print("Check dashboard_queue.json and your Google Sheet for results.")

if __name__ == "__main__":
    main()
