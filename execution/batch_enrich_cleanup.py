"""
Batch enrichment script for accounts without contacts.
Runs enrichment for each, then cleans up unenrichable accounts.

Usage:
    python batch_enrich_cleanup.py --client pulsepoint_strategic
    python batch_enrich_cleanup.py --client mike_ecker
"""
import os
import sys
import re
import requests
import time
import argparse
from dotenv import load_dotenv
from supabase import create_client
from apify_client import ApifyClient

# Make shared module importable
sys.path.insert(0, os.path.dirname(__file__))
from shared.enrichment_utils import (
    is_valid_full_name, normalize_company, company_matches,
    find_website, find_decision_makers, verify_email,
    is_junk_company_name, JUNK_COMPANY_NAMES
)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
APIFY_TOKEN = os.environ.get('APIFY_API_KEY')
ANYMAILFINDER_KEY = os.environ.get('ANYMAILFINDER_API_KEY')

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
apify = ApifyClient(APIFY_TOKEN)


def resolve_leads_table(client_context: str) -> str:
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
        print(f"⚠️ Could not resolve leads table: {e}")
    return f"{client_context.upper()}_TRIGGERED_LEADS"


def run_batch_enrichment(client_context: str):
    """Run batch enrichment and cleanup for a given client."""
    leads_table = resolve_leads_table(client_context)

    print("=" * 60)
    print(f"BATCH ENRICHMENT — {client_context}")
    print(f"Leads table: {leads_table}")
    print("=" * 60)

    # Get companies without contacts
    companies = supabase.table('triggered_companies')\
        .select('*')\
        .eq('client_context', client_context)\
        .execute().data

    leads = supabase.table(leads_table)\
        .select('triggered_company_id')\
        .execute().data

    company_ids_with_contacts = set(l['triggered_company_id'] for l in leads)
    companies_to_process = [c for c in companies if c['id'] not in company_ids_with_contacts]

    print(f"\nCompanies without contacts: {len(companies_to_process)}")

    stats = {
        "processed": 0,
        "enriched": 0,
        "failed": 0,
        "skipped_junk": 0,
        "deleted": 0
    }

    companies_to_delete = []

    for comp in companies_to_process:
        company_name = comp.get('company', '').strip()
        company_id = comp['id']

        print(f"\n{'='*40}")
        print(f"Processing: {company_name}")

        # Skip junk names
        if is_junk_company_name(company_name):
            print(f"  ⛔ JUNK NAME - will delete")
            companies_to_delete.append(company_id)
            stats["skipped_junk"] += 1
            continue

        stats["processed"] += 1

        # Get or find website
        domain = comp.get('website')
        if not domain:
            domain = find_website(company_name, apify)
            if domain:
                supabase.table("triggered_companies").update({"website": domain}).eq("id", company_id).execute()

        if not domain:
            print(f"  ❌ No website found - will delete")
            companies_to_delete.append(company_id)
            stats["failed"] += 1
            continue

        # Skip .gov domains (not ICP)
        if '.gov' in domain:
            print(f"  ⛔ Government domain ({domain}) - will delete")
            companies_to_delete.append(company_id)
            stats["failed"] += 1
            continue

        print(f"  Website: {domain}")

        # Find decision makers
        candidates = find_decision_makers(company_name, apify)
        print(f"  Found {len(candidates)} candidates")

        if not candidates:
            print(f"  ❌ No decision makers found - will delete")
            companies_to_delete.append(company_id)
            stats["failed"] += 1
            continue

        # Verify emails
        contacts_added = 0
        for person in candidates:
            email = verify_email(person['name'], domain, api_key=ANYMAILFINDER_KEY)
            if email:
                print(f"  ✅ {person['name']} <{email}>")
                try:
                    supabase.table(leads_table).insert({
                        "triggered_company_id": company_id,
                        "name": person['name'],
                        "title": person['title'],
                        "email": email,
                        "linkedin_url": person['linkedin'],
                        "contact_status": "pending"
                    }).execute()
                    contacts_added += 1
                except Exception as e:
                    print(f"  ⚠️ Insert error: {e}")
            else:
                print(f"  ❌ No email: {person['name']}")

        if contacts_added > 0:
            print(f"  ✅ ENRICHED: {contacts_added} contacts")
            stats["enriched"] += 1
        else:
            print(f"  ❌ No verified emails - will delete")
            companies_to_delete.append(company_id)
            stats["failed"] += 1

        time.sleep(1)

    # Delete unenrichable companies
    print(f"\n{'='*60}")
    print(f"CLEANUP: Deleting {len(companies_to_delete)} unenrichable companies")
    print("=" * 60)

    for cid in companies_to_delete:
        try:
            supabase.table(leads_table).delete().eq("triggered_company_id", cid).execute()
            resp = supabase.table("triggered_companies").delete().eq("id", cid).execute()
            if resp.data:
                print(f"  🗑️ Deleted: {resp.data[0].get('company', cid)}")
                stats["deleted"] += 1
        except Exception as e:
            print(f"  ⚠️ Delete error for {cid}: {e}")

    print(f"\n{'='*60}")
    print(f"BATCH ENRICHMENT COMPLETE — {client_context}")
    print("=" * 60)
    print(f"  Processed: {stats['processed']}")
    print(f"  Enriched: {stats['enriched']}")
    print(f"  Failed/Deleted: {stats['failed']}")
    print(f"  Junk Deleted: {stats['skipped_junk']}")
    print(f"  Total Deleted: {stats['deleted']}")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch enrich and cleanup accounts")
    parser.add_argument("--client", default="pulsepoint_strategic",
                        help="Client context slug (default: pulsepoint_strategic)")
    args = parser.parse_args()
    run_batch_enrichment(args.client)

