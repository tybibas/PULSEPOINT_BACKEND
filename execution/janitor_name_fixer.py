"""
Janitor script to fix generic company names in Supabase (e.g. "Home", "Index").
Runs in a loop to correct bad data from the scraper without interrupting it.
"""
import os
import time
import requests
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

load_dotenv('../.env')

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BAD_NAMES = ["Home", "Index", "Welcome", "About", "Contact", "Portland", "Seattle", "Austin", "New York", "San Francisco", "Chicago", "Los Angeles", "Boston", "Miami", "Denver"]

def get_better_name(url):
    try:
        # Try to get title from page
        if not url.startswith('http'):
            url = 'https://' + url
            
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            title = soup.title.string.strip() if soup.title else ""
            
            # Remove "Home" from title
            title = re.sub(r'^\s*Home\s*[-|]\s*', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\s*[-|]\s*Home\s*$', '', title, flags=re.IGNORECASE)
            
            # Split by common separators
            parts = re.split(r'\s*[-|]\s*', title)
            
            # Pick the longest part that isn't generic? No, pick the first non-generic part.
            for part in parts:
                if part.strip() not in BAD_NAMES and len(part.strip()) > 3:
                    return part.strip()
                    
    except Exception as e:
        print(f"Error fetching {url}: {e}")

    # Fallback: Use Domain Name
    try:
        domain = urlparse(url).netloc
        if not domain: domain = url
        domain = domain.replace("www.", "").split(".")[0]
        return domain.replace("-", " ").title()
    except:
        return "Unknown Company"

def run_janitor():
    print("🧹 Janitor started. Monitoring for bad names...")
    while True:
        try:
            # Check for bad names
            for bad_name in BAD_NAMES:
                res = supabase.table('triggered_companies').select('id, company, website').eq('company', bad_name).execute()
                
                for comp in res.data:
                    old_name = comp['company']
                    url = comp['website']
                    print(f"  Found bad name: {old_name} ({url})")
                    
                    new_name = get_better_name(url)
                    
                    if new_name and new_name != old_name:
                        print(f"  ✨ Fixing: {old_name} -> {new_name}")
                        supabase.table('triggered_companies').update({'company': new_name}).eq('id', comp['id']).execute()
                    else:
                        print(f"  ⚠️ Could not fix: {old_name}")
                        
            time.sleep(10) # Run every 10 seconds
            
        except Exception as e:
            print(f"Janitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    run_janitor()
