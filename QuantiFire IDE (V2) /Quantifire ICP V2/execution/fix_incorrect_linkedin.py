import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import unicodedata

# Add root path to find local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.enrich_lead import find_linkedin_url

QUEUE_FILE = "dashboard_queue.json"

def normalize_slug(text):
    if not text: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn').lower().replace(" ", "-")

def fix_linkedin_profiles():
    if not os.path.exists(QUEUE_FILE):
        print("No dashboard_queue.json found.")
        return

    with open(QUEUE_FILE, 'r') as f:
        queue = json.load(f)

    # Filter for DAX items that have contacts
    items_to_process = [
        item for item in queue 
        if item.get('index_name') == "DAX" and item.get('contacts')
    ]

    print(f"Checking {len(items_to_process)} DAX items for bad LinkedIn profiles...")

    contacts_to_fix = []
    
    for item in items_to_process:
        company = item.get('company')
        for contact in item.get('contacts', []):
            name = contact.get('name', '')
            url = contact.get('linkedin', '')
            
            if not url or "linkedin.com" not in url:
                continue
                
            # Heuristic check: Does URL contain the name?
            # e.g. name="Anna Dimitrova", url=".../julia-hoppe..."
            
            # Simple check: last name must be in the URL slug
            parts = name.lower().split()
            last_name = parts[-1] if parts else ""
            
            # Remove query params for check
            clean_url = url.split("?")[0].lower()
            
            # Normalized check (remove accents)
            norm_last = normalize_slug(last_name)
            
            if norm_last and norm_last not in clean_url:
                print(f"  [Suspect] {name} ({company}) -> {url}")
                contacts_to_fix.append({
                    "company": company,
                    "contact": contact,
                    "reason": "Name mismatch"
                })
            else:
                # pass
                pass

    print(f"Found {len(contacts_to_fix)} suspect profiles to re-check.")

    if not contacts_to_fix:
        print("No suspect profiles found.")
        return

    # Use ThreadPool to speed up searching
    def process_fix(info):
        comp = info['company']
        cont = info['contact']
        name = cont.get('name')
        
        print(f"  Re-searching for {name} at {comp}...")
        new_url = find_linkedin_url(name, comp)
        
        if new_url:
            if new_url != cont.get('linkedin'):
                print(f"    [FIXED] {name}: {cont.get('linkedin')} -> {new_url}")
                cont['linkedin'] = new_url
                return True
            else:
                print(f"    [SAME] {name}: Still found {new_url}")
                return False
        else:
            print(f"    [REMOVED] {name}: Could not find valid profile. removing bad link.")
            cont['linkedin'] = "" # Clear bad link
            return True

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(process_fix, info) for info in contacts_to_fix]
        
        fixed_count = 0
        for future in as_completed(futures):
            try:
                if future.result():
                    fixed_count += 1
            except Exception as e:
                print(f"Error in future: {e}")

    print(f"Fix complete. Updated {fixed_count} profiles.")

    # Save the updated queue
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)
    print("Updated dashboard_queue.json")
    
    # Sync
    from execution.sync_to_gsheet import sync_to_sheet
    sync_to_sheet()

if __name__ == "__main__":
    fix_linkedin_profiles()
