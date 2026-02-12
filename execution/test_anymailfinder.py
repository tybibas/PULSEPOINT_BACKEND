import requests
import os
import sys

from dotenv import load_dotenv
load_dotenv('../.env')
API_KEY = os.environ.get('ANYMAILFINDER_API_KEY')

def test_domain_search():
    # Try to find contacts for a known domain
    domain = "flagright.com"
    headers = {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    # Attempt 1: Standard Person Search (verify we can find the CEO)
    print(f"Testing Person Search for {domain}...")
    url_person = "https://api.anymailfinder.com/v5.0/search/person.json"
    payload_person = {"domain": domain, "name": "Baran Ozkan"}
    
    try:
        resp = requests.post(url_person, json=payload_person, headers=headers)
        print(f"Person Search Status: {resp.status_code}")
        print(f"Person Search Response: {resp.text[:500]}")
    except Exception as e:
        print(f"Person Search Failed: {e}")

    # Attempt 3: Company Search (v5.0 and v5.1)
    print(f"\nTesting Company Search for {domain}...")
    
    # Try v5.0 search/company.json (common structure)
    endpoints = [
        "https://api.anymailfinder.com/v5.0/search/company.json",
        "https://api.anymailfinder.com/v5.1/find-email/company"
    ]
    
    for url in endpoints:
        print(f"  Trying {url}...")
        try:
            # According to docs, usually takes 'domain' or 'company_name'
            payload = {"domain": domain}
            resp = requests.post(url, json=payload, headers=headers)
            print(f"  Status: {resp.status_code}")
            print(f"  Response: {resp.text[:500]}")
        except Exception as e:
            print(f"  Failed: {e}")

if __name__ == "__main__":
    test_domain_search()
