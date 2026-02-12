
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("APOLLO_API_KEY")

if not api_key:
    print("No APOLLO_API_KEY found in .env")
    print("Please ensure you have an APOLLO_API_KEY in your .env file.")
else:
    url = "https://api.apollo.io/v1/mixed_people/search"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key
    }
    
    # Search for a common role at a known company to inspect response
    data = {
        "q_organization_domains": "google.com",
        "person_titles": ["software engineer"],
        "page": 1,
        "per_page": 1
    }
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            res_json = resp.json()
            people = res_json.get('people', [])
            if people:
                p = people[0]
                print("Found person keys:", p.keys())
                if 'phone_numbers' in p:
                    print("Phone numbers:", p['phone_numbers'])
                else:
                    print("No 'phone_numbers' field found directly.")
                    
                # Check for other potential fields
                print("Full person object (truncated):")
                print(str(p)[:500])
            else:
                print("No people found.")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")
