import json
import requests
import time
import os

API_KEY = "0TJuykKKsoOQd8s5ac6Cj5ps"
URL = "https://api.anymailfinder.com/v5.1/find-email/person"

def enrich_leads():
    input_path = "pulsepoint_strategic/leads/enriched_contacts.json"
    output_path = "pulsepoint_strategic/leads/enriched_contacts_verified.json"
    
    with open(input_path, 'r') as f:
        contacts = json.load(f)
    
    verified_contacts = []
    
    print(f"Enriching {len(contacts)} contacts...")
    
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    for contact in contacts:
        # Determine domain (some might be full URLs)
        domain = contact.get("website", "").replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        # Fallback if website missing, try to infer from email
        if not domain and "@" in contact.get("email", ""):
            domain = contact["email"].split("@")[1]
            
        full_name = contact["contact_name"]
        
        print(f"Checking {full_name} @ {domain}...")
        
        payload = {
            "domain": domain,
            "full_name": full_name
        }
        
        try:
            resp = requests.post(URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid_email"):
                    print(f"  -> VALID: {data['valid_email']}")
                    contact["email"] = data["valid_email"]
                    contact["verification_status"] = "verified"
                else:
                    print("  -> No valid email found, keeping original.")
                    contact["verification_status"] = "unverified"
            else:
                print(f"  -> API Error {resp.status_code}: {resp.text}")
                contact["verification_status"] = "api_error"
                
        except Exception as e:
            print(f"  -> Exception: {e}")
            contact["verification_status"] = "script_error"
            
        verified_contacts.append(contact)
        # Be nice to the API
        time.sleep(0.5)

    with open(output_path, 'w') as f:
        json.dump(verified_contacts, f, indent=2)
        
    print(f"\nSaved verified contacts to {output_path}")

if __name__ == "__main__":
    enrich_leads()
