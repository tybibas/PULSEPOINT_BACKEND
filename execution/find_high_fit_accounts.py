"""
Script to find and enrich 600 high-fit accounts for PulsePoint Strategic.
ICP: Marketing Agencies, Dev Shops, Architecture Firms, B2B SaaS (US Only).
OPTIMIZED: Uses parallel processing for faster enrichment.
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
MAX_WORKERS = 8  # Number of parallel enrichment threads

# Expanded Search Queries (City x Industry)
CITIES = ["New York", "San Francisco", "Austin", "Chicago", "Los Angeles", "Seattle", "Denver", "Boston", "Atlanta", "Miami", "Dallas", "Houston", "Portland", "Washington DC", "San Diego", "Nashville", "Philadelphia"]
INDUSTRIES = [
    "branding agencies", "digital marketing agencies", "software development shops", "mobile app development companies",
    "creative agencies", "boutique consultancies", "management consulting firms", "strategy consulting firms",
    "graphic design studios", "ux design agencies", "b2b pr firms", "video production agencies"
]

SEARCH_QUERIES = [f"top {ind} {city}" for city in CITIES for ind in INDUSTRIES]
random.shuffle(SEARCH_QUERIES)

# JUNK FILTERS
JUNK_TERMS = ["clutch.co", "upcity.com", "designrush.com", "goodfirms.co", "yelp.com", "linkedin.com", "facebook.com", "instagram.com", "glassdoor.com", "zoominfo.com", "directory", "list", "top 10", "best", "rankings", "manifest", "agency spotter", "sortlist", "expertise.com"]

# ===== HELPER FUNCTIONS =====

def is_valid_full_name(name: str) -> bool:
    if not name or len(name) < 5: return False
    parts = name.strip().split()
    if len(parts) < 2: return False
    return not bool(re.search(r'\d', name))

def normalize_company(name: str) -> str:
    if not name: return ""
    return re.sub(r'\b(inc|llc|ltd|corp|co|company|group|agency|studios?)\b', '', name.lower()).strip()

def company_matches(profile_text: str, target: str) -> bool:
    if not profile_text or not target: return False
    return normalize_company(target) in profile_text.lower()

def verify_email(name: str, domain: str) -> str:
    try:
        resp = requests.post(
            "https://api.anymailfinder.com/v5.0/search/person.json",
            headers={"Authorization": ANYMAILFINDER_KEY},
            json={"full_name": name, "domain": domain},
            timeout=15
        )
        return resp.json().get("results", {}).get("email")
    except:
        return None

def process_single_company(company_data):
    """
    Enriches and adds a single company.
    Returns True if added, False otherwise.
    """
    company_name = company_data['company']
    domain = company_data['domain']
    
    # Check if exists in DB (double check to avoid race conditions)
    existing = supabase.table('triggered_companies').select('id').eq('website', domain).execute()
    if existing.data:
        print(f"  ⏭️  Skipping existing: {company_name}")
        return False

    print(f"    🔍 Searching executives for {company_name} ({domain})...")
    query = f'site:linkedin.com/in/ "{company_name}" (CEO OR Founder OR "Managing Director" OR Principal OR Owner OR CMO OR "VP Marketing")'
    candidates = []
    
    try:
        run = apify.actor("apify/google-search-scraper").call(run_input={
            "queries": query, "resultsPerPage": 5, "maxPagesPerQuery": 1, "countryCode": "us"
        })
        items = apify.dataset(run["defaultDatasetId"]).list_items().items
        
        seen_names = set()
        
        for page in items:
            for res in page.get("organicResults", []):
                title = res.get("title", "")
                url = res.get("url", "")
                
                if "linkedin.com/in/" not in url: continue
                if not company_matches(title, company_name): continue
                
                name_parts = title.split(" - ")[0].split("|")[0].split("–")[0].strip()
                if not is_valid_full_name(name_parts): continue
                
                name_lower = name_parts.lower()
                if name_lower in seen_names: continue
                seen_names.add(name_lower)
                
                job_title = "Executive"
                if " - " in title:
                    parts = title.split(" - ")
                    if len(parts) > 1: job_title = parts[1].split("|")[0].strip()[:100]
                
                # VERIFY EMAIL IMMEDIATELY
                email = verify_email(name_parts, domain)
                if email:
                    print(f"    ✅ Verified: {name_parts} <{email}>")
                    candidates.append({
                        "name": name_parts,
                        "title": job_title,
                        "email": email,
                        "linkedin": url
                    })
                
                if len(candidates) >= 2: break # Stop after 2 verified contacts to save time
            if len(candidates) >= 2: break
            
        if candidates:
            # ADD TO SUPABASE
            try:
                comp_data = {
                    "company": company_name,
                    "website": domain,
                    "client_context": "pulsepoint_strategic",
                    "monitoring_status": "active",
                    "last_monitored_at": None
                }
                comp_resp = supabase.table("triggered_companies").insert(comp_data).execute()
                comp_id = comp_resp.data[0]['id']
                
                for contact in candidates:
                    supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").insert({
                        "triggered_company_id": comp_id,
                        "name": contact['name'],
                        "title": contact['title'],
                        "email": contact['email'],
                        "linkedin_url": contact['linkedin'],
                        "contact_status": "pending"
                    }).execute()
                    
                print(f"  🎉 ADDED: {company_name} with {len(candidates)} contacts")
                return True
            except Exception as e:
                print(f"  ❌ DB Error: {e}")
                return False
        else:
            print(f"    ⚠️ No verified contacts for {company_name}")
            return False
            
    except Exception as e:
        print(f"    ⚠️ Search error for {company_name}: {e}")
        return False

# ===== MAIN LOGIC =====

print("=" * 60)
print(f"FINDING {TARGET_COUNT} HIGH-FIT ACCOUNTS (Parallel Mode)")
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
                
                from urllib.parse import urlparse
                try:
                    parsed = urlparse(url)
                    domain = parsed.netloc.replace("www.", "")
                    
                    if not domain or len(domain) < 4: continue
                    if ".gov" in domain or ".edu" in domain: continue
                    if domain in existing_domains or domain in processed_domains: continue
                    
                    company_name = title.split(" - ")[0].split("|")[0].split(":")[0].strip()
                    company_name = re.sub(r'\.\.\.$', '', company_name).strip()
                    
                    # Enhanced Junk Filter
                    if len(company_name) > 3:
                        if len(company_name.split()) > 6: continue # Filter long titles
                        if re.search(r'\btop \d+', company_name.lower()): continue
                        if re.search(r'\best \d+', company_name.lower()): continue
                        
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
