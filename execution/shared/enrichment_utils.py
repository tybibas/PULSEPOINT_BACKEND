"""
Shared enrichment utilities for QuantiFire backend.
Canonical versions of functions previously duplicated across 5+ scripts.

Used by: monitor_companies_job.py, enrich_pulsepoint_job.py, enrich_pulsepoint_accounts.py,
         batch_enrich_cleanup.py, find_high_fit_accounts.py, find_accounts_fast.py
"""
import os
import re
import requests
from urllib.parse import urlparse


# ===== NAME VALIDATION =====

def is_valid_full_name(name: str) -> bool:
    """
    Validates that a string looks like a real person's full name.
    Rejects single names, very short names, and names containing digits.
    """
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


# ===== COMPANY NORMALIZATION =====

# Common suffixes stripped during normalization
_COMPANY_SUFFIXES = r'\b(inc|llc|ltd|corp|corporation|co|company|group|agency|studios?|partners?|solutions?|enterprises?)\b'

# Generic page names that should never match as a company
_GENERIC_NAMES = frozenset([
    "home", "about", "contact", "index", "main", "page",
    "site", "search", "login", "signup"
])

def normalize_company(name: str) -> str:
    """
    Normalizes a company name by lowercasing, stripping common suffixes,
    and removing special characters.
    """
    if not name:
        return ""
    clean = re.sub(_COMPANY_SUFFIXES, '', name.lower(), flags=re.IGNORECASE)
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    return clean.strip()


def company_matches(profile_text: str, target: str) -> bool:
    """
    Strict company name matching using word boundaries.
    Returns True only if the normalized target appears as a whole-word match
    in the profile text. Rejects generic/short names.
    """
    if not profile_text or not target:
        return False

    norm_target = normalize_company(target)

    # Reject generic names
    if norm_target in _GENERIC_NAMES:
        return False

    if len(norm_target) < 3:
        return False  # Too short to be safe

    norm_profile = profile_text.lower()

    # Word boundary match
    pattern = fr"\b{re.escape(norm_target)}\b"
    return bool(re.search(pattern, norm_profile))


# ===== JUNK NAME DETECTION =====

JUNK_COMPANY_NAMES = frozenset([
    "unknown", "branding studios", "not specified", "mid-sized marketing agencies",
    "n/a", "tbd", "test", "example"
])

def is_junk_company_name(name: str) -> bool:
    """Returns True if the company name is a known junk/placeholder value."""
    if not name or len(name.strip()) < 3:
        return True
    return name.strip().lower() in JUNK_COMPANY_NAMES


# ===== WEBSITE DISCOVERY =====

# Domains to filter out of website results
_JUNK_DOMAINS = frozenset([
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com",
    "glassdoor.com", "zoominfo.com", "yelp.com", "crunchbase.com"
])

def find_website(company_name: str, apify_client) -> str | None:
    """
    Finds a company's official website via Google Search (Apify).
    Returns the domain (e.g. 'example.com') or None.
    """
    print(f"    📡 Finding website for: {company_name}")
    try:
        run = apify_client.actor("apify/google-search-scraper").call(run_input={
            "queries": f'"{company_name}" official website',
            "resultsPerPage": 3,
            "maxPagesPerQuery": 1,
        })
        items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        for page in items:
            for res in page.get("organicResults", []):
                url = res.get("url", "")
                if not url:
                    continue
                parsed = urlparse(url)
                domain = parsed.netloc.replace("www.", "")
                # Skip social/directory sites
                if any(junk in domain for junk in _JUNK_DOMAINS):
                    continue
                if domain and len(domain) >= 4:
                    print(f"    ✅ Found website: {domain}")
                    return domain
    except Exception as e:
        print(f"    ⚠️ Website search error: {e}")
    return None


# ===== DECISION MAKER DISCOVERY =====

# Job titles to search for
_EXECUTIVE_TITLES = (
    'CEO OR Founder OR "Managing Director" OR Principal OR Owner '
    'OR CMO OR "VP Marketing" OR "VP Operations" OR "Head of Operations"'
)

def find_decision_makers(company_name: str, apify_client, max_candidates: int = 3) -> list:
    """
    Finds decision makers via LinkedIn Google Search.
    Returns a list of dicts: [{"name": ..., "title": ..., "linkedin": ...}]
    """
    print(f"    🔍 Searching LinkedIn for decision makers at: {company_name}")
    query = f'site:linkedin.com/in/ "{company_name}" ({_EXECUTIVE_TITLES})'
    candidates = []
    seen_names = set()

    try:
        run = apify_client.actor("apify/google-search-scraper").call(run_input={
            "queries": query,
            "resultsPerPage": 5,
            "maxPagesPerQuery": 1,
            "countryCode": "us"
        })
        items = apify_client.dataset(run["defaultDatasetId"]).list_items().items

        for page in items:
            for res in page.get("organicResults", []):
                title = res.get("title", "")
                url = res.get("url", "")

                if "linkedin.com/in/" not in url:
                    continue

                # Strict company match check
                if not company_matches(title, company_name):
                    continue

                # Extract name (before first separator)
                name = title.split(" - ")[0].split("|")[0].split("–")[0].strip()

                if not is_valid_full_name(name):
                    continue

                name_lower = name.lower()
                if name_lower in seen_names:
                    continue
                seen_names.add(name_lower)

                # Extract job title
                job_title = "Executive"
                if " - " in title:
                    parts = title.split(" - ")
                    if len(parts) > 1:
                        job_title = parts[1].split("|")[0].strip()[:100]

                candidates.append({
                    "name": name,
                    "title": job_title,
                    "linkedin": url
                })

                if len(candidates) >= max_candidates:
                    break
            if len(candidates) >= max_candidates:
                break

    except Exception as e:
        print(f"    ⚠️ LinkedIn search error: {e}")

    print(f"    Found {len(candidates)} candidates")
    return candidates


# ===== EMAIL VERIFICATION =====

def verify_email(name: str, domain: str, api_key: str = None) -> str | None:
    """
    Verifies/finds an email address via Anymailfinder.
    Returns the email string or None.
    
    Args:
        name: Full name of the person
        domain: Company domain (e.g. 'example.com')
        api_key: Anymailfinder API key. Falls back to ANYMAILFINDER_API_KEY env var.
    """
    if not api_key:
        api_key = os.environ.get("ANYMAILFINDER_API_KEY")
    if not api_key:
        print("    ⚠️ No Anymailfinder API key available")
        return None

    try:
        resp = requests.post(
            "https://api.anymailfinder.com/v5.0/search/person.json",
            headers={"Authorization": api_key},
            json={"full_name": name, "domain": domain},
            timeout=15
        )
        data = resp.json()
        return data.get("results", {}).get("email")
    except Exception as e:
        print(f"    ⚠️ Email verify error for {name}@{domain}: {e}")
    return None


def verify_email_domain(domain: str, api_key: str = None, max_emails: int = 5) -> list | None:
    """
    Finds emails for a domain via Anymailfinder company search.
    Returns a list of email strings or None.
    
    Args:
        domain: Company domain (e.g. 'example.com')
        api_key: Anymailfinder API key. Falls back to ANYMAILFINDER_API_KEY env var.
        max_emails: Maximum number of emails to return.
    """
    if not api_key:
        api_key = os.environ.get("ANYMAILFINDER_API_KEY")
    if not api_key:
        print("    ⚠️ No Anymailfinder API key available")
        return None

    try:
        resp = requests.post(
            "https://api.anymailfinder.com/v5.0/search/company.json",
            headers={"Authorization": api_key},
            json={"domain": domain},
            timeout=15
        )
        data = resp.json()

        if "results" in data and "emails" in data["results"]:
            emails = data["results"]["emails"]
            if emails:
                return [e for e in emails if "@" in e][:max_emails]
        return None
    except Exception as e:
        print(f"    ⚠️ Domain email search error for {domain}: {e}")
    return None
