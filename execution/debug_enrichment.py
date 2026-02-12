
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
ANYMAILFINDER_KEY = os.environ.get("ANYMAILFINDER_API_KEY")

def debug_anymail():
    print(f"Key: {ANYMAILFINDER_KEY[:5]}...")
    
    # Test 1: Known valid email (e.g. Elon Musk at Tesla or someone public)
    # Using a generic specific example: "Satya Nadella" at "microsoft.com"
    print("\n--- Test 1: Known Target (Satya Nadella @ microsoft.com) ---")
    url = "https://api.anymailfinder.com/v5.0/search/person.json"
    headers = {"Authorization": ANYMAILFINDER_KEY}
    payload = {"full_name": "Satya Nadella", "domain": "microsoft.com"}
    
    try:
        resp = requests.post(url, headers=headers, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: One of our actual targets that failed
    # Kyle York @ york.ie
    print("\n--- Test 2: Actual Target (Kyle York @ york.ie) ---")
    payload = {"full_name": "Kyle York", "domain": "york.ie"}
    try:
        resp = requests.post(url, headers=headers, json=payload)
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_anymail()
