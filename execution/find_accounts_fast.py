"""
Script to find and enrich 600 high-fit accounts FAST.
ICP: Marketing Agencies, Dev Shops, Architecture Firms, B2B SaaS (US Only).
"""
import os
import re
import time
import random
import requests
import concurrent.futures
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient

load_dotenv('../.env')

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
APIFY_TOKEN = os.environ.get('APIFY_API_KEY')
ANYMAILFINDER_KEY = os.environ.get('ANYMAILFINDER_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
apify = ApifyClient(APIFY_TOKEN)

TARGET_COUNT = 600
MAX_WORKERS = 5

# Expanded Search Queries (City x Industry)
CITIES = ["New York", "San Francisco", "Austin", "Chicago", "Los Angeles", "Seattle", "Denver", "Boston", "Atlanta", "Miami", "Dallas", "Houston", "Portland", "Washington DC", "San Diego", "Nashville", "Philadelphia"]
INDUSTRIES = [
    "branding agencies", "digital marketing agencies", "software development shops", "mobile app development companies",
    "creative agencies", "boutique consultancies", "management consulting firms", "strategy consulting firms",
    "graphic design studios", "ux design agencies", "b2b pr firms", "video production agencies"
]

SEARCH_QUERIES = [f"top {ind} {city}" for city in CITIES for ind in INDUSTRIES]
random.shuffle(SEARCH_QUERIES)

JUNK_TERMS = ["clutch.co", "upcity.com", "designrush.com", "goodfirms.co", "yelp.com", "linkedin.com", "facebook.com", "instagram.com", "glassdoor.com", "zoominfo.com", "directory", "list", "top 10", "best", "rankings", "manifest", "agency spotter", "sortlist", "expertise.com"]

def verify_email_domain(company_name, domain):
    try:
        url = "https://api.anymailfinder.com/v5.0/search/company.json"
        
        resp = requests.post(
            url,
            headers={"Authorization": ANYMAILFINDER_KEY},
            json={"domain": domain},
            timeout=15
        )
        data = resp.json()
        
        if "results" in data and "emails" in data["results"]:
            emails = data["results"]["emails"]
            if emails:
                return [e for e in emails if "@" in e][:5] # Limit to top 5
        return None
    except Exception as e:
        print(f"Anymailfinder error for {domain}: {e}")
        return None

def process_single_company(company_data):
    company_name = company_data['company']
    domain = company_data['domain']
    
    # Check if exists in DB
    existing = supabase.table('triggered_companies').select('id').eq('website', domain).execute()
    if existing.data:
        print(f"  ⏭️  Skipping existing: {company_name}")
        return False

    print(f"    🔍 Rapid Enrichment for {company_name} ({domain})...")
    
    # ANYMAILFINDER DIRECT DOMAIN ENRICHMENT
    emails = verify_email_domain(company_name, domain)
    
    if emails:
        print(f"    ✅ Found {len(emails)} emails via Anymailfinder domain search")
        try:
            # 1. Add Company
            comp_data = {
                "company": company_name,
                "website": domain,
                "client_context": "pulsepoint_strategic",
                "monitoring_status": "active",
                "last_monitored_at": None
            }
            comp_resp = supabase.table("triggered_companies").insert(comp_data).execute()
            comp_id = comp_resp.data[0]['id']
            
            # 2. Add Contacts (Unknown Title)
            for email in emails:
                # Try to guess name from email (john.doe@...)
                name = email.split("@")[0].replace(".", " ").title()
                
                supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").insert({
                    "triggered_company_id": comp_id,
                    "name": name,
                    "title": "Contact (Role unconfirmed)", # Set explicit note
                    "email": email,
                    "linkedin_url": None,
                    "contact_status": "pending"
                }).execute()
                
            print(f"  🎉 ADDED: {company_name} with {len(emails)} contacts")
            return True
        except Exception as e:
            print(f"  ❌ DB Error: {e}")
            return False
            
    else:
        print(f"    ⚠️ No email found for domain {domain} - Skipping")
        return False

# ===== MAIN LOGIC =====

print("=" * 60)
print(f"FINDING {TARGET_COUNT} HIGH-FIT ACCOUNTS (FAST MODE)")
print("=" * 60)

# Pre-load existing domains
existing_companies = supabase.table('triggered_companies').select('website').execute().data
existing_domains = set(c.get('website') for c in existing_companies if c.get('website'))
print(f"Existing database matches: {len(existing_domains)}")

added_count = 0
processed_domains = set()

# Process queries
for query in SEARCH_QUERIES:
    if added_count >= TARGET_COUNT: break
    
    print(f"\n📡 Google Search: {query}")
    potential_companies = []
    
    try:
        run = apify.actor("apify/google-search-scraper").call(run_input={
            "queries": query, "resultsPerPage": 25, "maxPagesPerQuery": 1, "countryCode": "us"
        })
        items = apify.dataset(run["defaultDatasetId"]).list_items().items
        
        for page in items:
            for res in page.get("organicResults", []):
                title = res.get("title", "")
                url = res.get("url", "")
                
                # Filter junk
                if any(term in url.lower() for term in JUNK_TERMS): continue
                if any(term in title.lower() for term in JUNK_TERMS): continue
                if re.search(r'\btop \d+', title.lower()): continue # "Top 10", "Top 20" etc.
                if re.search(r'\best \d+', title.lower()): continue # "Best 10" etc.
                
                from urllib.parse import urlparse
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.replace("www.", "")
                    
                    if not domain or len(domain) < 4: continue
                    if ".gov" in domain or ".edu" in domain: continue
                    if domain in existing_domains or domain in processed_domains: continue
                    
                    company_name = title.split(" - ")[0].split("|")[0].split(":")[0].strip()
                    company_name = re.sub(r'\.\.\.$', '', company_name).strip()
                    
                    if len(company_name) > 3:
                        if len(company_name.split()) > 6: continue # Filter long junk titles
                        processed_domains.add(domain)
                        potential_companies.append({"company": company_name, "domain": domain})
                        
                except: continue
        
        print(f"  Found {len(potential_companies)} potential companies. Enriching in parallel...")
        
        # Parallel Enrichment
        if potential_companies:
            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                results = list(executor.map(process_single_company, potential_companies))
                
            new_adds = sum(1 for r in results if r)
            added_count += new_adds
            print(f"  --> Added {new_adds} accounts from this batch. Total: {added_count}/{TARGET_COUNT}")
            
    except Exception as e:
        print(f"Search error: {e}")
        
    time.sleep(1)

print(f"\nDONE! Added {added_count} new accounts.")
