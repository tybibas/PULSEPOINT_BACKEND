import json
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = '.tmp/qualified_targets.json'
OUTPUT_FILE = '.tmp/targets_with_contacts.json'

def fetch_domain(company_name):
    # Quick helper to guess or fetch domain.
    # For MVP, we'll try a simple Clearbit Autocomplete free endpoint or similar, 
    # OR since we have the IR URL from step 2 (candidates_enriched.json), we SHOULD use that.
    # But qualified_targets.json might not have preserved the IR URL if we didn't pass it through.
    # Let's check 3_score_narrative.py ... it preserves candidate data.
    return None

def find_contacts(api_key, domain):
    print(f"Searching contacts for {domain}...")
    # AMF focuses on finding specific people. We'll try to guess "Head of Investor Relations"
    # Note: This is speculative without real names.
    url = "https://api.anymailfinder.com/v5.0/search/person.json"
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }
    
    contacts = []
    # Try a few generic IR roles
    roles_to_try = [
        {"first_name": "Head", "last_name": "of Investor Relations"},
        {"first_name": "Investor", "last_name": "Relations"},
        {"first_name": "CFO", "last_name": ""}
    ]
    
    for role in roles_to_try:
        data = {
            "domain": domain,
            "first_name": role["first_name"],
            "last_name": role["last_name"]
        }
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                contacts.append(response.json())
            else:
                # 404 just means not found usually
                pass
        except Exception as e:
            print(f"AMF Exception: {e}")
            
    return contacts if contacts else None

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"{INPUT_FILE} not found.")
        return

    amf_key = os.getenv("ANYMAILFINDER_API_KEY")
    # Quick fix: allow passing directly if not in env for testing (but it should be in env now)
    if not amf_key:
        print("ANYMAILFINDER_API_KEY not found in .env")
        return

    with open(INPUT_FILE, 'r') as f:
        targets = json.load(f)

    if not targets:
        print("No targets to process.")
        return

    # Load enriched data to get URLs (domains) since qualified_targets might not have it parsed
    # Actually, qualified_targets.json has whatever we preserved.
    # Let's assume we need to re-derive domain from 'IR_URL' if present, or Company Name.
    
    # Note: Step 3 (Score) preserved "candidate" dict, which HAD 'IR_URL'.
    
    enriched_targets = []
    
    for target in targets:
        company = target.get('Company')
        ir_url = target.get('IR_URL')
        domain = ""
        
        if ir_url:
            from urllib.parse import urlparse
            parsed = urlparse(ir_url)
            domain = parsed.netloc.replace("www.", "")
            # Clean up subdomain if it's ir.company.com -> company.com
            # Heuristic: mostly yes.
            parts = domain.split('.')
            if len(parts) > 2:
                domain = ".".join(parts[-2:])
        
        contacts = []
        if domain:
            result = find_contacts(amf_key, domain)
            if result:
                # dependent on AMF response structure
                # Assuming standard response
                contacts.append(result)
        
        target['Contacts'] = contacts
        enriched_targets.append(target)
        
        time.sleep(1)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_targets, f, indent=2)
    print(f"Saved {len(enriched_targets)} targets with contacts to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
