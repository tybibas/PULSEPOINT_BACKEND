
import modal
import os
import requests
import time
import re
from dotenv import load_dotenv

# Define Image
image = (
    modal.Image.debian_slim()
    .pip_install("supabase", "apify-client", "python-dotenv", "requests")
)

app = modal.App("quantifire-enrichment-worker")

# ================== INLINE HELPERS (Modal sandbox-safe) ==================
# These are defined at module level so they work inside Modal's remote execution.
# They mirror the canonical versions in shared/enrichment_utils.py.

_JUNK_NAMES = frozenset([
    "unknown", "branding studios", "not specified",
    "mid-sized marketing agencies", "n/a", "tbd", "test", "example"
])

def _is_valid_full_name(name: str) -> bool:
    if not name or len(name) < 5:
        return False
    parts = name.strip().split()
    if len(parts) < 2:
        return False
    for part in parts:
        if len(part) < 2:
            return False
    if re.search(r'\d', name):
        return False
    return True

def _normalize_company(name: str) -> str:
    if not name:
        return ""
    clean = re.sub(
        r'\b(inc|llc|ltd|corp|corporation|co|company|group|agency|studios?|partners?|solutions?|enterprises?)\b',
        '', name.lower(), flags=re.IGNORECASE
    )
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    return clean.strip()

_GENERIC_NAMES = frozenset([
    "home", "about", "contact", "index", "main",
    "page", "site", "search", "login", "signup"
])

def _company_matches(profile_text: str, target: str) -> bool:
    if not profile_text or not target:
        return False
    norm_target = _normalize_company(target)
    if norm_target in _GENERIC_NAMES or len(norm_target) < 3:
        return False
    pattern = fr"\b{re.escape(norm_target)}\b"
    return bool(re.search(pattern, profile_text.lower()))


def _resolve_leads_table(supabase, client_context: str) -> str:
    """Look up the leads table name from client_strategies. Falls back to convention."""
    try:
        resp = supabase.table("client_strategies")\
            .select("config")\
            .eq("slug", client_context)\
            .limit(1)\
            .execute()
        if resp.data:
            config = resp.data[0].get("config", {})
            table = config.get("leads_table")
            if table:
                return table
    except Exception as e:
        print(f"⚠️ Could not resolve leads table from DB: {e}")
    # Convention fallback: SLUG_TRIGGERED_LEADS (uppercased)
    return f"{client_context.upper()}_TRIGGERED_LEADS"


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=3600
)
def enrich_accounts(client_context: str = "pulsepoint_strategic"):
    """
    Client-aware enrichment script.
    
    Finds decision-makers at target companies for any client.
    Validates: company name match, name quality, email verification.
    
    Args:
        client_context: Slug identifying the client (e.g. 'pulsepoint_strategic', 'mike_ecker')
    """
    print(f"🚀 Starting Enrichment Job for: {client_context}")

    from supabase import create_client
    from apify_client import ApifyClient

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
    ANYMAILFINDER_KEY = os.environ.get("ANYMAILFINDER_API_KEY")

    if not all([SUPABASE_URL, SUPABASE_KEY, APIFY_TOKEN, ANYMAILFINDER_KEY]):
        print("❌ Missing API Keys")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    apify = ApifyClient(APIFY_TOKEN)

    # Resolve leads table dynamically
    leads_table = _resolve_leads_table(supabase, client_context)
    print(f"📋 Using leads table: {leads_table}")

    # ================== CORE FUNCTIONS ==================

    def find_website(company_name: str) -> str:
        print(f"  🔍 Finding website for: {company_name}")
        query = f'"{company_name}" official website -site:linkedin.com -site:facebook.com -site:instagram.com'
        try:
            run = apify.actor("apify/google-search-scraper").call(run_input={
                "queries": query, "resultsPerPage": 3, "maxPagesPerQuery": 1, "countryCode": "us"
            })
            items = apify.dataset(run["defaultDatasetId"]).list_items().items
            for page in items:
                for res in page.get("organicResults", []):
                    url = res.get("url")
                    if url:
                        domain = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
                        print(f"    -> Found Domain: {domain}")
                        return domain
        except Exception as e:
            print(f"    -> Error finding website: {e}")
        return None

    def find_decision_makers(company_name: str) -> list:
        """Find and validate decision-makers at a company via LinkedIn."""
        print(f"  🔍 Finding decision makers for: {company_name}")
        query = f'site:linkedin.com/in/ "{company_name}" (CEO OR Founder OR "Managing Director" OR Principal OR Owner OR CMO OR "VP Marketing")'
        candidates = []
        seen_names = set()

        try:
            run = apify.actor("apify/google-search-scraper").call(run_input={
                "queries": query, "resultsPerPage": 5, "maxPagesPerQuery": 1, "countryCode": "us"
            })
            items = apify.dataset(run["defaultDatasetId"]).list_items().items

            for page in items:
                for res in page.get("organicResults", []):
                    title = res.get("title", "")
                    url = res.get("url", "")

                    if "linkedin.com/in/" not in url:
                        continue
                    if not _company_matches(title, company_name):
                        continue

                    name = title.split(" - ")[0].split("|")[0].split("–")[0].strip()
                    if not _is_valid_full_name(name):
                        continue

                    name_lower = name.lower()
                    if name_lower in seen_names:
                        continue
                    seen_names.add(name_lower)

                    job_title = "Executive"
                    if " - " in title:
                        parts = title.split(" - ")
                        if len(parts) > 1:
                            job_title = parts[1].split("|")[0].strip()[:100]

                    candidates.append({"name": name, "title": job_title, "linkedin": url})
                    if len(candidates) >= 3:
                        break
                if len(candidates) >= 3:
                    break

            print(f"    -> Found {len(candidates)} validated candidates.")
        except Exception as e:
            print(f"    -> Error finding decision makers: {e}")
        return candidates

    def verify_email(name: str, domain: str) -> str:
        try:
            resp = requests.post(
                "https://api.anymailfinder.com/v5.0/search/person.json",
                headers={"Authorization": ANYMAILFINDER_KEY},
                json={"full_name": name, "domain": domain},
                timeout=15
            )
            data = resp.json()
            return data.get("results", {}).get("email")
        except Exception as e:
            print(f"    -> Email verify error: {e}")
        return None

    # ================== MAIN LOGIC ==================

    companies = supabase.table("triggered_companies")\
        .select("*")\
        .eq("client_context", client_context)\
        .execute().data

    print(f"Found {len(companies)} companies for {client_context}.")

    stats = {"processed": 0, "leads_added": 0, "skipped_existing": 0, "skipped_junk": 0}

    for comp in companies:
        company_name = comp.get('company', '').strip()

        if company_name.lower() in _JUNK_NAMES or len(company_name) < 3:
            print(f"Skipping junk: {company_name}")
            stats["skipped_junk"] += 1
            continue

        print(f"\nProcessing: {company_name} ({comp['id']})")
        stats["processed"] += 1

        # Get or find website
        domain = comp.get('website')
        if not domain:
            domain = find_website(company_name)
            if domain:
                try:
                    supabase.table("triggered_companies").update({"website": domain}).eq("id", comp['id']).execute()
                except Exception as e:
                    print(f"    -> Error updating website: {e}")

        if not domain:
            print("    -> No website found. Skipping.")
            continue

        # Check for existing leads
        existing = supabase.table(leads_table)\
            .select("id", count="exact")\
            .eq("triggered_company_id", comp['id'])\
            .execute()

        if existing.count > 0:
            print(f"    -> {existing.count} leads already exist. Skipping.")
            stats["skipped_existing"] += 1
            continue

        # Find and validate decision makers
        candidates = find_decision_makers(company_name)

        for person in candidates:
            email = verify_email(person['name'], domain)
            if email:
                print(f"    ✅ VALID: {person['name']} <{email}>")
                try:
                    supabase.table(leads_table).insert({
                        "triggered_company_id": comp['id'],
                        "name": person['name'],
                        "title": person['title'],
                        "email": email,
                        "linkedin_url": person['linkedin'],
                        "contact_status": "pending"
                    }).execute()
                    stats["leads_added"] += 1
                except Exception as e:
                    print(f"    ❌ Insert error: {e}")
            else:
                print(f"    ❌ No email found: {person['name']}")

        time.sleep(1)

    print(f"\n{'='*50}")
    print(f"✅ Enrichment Complete for {client_context}!")
    print(f"   Processed: {stats['processed']}")
    print(f"   Leads Added: {stats['leads_added']}")
    print(f"   Skipped (existing): {stats['skipped_existing']}")
    print(f"   Skipped (junk): {stats['skipped_junk']}")
    print(f"{'='*50}")


# Backward-compatible alias
enrich_pulsepoint_accounts = enrich_accounts


@app.local_entrypoint()
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", default="pulsepoint_strategic",
                        help="Client context slug (default: pulsepoint_strategic)")
    args = parser.parse_args()

    print(f"Triggering enrichment for: {args.client}")
    enrich_accounts.spawn(client_context=args.client)
    print("Job spawned! Check Modal dashboard for logs.")
