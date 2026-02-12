import requests
import os
import json

API_KEY = "0TJuykKKsoOQd8s5ac6Cj5ps"

def test_endpoints():
    domain = "flagright.com"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # 1. Confirmed Person Search (v5.1)
    print("Testing v5.1 Person Search...")
    url_person = "https://api.anymailfinder.com/v5.1/find-email/person"
    payload_person = {"domain": domain, "full_name": "Baran Ozkan"}
    
    try:
        resp = requests.post(url_person, json=payload_person, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
    except Exception as e:
        print(f"Failed: {e}")

    # 2. Hypothesis: Company People Search (v4.1)
    print("\nTesting v4.1 Company People Search...")
    url_domain = "https://api.anymailfinder.com/v4.1/search/company_people.json"
    payload_domain = {"domain": domain}
    
    try:
        resp = requests.post(url_domain, json=payload_domain, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text[:500]}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    test_endpoints()
