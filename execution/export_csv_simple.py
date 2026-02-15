import json
import csv
import os
import argparse
from dotenv import load_dotenv
from supabase import create_client

# Load env vars
load_dotenv()

def export_csv_legacy():
    client_slug = "pulsepoint_strategic"
    input_file = f"{client_slug}/leads/leads.json"
    output_path = os.path.expanduser(f"~/Desktop/PULSEPOINT_STRATEGIC_leads_legacy.csv")

    try:
        with open(input_file, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Could not find {input_file}")
        return

    headers = [
        "Company", "Event Type", "Event Title", "Event Context", "Source URL",
        "Contact Name", "Title", "Email", "Subject", "Body"
    ]

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for company in data.get("companies", []):
            c_name = company.get("name")
            e_type = company.get("event_type")
            e_title = company.get("event_title")
            e_context = company.get("event_context")
            e_url = company.get("event_source_url")

            for contact in company.get("contacts", []):
                row = [
                    c_name,
                    e_type,
                    e_title,
                    e_context,
                    e_url,
                    contact.get("name"),
                    contact.get("title"),
                    contact.get("email"),
                    contact.get("email_subject"),
                    contact.get("email_body")
                ]
                writer.writerow(row)

    print(f"✅ Exported LEGACY CSV to {output_path}")

def export_csv_supabase():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    supabase = create_client(url, key)
    output_path = os.path.expanduser(f"~/Desktop/PULSEPOINT_STRATEGIC_leads_ranked.csv")
    
    print("⏳ Fetching ranked leads from Supabase...")
    
    # Fetch leads with related company info
    # Note: Supabase-py join syntax can be tricky.
    # Alternative: Fetch all leads, then fetch companies, or use a view.
    # Since we need to join, let's try a simple join query.
    # "leads" table is PULSEPOINT_STRATEGIC_TRIGGERED_LEADS
    
    leads_table = "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS"
    
    # Select all leads, ordered by deal_score DESC
    resp = supabase.table(leads_table).select("*, triggered_companies(company, event_type, event_title)").order("deal_score", desc=True).execute()
    leads = resp.data
    
    if not leads:
        print("⚠️ No leads found in Supabase.")
        return

    headers = [
        "Deal Score", "Company", "Signal Type", "Date", "Why Now", 
        "Confidence", "Quote", "Source URL", 
        "Contact Name", "Title", "Email", "Contact Status"
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for l in leads:
            # Handle joined company data
            # Supabase returns joined data as a nested dict or list?
            # Usually nested dict if 1:1 or N:1.
            comp = l.get("triggered_companies") or {}
            company_name = comp.get("company", "Unknown") if isinstance(comp, dict) else "Unknown"
            
            row = [
                l.get("deal_score", 0),
                company_name,
                l.get("signal_type", ""),
                l.get("signal_date", ""),
                l.get("why_now", ""),
                l.get("confidence_score", 0),
                l.get("evidence_quote", ""),
                l.get("source_url", ""),
                l.get("name", ""),
                l.get("title", ""),
                l.get("email", ""),
                l.get("contact_status", "")
            ]
            writer.writerow(row)
            
    print(f"✅ Exported RANKED CSV to {output_path} ({len(leads)} leads)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export PulsePoint Leads")
    parser.add_argument("--source", choices=["json", "supabase"], default="json", help="Source of data (json=legacy, supabase=ranked)")
    args = parser.parse_args()
    
    if args.source == "json":
        export_csv_legacy()
    else:
        export_csv_supabase()
