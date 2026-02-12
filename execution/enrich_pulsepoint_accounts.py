
import os
import time
import json
import requests
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient

load_dotenv()

# CONFIG
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
ANYMAILFINDER_KEY = os.environ.get("ANYMAILFINDER_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
apify = ApifyClient(APIFY_TOKEN)

def find_website(company_name):
    """Finds official website via Google Search."""
    print(f"  🔍 Finding website for: {company_name}")
    query = f"{company_name} official website -site:linkedin.com -site:facebook.com -site:instagram.com"
    run_input = {
        "queries": query,
        "resultsPerPage": 3,
        "maxPagesPerQuery": 1,
        "countryCode": "us"
    }
    try:
        run = apify.actor("apify/google-search-scraper").call(run_input=run_input)
        items = apify.dataset(run["defaultDatasetId"]).list_items().items
        if items:
            for page in items:
                for res in page.get("organicResults", []):
                    url = res.get("url")
                    if url:
                        # Simple domain extraction
                        domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
                        print(f"    -> Found Domain: {domain}")
                        return domain
    except Exception as e:
        print(f"    -> Error finding website: {e}")
    return None

def normalize_company(name: str) -> str:
    if not name:
        return ""
    import re
    # Remove common suffixes and prefixes
    clean = re.sub(r'\b(inc|llc|ltd|corp|corporation|co|company|group|agency|studios?|partners?|solutions?|enterprises?)\b', '', name.lower(), flags=re.IGNORECASE)
    # Remove special chars
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    return clean.strip()

def company_matches(profile_text: str, target: str) -> bool:
    if not profile_text or not target:
        return False
    import re
    
    norm_target = normalize_company(target)
    norm_profile = profile_text.lower()
    
    # 1. REJECT GENERIC NAMES
    if norm_target in ["home", "about", "contact", "index", "main", "page", "site", "search", "login", "signup"]:
        return False
        
    if len(norm_target) < 3:
        return False # Too short to be safe
        
    # 2. WORD BOUNDARY MATCH
    pattern = fr"\b{re.escape(norm_target)}\b"
    if re.search(pattern, norm_profile):
        return True
        
    return False

def find_decision_maker(company_name, domain):
    """Finds decision maker names via LinkedIn Google Search."""
    print(f"  🔍 Finding decision maker for: {company_name}")
    query = f'site:linkedin.com/in/ "{company_name}" (CEO OR Founder OR Principal OR "Managing Director" OR "CMO" OR "VP Marketing")'
    run_input = {
        "queries": query,
        "resultsPerPage": 3, # Get top 3 candidates
        "maxPagesPerQuery": 1,
        "countryCode": "us"
    }
    candidates = []
    try:
        run = apify.actor("apify/google-search-scraper").call(run_input=run_input)
        items = apify.dataset(run["defaultDatasetId"]).list_items().items
        if items:
            for page in items:
                for res in page.get("organicResults", []):
                    title = res.get("title", "")
                    
                    # STRICT MATCH CHECK
                    if not company_matches(title, company_name):
                        continue
                        
                    # Extract name from title "Name - Title - Company"
                    name_part = title.split(" - ")[0].split("|")[0].strip()
                    job_title = "Executive"
                    if " - " in title:
                        parts = title.split(" - ")
                        if len(parts) > 1:
                            job_title = parts[1]
                    
                    candidates.append({"name": name_part, "title": job_title, "linkedin": res.get("url")})
                    
        print(f"    -> Found {len(candidates)} candidates.")
        return candidates
    except Exception as e:
        print(f"    -> Error finding verification: {e}")
    return []

def verify_email(name, domain):
    """Verifies email via Anymailfinder."""
    url = "https://api.anymailfinder.com/v5.0/search/person.json"
    headers = {"Authorization": ANYMAILFINDER_KEY}
    payload = {"full_name": name, "domain": domain}
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        data = resp.json()
        return data.get("results", {}).get("email") # Returns email if valid/verified
    except Exception as e:
        print(f"    -> Email verify error: {e}")
    return None

def main():
    print("--- Starting Enrichment for PulsePoint Strategic ---")
    
    # Process ALL PulsePoint companies
    companies = supabase.table("triggered_companies")\
        .select("*")\
        .eq("client_context", "pulsepoint_strategic")\
        .execute().data
        
    print(f"Found {len(companies)} companies to process.")
    
    for comp in companies:
        if comp['company'].lower() in ["unknown", "branding studios", "not specified", "mid-sized marketing agencies"]:
            print(f"Skipping junk company: {comp['company']}")
            continue
            
        print(f"\nProcessing: {comp['company']} ({comp['id']})")
        
        domain = comp.get('website')
        
        # 1. Find Website if missing
        if not domain:
            domain = find_website(comp['company'])
            if domain:
                supabase.table("triggered_companies").update({"website": domain}).eq("id", comp['id']).execute()
        
        if domain:
            print(f"    Using Domain: {domain}")
            # 2. Check if we already have leads to save API credits
            existing_leads = supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").select("id", count="exact").eq("triggered_company_id", comp['id']).execute()
            if existing_leads.count > 0:
                 print("    -> Leads already exist. Skipping enrichment.")
                 continue

            # 3. Find People
            candidates = find_decision_maker(comp['company'], domain)
            
            for person in candidates:
                # 4. Verify Email
                email = verify_email(person['name'], domain)
                if email:
                    print(f"    ✅ VALID: {person['name']} <{email}>")
                    
                    # 5. Insert Lead
                    try:
                        supabase.table("PULSEPOINT_STRATEGIC_TRIGGERED_LEADS").insert({
                            "triggered_company_id": comp['id'],
                            "name": person['name'],
                            "title": person['title'],
                            "email": email,
                            "linkedin_url": person['linkedin'],
                            "contact_status": "pending"
                        }).execute()
                    except Exception as e:
                        print(f"    -> Insert error (duplicate?): {e}")
                else:
                    print(f"    ❌ No email for {person['name']}")
                    
        else:
            print("    -> Could not find website.")
            
if __name__ == "__main__":
    main()
