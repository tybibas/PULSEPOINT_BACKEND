import json
import os
import requests
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from apify_client import ApifyClient
from openai import OpenAI
from dotenv import load_dotenv
import unicodedata

# Add root path to find local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from templates.prompts import get_trigger_type, generate_hook_prompt, assemble_email
from execution.sync_to_gsheet import sync_to_sheet

load_dotenv()

# Inputs
INPUT_FILE = "active_triggers.json"
OUTPUT_FILE = "dashboard_queue.json"

# Config
APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")
AMF_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def normalize_name(name):
    """Normalize name for deduplication (remove accents, lowercase)."""
    if not name: return ""
    return ''.join(c for c in unicodedata.normalize('NFD', name)
                  if unicodedata.category(c) != 'Mn').lower().strip()

def get_company_domain(company_name):
    """Uses Apify Google Search to find the first result for the company name."""
    if not APIFY_TOKEN: return None
    client = ApifyClient(APIFY_TOKEN)
    try:
        run = client.actor("apify/google-search-scraper").call(run_input={
            "queries": f"{company_name} official site", 
            "maxPagesPerQuery": 1, 
            "resultsPerPage": 1
        })
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        if items and items[0].get("organicResults"):
            return items[0]["organicResults"][0]["url"]
    except Exception as e:
        print(f"Error finding domain for {company_name}: {e}")
    return None

def find_officer_name(company, role):
    """Search for the current name of a specific officer."""
    if not APIFY_TOKEN: return None
    client = ApifyClient(APIFY_TOKEN)
    try:
        run = client.actor("apify/google-search-scraper").call(run_input={
            "queries": f"current {role} of {company} name", 
            "maxPagesPerQuery": 1, 
            "resultsPerPage": 3
        })
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        
        snippets = []
        if items and items[0].get("organicResults"):
            for res in items[0]["organicResults"][:3]:
                snippets.append(res.get("title", "") + ": " + res.get("description", ""))
        
        if not snippets or not OPENAI_API_KEY: return None
        
        client_ai = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"""
        Extract the full name of the current {role} of {company} from these snippets.
        Snippets: {json.dumps(snippets)}
        Return ONLY the full name. If not found, return "Not Found". Ignore "Dr.", "Prof.".
        """
        resp = client_ai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        name = resp.choices[0].message.content.strip()
        if "not found" in name.lower(): return None
        return name.replace("Dr. ", "").replace("Prof. ", "").strip()
    except Exception as e:
        print(f"Error finding {role} for {company}: {e}")
    return None

def find_verified_email(name, domain):
    """Uses Anymailfinder to find a verified email."""
    if not AMF_API_KEY or not name or not domain: return None
    try:
        resp = requests.post(
            "https://api.anymailfinder.com/v5.0/search/person.json",
            headers={"Authorization": AMF_API_KEY, "Content-Type": "application/json"},
            json={"full_name": name, "domain": domain}
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success'):
                res = data.get('results', {})
                if res.get('validation') == 'valid' or res.get('email_class') == 'verified':
                    return res.get('email')
    except Exception as e:
        print(f"Error verifying email for {name}: {e}")
    except Exception as e:
        print(f"Error verifying email for {name}: {e}")
    return None

def find_linkedin_url(name, company):
    """
    Search for the LinkedIn profile of a person at a company.
    Validates that the name appears in the search result title.
    """
    if not APIFY_TOKEN or not name: return None
    
    client = ApifyClient(APIFY_TOKEN)
    
    def validate_result(item, target_name):
        """Check if target name parts are in the title"""
        title = item.get("title", "").lower()
        # simplified check: at least the last name and first char of first name
        parts = target_name.lower().split()
        if not parts: return False
        
        # Check last name is in title
        if parts[-1] not in title:
            return False
            
        # Check first name or initial is in title
        if parts[0] not in title:
            return False
            
        return True

    # Attempt 1: Strict Search
    try:
        query = f"site:linkedin.com/in/ \"{name}\" \"{company}\""
        print(f"    [LinkedIn] Searching: {query}")
        run = client.actor("apify/google-search-scraper").call(run_input={
            "queries": query, 
            "maxPagesPerQuery": 1, 
            "resultsPerPage": 3
        })
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        if items and items[0].get("organicResults"):
            for res in items[0]["organicResults"]:
                if validate_result(res, name):
                    return res["url"]
                else:
                    print(f"    [LinkedIn] Skipped mismatch: {res.get('title')} vs {name}")
    except Exception as e:
        print(f"Error finding LinkedIn (Strict) for {name}: {e}")

    # Attempt 2: Broader Search (if strict failed)
    try:
        query = f"site:linkedin.com/in/ {name} {company}"
        print(f"    [LinkedIn] Retry Broad: {query}")
        run = client.actor("apify/google-search-scraper").call(run_input={
            "queries": query, 
            "maxPagesPerQuery": 1, 
            "resultsPerPage": 3
        })
        items = client.dataset(run["defaultDatasetId"]).list_items().items
        if items and items[0].get("organicResults"):
            for res in items[0]["organicResults"]:
                if validate_result(res, name):
                    return res["url"]
    except Exception as e:
        print(f"Error finding LinkedIn (Broad) for {name}: {e}")

    return None

def find_contact_via_apollo(domain, role_title, name=None):
    """
    Fallback: Search Apollo.io for a person with this role at this domain.
    Requires APOLLO_API_KEY in env.
    Returns dict {name, role, email, phone_numbers} or None.
    STRICT FILTERING: Must have 'contact_email_status' == 'verified'.
    """
    api_key = os.getenv("APOLLO_API_KEY")
    if not api_key: return None
    
    url = "https://api.apollo.io/v1/mixed_people/search"
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key
    }
    
    data = {
        "q_organization_domains": domain,
        "person_titles": [role_title],
        "page": 1,
        "per_page": 1,
        "contact_email_status": ["verified"] # STRICT FILTERING
    }
    
    if name:
        data["q_keywords"] = name
    
    try:
        resp = requests.post(url, headers=headers, json=data)
        if resp.status_code == 200:
            res_json = resp.json()
            people = res_json.get('people', [])
            if people:
                p = people[0]
                # Double check email status just in case (API usually filters, but safety first)
                if p.get('email_status') == 'verified' and p.get('email'):
                    # Extract phone numbers
                    phones = []
                    for ph in p.get('phone_numbers', []):
                         raw = ph.get('sanitized_number') or ph.get('raw_number')
                         p_type = ph.get('type')
                         if raw:
                             phones.append(f"{raw} ({p_type})")

                    return {
                        "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                        "role": p.get('title', role_title), # Use actual title from Apollo
                        "email": p.get('email'),
                        "phone_numbers": phones,
                        "linkedin": p.get('linkedin_url') or p.get('person_linkedin_url') or ""
                    }
    except Exception as e:
        print(f"    [Apollo Error] {e}")
        
    return None

def get_performance_data(ticker, universe_data):
    for c in universe_data:
        if c.get("ticker") == ticker:
            change = c.get("fifty_two_week_change", 0) or 0
            return f"{change*100:+.1f}% (52-wk)"
    return "N/A"

def generate_hook(company, event, contact_name, performance_str, sender_name="Your Name"):
    """
    HYBRID EMAIL ENGINE: Generate dynamic hook + static body.
    
    1. Detect trigger type from event
    2. Generate ONLY the opening hook sentence via OpenAI
    3. Assemble with static body template
    4. Return complete email draft
    """
    if not OPENAI_API_KEY: 
        return "Error: No OpenAI Key"
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Extract event details
    event_type = event.get('event_type') if isinstance(event, dict) else "Update"
    event_title = event.get('title') if isinstance(event, dict) else "Recent News"
    event_date = event.get('detected_at', "").split("T")[0] if isinstance(event, dict) else None
    event_description = event.get('description', "") if isinstance(event, dict) else ""
    
    # Step 1: Detect trigger type
    trigger_type = get_trigger_type(event_type, performance_str)
    print(f"    [Hook Engine] Trigger Type: {trigger_type}")
    
    # Step 2: Get the appropriate meta-prompt
    # Determine role if leadership trigger
    role = None
    if trigger_type == "LEADERSHIP":
        if "cfo" in event_type.lower():
            role = "Chief Financial Officer"
        elif "head of ir" in event_type.lower() or "investor relations" in event_type.lower():
            role = "Head of Investor Relations"
        else:
            role = "CFO"  # Default
    
    meta_prompt = generate_hook_prompt(
        trigger_type=trigger_type,
        contact_name=contact_name,
        company_name=company,
        event_date=event_date,
        role=role,
        performance=performance_str,
        event_description=event_description
    )
    
    # Step 3: Call OpenAI to generate ONLY the hook sentence
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You generate exactly one sentence. No quotes. No extra text."},
            {"role": "user", "content": meta_prompt}
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    hook = response.choices[0].message.content.strip()
    print(f"    [Hook Engine] Generated Hook: {hook[:80]}...")
    
    # Step 4: Assemble final email (hook + static body)
    email_draft = assemble_email(
        hook=hook,
        contact_name=contact_name,
        company_name=company,
        sender_name=sender_name
    )
    
    return email_draft

def enrich_company_details(item, universe_data):
    """
    Performs the heavy lifting of sourcing contacts for a single company item.
    Returns the updated item dictionary.
    """
    company = item['company']
    print(f"  [Worker] Sourcing contacts for {company}...")
    
    # 1. Domain
    domain = item.get('domain')
    if not domain or "None" in domain:
        url = item.get('event', {}).get('website') or get_company_domain(company)
        if url:
             domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    
    if not domain:
        print(f"  [Worker] Failed to resolve domain for {company}")
        return item
        
    item['domain'] = domain
    
    # 2. Roles
    roles = ["Chief Financial Officer", "Head of Investor Relations", "Company Secretary"]
    found_contacts = item.get('contacts', [])
    existing_names = {normalize_name(c['name']) for c in found_contacts}
    
    for role in roles:
        if len(found_contacts) >= 3: break
        
        # Skip if we already have this role (Simple containment check)
        if any(role.lower() in c.get('role', '').lower() for c in found_contacts):
             continue
        
        # -- PRIMARY METHOD: Google Search + Anymailfinder --
        name = find_officer_name(company, role)
        contact_added = False
        
        if name and normalize_name(name) not in existing_names:
            print(f"    [Primary] Found {name} ({role})")
            email = find_verified_email(name, domain)
            if email:
                print(f"    [Primary] Verified: {email}")
                
                # Try to get phone number via Apollo Cross-Reference
                phones = []
                try:
                    # Only attempt if we have an API key, otherwise it's a wasted call
                    aux = find_contact_via_apollo(domain, role, name=name)
                    if aux and aux.get('phone_numbers'):
                        phones = aux['phone_numbers']
                        print(f"    [Primary] Phone found: {phones}")
                except Exception as e:
                    print(f"    [Primary] Phone check failed: {e}")
                except Exception as e:
                    print(f"    [Primary] Phone check failed: {e}")
                
                # Try to get LinkedIn Profile
                linkedin_url = find_linkedin_url(name, company)
                if linkedin_url:
                    print(f"    [Primary] LinkedIn found: {linkedin_url}")

                found_contacts.append({
                    "name": name, 
                    "role": role, 
                    "email": email, 
                    "phone_numbers": phones,
                    "linkedin": linkedin_url or ""
                })
                existing_names.add(normalize_name(name))
                contact_added = True

                existing_names.add(normalize_name(name))
                contact_added = True
        
        # -- SECONDARY METHOD: Apollo.io (Fallback) --
        if not contact_added:
             print(f"    [Secondary] Trying Apollo for {role}...")
             apollo_contact = find_contact_via_apollo(domain, role)
             if apollo_contact:
                  a_name = apollo_contact['name']
                  if normalize_name(a_name) not in existing_names:
                       print(f"    [Secondary] Apollo found verified: {a_name} ({apollo_contact['email']})")
                       found_contacts.append(apollo_contact)
                       existing_names.add(normalize_name(a_name))
                       contact_added = True
    
    # Fallback
    if not found_contacts:
        found_contacts.append({"name": "Investor Relations", "role": "Generic", "email": f"ir@{domain}"})
        
    item['contacts'] = found_contacts
    
    # 3. Generate Email Drafts for EACH contact (Hybrid Engine: Hook + Static Body)
    perf_str = get_performance_data(item.get('ticker'), universe_data)
    
    email_drafts = []
    for contact in found_contacts:
        contact_name = contact.get('name', 'there')
        contact_role = contact.get('role', '')
        
        print(f"    [Hook Engine] Generating draft for {contact_name} ({contact_role})...")
        
        # Generate personalized email for this specific contact
        email_draft = generate_hook(
            company, 
            item['event'], 
            contact_name, 
            perf_str, 
            sender_name="Your Name"
        )
        
        # Store with contact info for reference
        email_drafts.append({
            "contact_name": contact_name,
            "contact_role": contact_role,
            "contact_email": contact.get('email', ''),
            "draft": email_draft
        })
    
    # Save all drafts
    item['email_drafts'] = email_drafts
    
    # Backwards compatibility: first draft goes to these fields
    if email_drafts:
        item['email_draft'] = email_drafts[0]['draft']
        item['draft_hook'] = email_drafts[0]['draft']
    
    item['status'] = "needs_approval" # Ready for review
    
    return item

def process_leads():
    # 1. SETUP
    try:
        with open(INPUT_FILE, 'r') as f: triggers = json.load(f)
    except:
        print("No active triggers.")
        return

    universe_data = []
    for f_name in ["ftse_constituents.json", "dax_constituents.json"]:
        try:
            with open(f_name, 'r') as f: universe_data.extend(json.load(f))
        except: pass

    # 2. LOAD EXISTING QUEUE
    current_queue = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f: current_queue = json.load(f)
        
    existing_companies = {item['company']: item for item in current_queue}
    
    # 3. PHASE 1: POPULATE QUEUE (FAST)
    print("Phase 1: Populating Dashboard with triggers...")
    
    # Group triggers
    grouped = {}
    for t in triggers:
        grouped.setdefault(t['company'], []).append(t)
        
    new_items_added = False
    
    for company, t_list in grouped.items():
        # Merge event types
        event_types = sorted(list({t.get('event_type') for t in t_list if t.get('event_type')}))
        combined_event = " / ".join(event_types)
        
        base_t = t_list[0]
        base_t['event_type'] = combined_event # Update for record
        
        perf_str = get_performance_data(base_t.get('ticker'), universe_data)
        
        if company in existing_companies:
            # Update event if new
            item = existing_companies[company]
            old_evt = item.get('event', {}).get('event_type', '')
            if combined_event not in old_evt:
                item['event']['event_type'] = f"{old_evt} / {combined_event}"
                # If we updated info, maybe reset status?
                # item['status'] = pending_sourcing?
                # User might have already approved. Let's leave status unless "Pending".
        else:
            # Create NEW pending item
            new_item = {
                "company": company,
                "ticker": base_t.get('ticker'),
                "domain": base_t.get('website'), # Preliminary
                "performance": perf_str,
                "contacts": [],
                "primary_email": "",
                "event": base_t,
                "index_name": base_t.get("index_name", "FTSE"),
                "draft_hook": "Pending Sourcing...",
                "status": "Pending Sourcing"
            }
            current_queue.append(new_item)
            existing_companies[company] = new_item
            new_items_added = True

    # Save Queue & Sync
    with open(OUTPUT_FILE, 'w') as f: json.dump(current_queue, f, indent=2)
    print("Dashboard populated.")
    
    print("Syncing to Google Sheets...")
    sync_to_sheet()
    
    # 4. PHASE 2: PARALLEL SOURCING
    items_to_enrich = [
        item for item in current_queue 
        if item.get('status') == "Pending Sourcing" or (item.get('status') != "approved" and len(item.get('contacts', [])) < 3)
    ]
    
    if not items_to_enrich:
        print("All items enriched.")
        return

    print(f"Phase 2: Enriching {len(items_to_enrich)} companies in parallel...")
    
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {executor.submit(enrich_company_details, item, universe_data): item['company'] for item in items_to_enrich}
        
        for future in as_completed(future_map):
            company = future_map[future]
            try:
                updated_item = future.result()
                
                # Update in main list ID-wise (by company name ref)
                for idx, q_item in enumerate(current_queue):
                    if q_item['company'] == updated_item['company']:
                        current_queue[idx] = updated_item
                        break
                
                # Incremental Save
                with open(OUTPUT_FILE, 'w') as f: json.dump(current_queue, f, indent=2)
                print(f"  [Saved] {company} enriched.")
                
            except Exception as e:
                print(f"  [Error] Failed to enrich {company}: {e}")

    print("Enrichment complete. Final Sync...")
    sync_to_sheet()

if __name__ == "__main__":
    process_leads()
