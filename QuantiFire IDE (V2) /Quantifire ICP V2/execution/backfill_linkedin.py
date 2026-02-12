import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add root path to find local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the search function from enrich_lead
from execution.enrich_lead import find_linkedin_url, normalize_name

QUEUE_FILE = "dashboard_queue.json"

def backfill_linkedin():
    if not os.path.exists(QUEUE_FILE):
        print("No dashboard_queue.json found.")
        return

    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)

    # Filter for DAX items that have contacts
    # User asked for "DAX Triggered Tab", so we prioritize items with index_name="DAX"
    # But for robustness, we can do all. Let's start with DAX as requested.
    items_to_process = [
        item for item in queue 
        if item.get('index_name') == "DAX" and item.get('contacts')
    ]

    print(f"Found {len(items_to_process)} DAX items to check for LinkedIn profiles.")

    # We need to process contacts that don't have a 'linkedin' key or it is empty
    contacts_to_enrich = []
    
    for item in items_to_process:
        company = item.get('company')
        for contact in item.get('contacts', []):
            if not contact.get('linkedin'):
                contacts_to_enrich.append({
                    "company": company,
                    "contact": contact
                })

    print(f"Found {len(contacts_to_enrich)} contacts missing LinkedIn profiles.")

    if not contacts_to_enrich:
        print("No contacts need backfilling.")
        return

    # Use ThreadPool to speed up searching
    # Helper function for the thread
    def process_contact_wrapper(info):
        comp = info['company']
        cont = info['contact']
        name = cont.get('name')
        
        url = find_linkedin_url(name, comp)
        if url:
            cont['linkedin'] = url
            print(f"  [Found] {name} ({comp}) -> {url}")
            return True
        else:
            print(f"  [Not Found] {name} ({comp})")
            return False

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_contact_wrapper, info) for info in contacts_to_enrich]
        
        found_count = 0
        for future in as_completed(futures):
            if future.result():
                found_count += 1

    print(f"Backfill complete. Found {found_count} new LinkedIn profiles.")

    # Save the updated queue
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)
    print("Updated dashboard_queue.json")

    print("Syncing to Google Sheets...")
    # Import here to avoid circular imports or early execution
    from execution.sync_to_gsheet import sync_to_sheet
    sync_to_sheet()

if __name__ == "__main__":
    backfill_linkedin()
