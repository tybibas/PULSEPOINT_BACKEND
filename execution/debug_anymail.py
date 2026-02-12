import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("ANYMAILFINDER_API_KEY")

def debug_search():
    url = "https://api.anymailfinder.com/v5.0/search/person.json"
    headers = {"Authorization": API_KEY}
    # Test with a known easy one
    payload = {"full_name": "Nicole LaFave", "domain": "designwomb.com"}
    
    print(f"Debug Search for: {payload}")
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response Headers:", response.headers)
        print("Raw Response:", response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_search()
