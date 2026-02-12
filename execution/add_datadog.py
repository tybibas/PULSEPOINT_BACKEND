import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
URL = "https://api.anymailfinder.com/v5.1/find-email/person"

datadog_lead = {
    "name": "Datadog",
    "event_type": "TRIGGER_DETECTED",
    "event_title": "Hiring Sales Development Representative",
    "event_context": "Trigger detected: Hiring Sales Development Representative",
    "event_source_url": "https://careers.datadoghq.com/",
    "contacts": [
        {
            "name": "Olivier Pomel",
            "title": "CEO",
            "email": "" # To be filled
        }
    ]
}

def enrich_and_add():
    # 1. Enrich
    domain = "datadoghq.com"
    full_name = "Olivier Pomel"
    payload = {"domain": domain, "full_name": full_name}
    headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}
    
    print(f"Enriching {full_name} @ {domain}...")
    email = "olivier@datadoghq.com" # Default guess
    try:
        resp = requests.post(URL, json=payload, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("valid_email"):
                print(f"  -> FOUND: {data['valid_email']}")
                email = data['valid_email']
            else:
                print("  -> Not found by API, using backup.")
        else:
            print(f"API Error {resp.status_code}")
    except Exception as e:
        print(f"Exception: {e}")

    datadog_lead["contacts"][0]["email"] = email
    
    # 2. Add to leads.json
    leads_path = "pulsepoint_strategic/leads/leads.json"
    with open(leads_path, "r") as f:
        data = json.load(f)
        
    # Check if mostly redundant
    names = [c["name"] for c in data["companies"]]
    if "Datadog" not in names:
        data["companies"].append(datadog_lead)
        print("Added Datadog to leads.json")
    else:
        print("Datadog already exists.")
        
    with open(leads_path, "w") as f:
        json.dump(data, f, indent=2)

    # 3. Add to enriched_contacts.json
    contacts_path = "pulsepoint_strategic/leads/enriched_contacts.json"
    with open(contacts_path, "r") as f:
        contacts = json.load(f)
        
    contacts.append({
        "company": "Datadog",
        "contact_name": "Olivier Pomel",
        "title": "CEO",
        "email": email,
        "website": "https://careers.datadoghq.com/",
        "verification_status": "verified"
    })
    
    with open(contacts_path, "w") as f:
        json.dump(contacts, f, indent=2)
    print("Updated enriched_contacts.json")

if __name__ == "__main__":
    enrich_and_add()
