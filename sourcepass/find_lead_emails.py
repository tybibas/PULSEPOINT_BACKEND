#!/usr/bin/env python3
"""
Email Finder for Sourcepass Leads

Uses Anymailfinder API to find verified email addresses.
Falls back to Apollo.io if Anymailfinder returns nothing.

USAGE:
    python find_lead_emails.py

This script will:
1. Use Anymailfinder for each lead
2. Fall back to Apollo.io if needed
3. Output results to leads/enriched_contacts.json
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# API Keys
AMF_API_KEY = os.getenv("ANYMAILFINDER_API_KEY")
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

# Output file
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "leads/enriched_contacts.json")


def find_email_anymailfinder(full_name: str, domain: str) -> dict:
    """
    Use Anymailfinder API to find verified email.
    Returns dict with email, validation status, and source.
    """
    if not AMF_API_KEY:
        print("  [ERROR] No ANYMAILFINDER_API_KEY found")
        return None
    
    if not full_name or not domain:
        return None
    
    print(f"  [AMF] Searching: {full_name} @ {domain}")
    
    try:
        resp = requests.post(
            "https://api.anymailfinder.com/v5.0/search/person.json",
            headers={
                "Authorization": AMF_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "full_name": full_name,
                "domain": domain
            },
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"  [AMF] Response: {data}")
            
            if data.get('success'):
                results = data.get('results', {})
                email = results.get('email')
                validation = results.get('validation')
                email_class = results.get('email_class')
                
                if email:
                    return {
                        "email": email,
                        "validation": validation,
                        "email_class": email_class,
                        "source": "anymailfinder",
                        "verified": validation == 'valid' or email_class == 'verified'
                    }
        else:
            print(f"  [AMF] Error status: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"  [AMF] Exception: {e}")
    
    return None


def find_contact_apollo(domain: str, role_title: str, name: str = None) -> dict:
    """
    Use Apollo.io API to find contact.
    Returns dict with name, email, role, etc.
    """
    if not APOLLO_API_KEY:
        print("  [Apollo] No APOLLO_API_KEY found")
        return None
    
    print(f"  [Apollo] Searching: {role_title} @ {domain}" + (f" ({name})" if name else ""))
    
    try:
        resp = requests.post(
            "https://api.apollo.io/v1/mixed_people/search",
            headers={
                "Content-Type": "application/json",
                "Cache-Control": "no-cache",
                "X-Api-Key": APOLLO_API_KEY
            },
            json={
                "q_organization_domains": domain,
                "person_titles": [role_title],
                "page": 1,
                "per_page": 5,
                "contact_email_status": ["verified"]
            },
            timeout=30
        )
        
        if resp.status_code == 200:
            data = resp.json()
            people = data.get('people', [])
            
            results = []
            for p in people:
                if p.get('email') and p.get('email_status') == 'verified':
                    contact = {
                        "name": f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
                        "email": p.get('email'),
                        "role": p.get('title', role_title),
                        "linkedin": p.get('linkedin_url', ''),
                        "source": "apollo",
                        "verified": True
                    }
                    results.append(contact)
                    
            return results if results else None
        else:
            print(f"  [Apollo] Error status: {resp.status_code}")
            
    except Exception as e:
        print(f"  [Apollo] Exception: {e}")
    
    return None


def guess_email_pattern(name: str, domain: str) -> str:
    """
    Generate likely email patterns when API lookup fails.
    Most common pattern: first.last@domain or first@domain
    """
    parts = name.lower().split()
    if len(parts) >= 2:
        first = parts[0]
        last = parts[-1]
        # Common corporate patterns
        patterns = [
            f"{first}.{last}@{domain}",      # john.smith@company.com
            f"{first[0]}{last}@{domain}",     # jsmith@company.com
            f"{first}{last[0]}@{domain}",     # johns@company.com
            f"{first}@{domain}",              # john@company.com
        ]
        return patterns[0]  # Return most common pattern
    return None


# ========================================
# SOURCEPASS LEAD DEFINITIONS
# ========================================

LEADS_TO_ENRICH = [
    {
        "company": "Penn State Health",
        "domain": "pennstatehealth.org",
        "trigger": "New CIO Appointed November 2025",
        "contacts_to_find": [
            {"name": "Dennis Sutterfield", "role": "SVP & CIO"}
        ]
    },
    {
        "company": "Allegheny Health Network",
        "domain": "ahn.org",
        "trigger": "New CDIO + Data Breach Feb 2025",
        "contacts_to_find": [
            {"name": "Richard Medford", "role": "Chief Digital Information Officer"},
            {"name": "John Gabrick", "role": "VP Clinical Information Systems"}
        ]
    },
    {
        "company": "Bayhealth Medical Center",
        "domain": "bayhealth.org",
        "trigger": "New CIO Jan 2026 + Breach Settlement",
        "contacts_to_find": [
            {"name": "Thomas Marlow", "role": "VP Chief Digital & Information Officer"},
            {"name": "Jonathan Kaufmann", "role": "VP Chief Health Information Officer"}
        ]
    },
    {
        "company": "Central Jersey Medical Center",
        "domain": "cjmc.us",
        "trigger": "Ransomware Attack Aug 2025",
        "contacts_to_find": [
            {"name": "John O'Leary", "role": "CEO"},
            {"name": "Thomas Boggiano", "role": "COO/CFO"}
        ]
    },
    {
        "company": "Gaylord Specialty Healthcare",
        "domain": "gaylord.org",
        "trigger": "New CIO Jan 2025",
        "contacts_to_find": [
            {"name": "VP & CIO", "role": "VP & CIO"}  # Name TBD
        ]
    }
]


def main():
    print("=" * 60)
    print("SOURCEPASS - EMAIL ENRICHMENT")
    print("=" * 60)
    print(f"Anymailfinder Key: {'✓' if AMF_API_KEY else '✗'}")
    print(f"Apollo Key: {'✓' if APOLLO_API_KEY else '✗'}")
    print()
    
    enriched_results = []
    
    for lead in LEADS_TO_ENRICH:
        company = lead["company"]
        domain = lead["domain"]
        trigger = lead.get("trigger", "")
        
        print(f"\n{'='*60}")
        print(f"LEAD: {company}")
        print(f"Domain: {domain}")
        print(f"Trigger: {trigger}")
        print(f"{'='*60}")
        
        company_result = {
            "company": company,
            "domain": domain,
            "trigger": trigger,
            "contacts": []
        }
        
        for contact in lead["contacts_to_find"]:
            name = contact["name"]
            role = contact["role"]
            
            print(f"\n  Contact: {name} ({role})")
            print(f"  {'-'*40}")
            
            contact_result = {
                "name": name,
                "role": role,
                "email": None,
                "source": None,
                "verified": False
            }
            
            # Skip if name is placeholder
            if "TBD" in name or "VP &" in name:
                print(f"  ~ Skipping: Name unknown, using pattern guess")
                contact_result["email"] = guess_email_pattern(name.replace("VP &", "").strip(), domain)
                contact_result["source"] = "pattern_guess"
                contact_result["verified"] = False
            else:
                # Method 1: Anymailfinder
                amf_result = find_email_anymailfinder(name, domain)
                
                if amf_result and amf_result.get('email'):
                    contact_result["email"] = amf_result["email"]
                    contact_result["source"] = "anymailfinder"
                    contact_result["verified"] = amf_result.get("verified", False)
                    contact_result["validation"] = amf_result.get("validation")
                    print(f"  ✓ FOUND via Anymailfinder: {amf_result['email']}")
                else:
                    print(f"  ✗ Not found via Anymailfinder")
                    
                    # Method 2: Apollo Fallback
                    apollo_results = find_contact_apollo(domain, role, name)
                    
                    if apollo_results:
                        # Try to match by name
                        matched = None
                        for ar in apollo_results:
                            if name.lower() in ar["name"].lower() or ar["name"].lower() in name.lower():
                                matched = ar
                                break
                        
                        if matched:
                            contact_result["email"] = matched["email"]
                            contact_result["source"] = "apollo"
                            contact_result["verified"] = True
                            contact_result["linkedin"] = matched.get("linkedin", "")
                            print(f"  ✓ FOUND via Apollo: {matched['email']}")
                        else:
                            # Take first result
                            ar = apollo_results[0]
                            contact_result["email"] = ar["email"]
                            contact_result["source"] = "apollo (different contact)"
                            contact_result["verified"] = True
                            contact_result["actual_name"] = ar["name"]
                            contact_result["actual_role"] = ar["role"]
                            print(f"  ~ FOUND via Apollo (different): {ar['name']} - {ar['email']}")
                    else:
                        # Method 3: Pattern Guess
                        guessed = guess_email_pattern(name, domain)
                        if guessed:
                            contact_result["email"] = guessed
                            contact_result["source"] = "pattern_guess"
                            contact_result["verified"] = False
                            print(f"  ~ Using pattern guess: {guessed}")
                        else:
                            print(f"  ✗ Could not find or guess email")
            
            company_result["contacts"].append(contact_result)
        
        enriched_results.append(company_result)
    
    # Save results
    print(f"\n{'='*60}")
    print("SAVING RESULTS")
    print(f"{'='*60}")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(enriched_results, f, indent=2)
    
    print(f"✓ Results saved to: {OUTPUT_FILE}")
    
    # Print Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for result in enriched_results:
        print(f"\n{result['company']}:")
        for contact in result["contacts"]:
            status = "✓" if contact.get("verified") else ("~" if contact.get("email") else "✗")
            email = contact.get("email", "NOT FOUND")
            source = f"({contact.get('source', 'N/A')})" if contact.get("email") else ""
            print(f"  {status} {contact['name']}: {email} {source}")


if __name__ == "__main__":
    main()
