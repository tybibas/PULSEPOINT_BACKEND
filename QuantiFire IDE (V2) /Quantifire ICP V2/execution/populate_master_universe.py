#!/usr/bin/env python3
"""
populate_master_universe.py

Populates the Master_Universe tab with DAX 40 companies, enriched contacts,
context snippets, and AI hooks for bulk cold outreach campaigns.

Usage:
    python execution/populate_master_universe.py           # Full run (all 40 companies)
    python execution/populate_master_universe.py --test    # Test mode (3 companies)
"""

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Add root path to find local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.enrich_lead import (
    find_officer_name,
    find_verified_email,
    find_contact_via_apollo,
    normalize_name,
    get_performance_data
)
from templates.prompts import (
    generate_consulting_grade_prompt, 
    assemble_email,
    filter_spam,
    ANALYST_SYSTEM_PROMPT
)
from execution.personalization_research import get_personalization_context
from openai import OpenAI

load_dotenv()

# Config
DAX_FILE = "dax_constituents.json"
OUTPUT_FILE = "master_universe_queue.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Target roles to source
TARGET_ROLES = ["Chief Financial Officer", "Head of Investor Relations", "Company Secretary"]


def parse_name(full_name: str) -> tuple:
    """Split full name into first and last name."""
    if not full_name:
        return ("", "")
    parts = full_name.strip().split()
    if len(parts) == 1:
        return (parts[0], "")
    return (parts[0], " ".join(parts[1:]))


def generate_context_snippet(company_data: dict) -> str:
    """
    Generate a context snippet based on stock performance.
    Example: "Stock +28.1% (52-wk)" or "Underperforming: -15.2% (52-wk)"
    """
    change = company_data.get("fifty_two_week_change", 0) or 0
    pct = change * 100
    
    if pct >= 0:
        return f"Stock +{pct:.1f}% (52-wk)"
    else:
        return f"Underperforming: {pct:.1f}% (52-wk)"


def generate_consulting_grade_hook(
    company_name: str, 
    contact_name: str, 
    context: dict
) -> str:
    """
    Generate a consulting-grade AI hook using one of three archetypes:
    - Transcript Miner: References Q&A friction from earnings calls
    - Peer Gap: Highlights valuation disparity with competitors
    - Event Context: Connects performance to narrative risk
    
    Uses the Specificity Bridge formula and anti-spam filtering.
    """
    if not OPENAI_API_KEY:
        return "Error: No OpenAI Key"
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Get recommended archetype from context
    archetype = context.get("recommended_archetype", "event_context")
    
    # Generate the appropriate prompt
    prompt = generate_consulting_grade_prompt(
        archetype=archetype,
        contact_name=contact_name,
        company_name=company_name,
        context=context
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": ANALYST_SYSTEM_PROMPT
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=100  # Reduced for 25-word constraint
        )
        hook = response.choices[0].message.content.strip()
        
        # Apply anti-spam filter
        hook = filter_spam(hook)
        
        # Clean up any quotes the LLM might add
        hook = hook.strip('"').strip("'")
        
        # Assemble full email using the static body
        email_draft = assemble_email(
            hook=hook,
            contact_name=contact_name,
            company_name=company_name,
            sender_name="Your Name"
        )
        
        return email_draft
        
    except Exception as e:
        print(f"    [Hook Error] {e}")
        return f"Error generating hook: {e}"


def enrich_company_for_universe(company_data: dict, all_companies: list) -> list:
    """
    Enrich a single company and return list of Master_Universe rows.
    Creates one row per verified contact.
    
    Args:
        company_data: Company dict from dax_constituents.json
        all_companies: Full list of all companies for peer comparison
    """
    company_name = company_data.get("name")
    ticker = company_data.get("ticker")
    website = company_data.get("website", "")
    
    print(f"\n[Processing] {company_name} ({ticker})")
    
    # Extract domain from website
    domain = None
    if website:
        domain = website.split("//")[-1].split("/")[0].replace("www.", "")
    
    if not domain:
        print(f"  [Skip] No domain found for {company_name}")
        return []
    
    # Build personalization context for this company
    context = get_personalization_context(company_data, all_companies)
    archetype = context.get("recommended_archetype", "event_context")
    print(f"  [Context] Archetype: {archetype}, Performance: {context['company_basics']['performance']}%")
    
    # Context snippet
    context_snippet = generate_context_snippet(company_data)
    
    rows = []
    existing_names = set()
    
    for role in TARGET_ROLES:
        # -- PRIMARY: Google Search + Anymailfinder --
        name = find_officer_name(company_name, role)
        contact_added = False
        
        if name and normalize_name(name) not in existing_names:
            print(f"  [Primary] Found {name} ({role})")
            email = find_verified_email(name, domain)
            
            if email:
                print(f"  [Primary] Verified: {email}")
                first_name, last_name = parse_name(name)
                
                # Generate AI hook using consulting-grade personalization
                print(f"  [Hook] Generating for {first_name} ({archetype})...")
                ai_hook = generate_consulting_grade_hook(company_name, first_name, context)
                
                rows.append({
                    "Company_Name": company_name,
                    "Ticker": ticker,
                    "Index": "DAX 40",
                    "First_Name": first_name,
                    "Last_Name": last_name,
                    "Role": role,
                    "Email_Address": email,
                    "Context_Snippet": context_snippet,
                    "AI_Hook_Draft": ai_hook,
                    "Status": "New"
                })
                existing_names.add(normalize_name(name))
                contact_added = True
        
        # -- SECONDARY: Apollo.io Fallback --
        if not contact_added:
            print(f"  [Secondary] Trying Apollo for {role}...")
            apollo_contact = find_contact_via_apollo(domain, role)
            
            if apollo_contact and apollo_contact.get("email"):
                a_name = apollo_contact.get("name", "")
                if normalize_name(a_name) not in existing_names:
                    print(f"  [Secondary] Apollo found: {a_name} ({apollo_contact['email']})")
                    first_name, last_name = parse_name(a_name)
                    
                    # Generate AI hook using consulting-grade personalization
                    print(f"  [Hook] Generating for {first_name} ({archetype})...")
                    ai_hook = generate_consulting_grade_hook(company_name, first_name, context)
                    
                    rows.append({
                        "Company_Name": company_name,
                        "Ticker": ticker,
                        "Index": "DAX 40",
                        "First_Name": first_name,
                        "Last_Name": last_name,
                        "Role": apollo_contact.get("role", role),
                        "Email_Address": apollo_contact["email"],
                        "Context_Snippet": context_snippet,
                        "AI_Hook_Draft": ai_hook,
                        "Status": "New"
                    })
                    existing_names.add(normalize_name(a_name))
    
    # If no contacts found at all, create a generic IR fallback
    if not rows:
        print(f"  [Fallback] Creating generic IR contact")
        rows.append({
            "Company_Name": company_name,
            "Ticker": ticker,
            "Index": "DAX 40",
            "First_Name": "Investor Relations",
            "Last_Name": "Team",
            "Role": "Investor Relations",
            "Email_Address": f"ir@{domain}",
            "Context_Snippet": context_snippet,
            "AI_Hook_Draft": generate_consulting_grade_hook(company_name, "there", context),
            "Status": "New"
        })
    
    print(f"  [Done] {len(rows)} contacts found for {company_name}")
    return rows


def main():
    # Check for test mode
    test_mode = "--test" in sys.argv
    
    # Load DAX data
    if not os.path.exists(DAX_FILE):
        print(f"Error: {DAX_FILE} not found")
        return
    
    with open(DAX_FILE, 'r') as f:
        dax_data = json.load(f)
    
    print(f"Loaded {len(dax_data)} DAX companies")
    
    # Limit in test mode
    if test_mode:
        dax_data = dax_data[:3]
        print(f"TEST MODE: Processing only {len(dax_data)} companies")
    
    # Load existing queue if present (append mode)
    existing_rows = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            existing_rows = json.load(f)
        print(f"Loaded {len(existing_rows)} existing rows")
    
    # Track existing company-email pairs to avoid duplicates
    existing_keys = {(r["Company_Name"], r["Email_Address"]) for r in existing_rows}
    
    # Process companies (sequential for API rate limiting)
    all_rows = list(existing_rows)
    
    processed_count = 0
    for company_data in dax_data:
        # User requested limit to ~10 lines (approx 4 companies)
        if processed_count >= 4:
            print("Reached limit of 4 companies (approx 10-12 lines). Stopping.")
            break
        processed_count += 1
        try:
            # Pass full dax_data for peer comparison context
            new_rows = enrich_company_for_universe(company_data, all_companies=dax_data)
            
            for row in new_rows:
                key = (row["Company_Name"], row["Email_Address"])
                if key not in existing_keys:
                    all_rows.append(row)
                    existing_keys.add(key)
            
            # Incremental save
            with open(OUTPUT_FILE, 'w') as f:
                json.dump(all_rows, f, indent=2)
                
        except Exception as e:
            print(f"  [Error] Failed to process {company_data.get('name')}: {e}")
    
    # Final validation: ensure no blank Email_Address or First_Name
    valid_rows = [r for r in all_rows if r.get("Email_Address") and r.get("First_Name")]
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(valid_rows, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"COMPLETE: {len(valid_rows)} valid rows in {OUTPUT_FILE}")
    print(f"Removed {len(all_rows) - len(valid_rows)} rows with blank Email/First_Name")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
