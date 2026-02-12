import json
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
URL = "https://api.anymailfinder.com/v5.1/find-email/person"

def enrich():
    with open("pulsepoint_strategic/leads/replacement_leads_v2.json", "r") as f:
        contacts = json.load(f)

    for contact in contacts:
        # Clean domain
        domain = contact["website"].replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        # For skanska, try both usa.skanska.com and skanska.com if needed, but start with provided
        
        payload = {"domain": domain, "full_name": contact["contact_name"]}
        headers = {"X-Api-Key": API_KEY, "Content-Type": "application/json"}
        
        print(f"Checking {contact['contact_name']} @ {domain}...")
        try:
            resp = requests.post(URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid_email"):
                    print(f"  -> FOUND: {data['valid_email']}")
                    contact["email"] = data["valid_email"]
                else:
                    print("  -> Not found")
            else:
                 print(f"Error: {resp.status_code}")
        except Exception as e:
            print(f"Exception: {e}")
        time.sleep(1)

    with open("pulsepoint_strategic/leads/replacement_leads_v2_verified.json", "w") as f:
        json.dump(contacts, f, indent=2)

if __name__ == "__main__":
    enrich()
