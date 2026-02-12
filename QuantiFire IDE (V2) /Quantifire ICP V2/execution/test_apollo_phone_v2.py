
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("APOLLO_API_KEY")

if not api_key:
    # Just in case the previous run failed because of this (unlikely given the 403)
    pass
else:
    # Try the main people search endpoint
    url = "https://api.apollo.io/v1/people/search"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key
    }
    
    data = {
        "q_organization_domains": "google.com",
        "person_titles": ["software engineer"],
        "page": 1,
        "per_page": 1
    }
    
    try:
        print(f"Testing {url} ...")
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            print("Success!")
            res_json = resp.json()
            people = res_json.get('people', [])
            if people:
                p = people[0]
                if 'phone_numbers' in p:
                    print("Phone numbers:", p['phone_numbers'])
                else:
                    print("No 'phone_numbers' field found directly.")
            else:
                print("No people found.")
        else:
            print(f"Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Exception: {e}")
