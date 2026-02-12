#!/usr/bin/env python3
"""
Client Leads Export Script

Generates Supabase-compatible SQL seed file for a new client's leads.
This script is called at the end of the client onboarding process.

USAGE:
    python export_client_leads.py --client "ACME_CORP" --input leads.json --output ~/Desktop/

INPUT FORMAT (leads.json):
    {
        "client_name": "Acme Corp",
        "companies": [
            {
                "name": "Target Company Inc",
                "event_type": "FUNDING",
                "event_title": "Series B Announced",
                "event_context": "Raised $50M to expand operations.",
                "event_source_url": "https://example.com/news",
                "contacts": [
                    {
                        "name": "John Smith",
                        "title": "CEO",
                        "email": "john@targetcompany.com",
                        "email_subject": "Congrats on the Series B",
                        "email_body": "Hi John,\\n\\nSaw the news about..."
                    }
                ]
            }
        ]
    }
"""

import argparse
import json
import uuid
import os
from datetime import datetime


def generate_uuid(seed_string: str) -> str:
    """Generate deterministic UUID from a seed string."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed_string))


def escape_sql(text: str) -> str:
    """Escape single quotes for SQL."""
    if text is None:
        return ""
    return text.replace("'", "''")


def generate_sql(client_name: str, data: dict) -> str:
    """Generate SQL seed file content."""
    
    table_name = f"{client_name.upper().replace(' ', '_')}_TRIGGERED_LEADS"
    
    sql_parts = []
    sql_parts.append(f"-- {client_name.upper()} - SEED DATA")
    sql_parts.append(f"-- Generated: {datetime.now().isoformat()}")
    sql_parts.append("-- Run this in the Supabase SQL Editor.\n")
    sql_parts.append("BEGIN;\n")
    
    # Collect all companies and leads
    company_inserts = []
    lead_inserts = []
    
    for company in data.get("companies", []):
        company_id = generate_uuid(company["name"])
        
        # Company insert
        company_inserts.append(f"""    (
        '{company_id}', 
        '{escape_sql(company["name"])}', 
        '{escape_sql(company.get("event_type", ""))}', 
        '{escape_sql(company.get("event_title", ""))}', 
        '{escape_sql(company.get("event_context", ""))}', 
        '{escape_sql(company.get("event_source_url", ""))}',
        NOW()
    )""")
        
        # Lead inserts for this company
        for contact in company.get("contacts", []):
            lead_inserts.append(f"""    (
        '{company_id}', 
        '{escape_sql(contact["name"])}', 
        '{escape_sql(contact.get("title", ""))}', 
        '{escape_sql(contact["email"])}', 
        'pending',
        '{escape_sql(contact.get("email_subject", ""))}', 
        '{escape_sql(contact.get("email_body", ""))}', 
        true,
        NOW(),
        NOW()
    )""")
    
    # Companies section
    sql_parts.append("-- 1. INSERT COMPANIES")
    sql_parts.append("-" * 80)
    sql_parts.append("""INSERT INTO public.triggered_companies (
    id, 
    company, 
    event_type, 
    event_title, 
    event_context, 
    event_source_url, 
    created_at
)
VALUES""")
    sql_parts.append(",\n".join(company_inserts))
    sql_parts.append("ON CONFLICT (id) DO UPDATE SET event_title = EXCLUDED.event_title;\n")
    
    # Leads section
    sql_parts.append(f"-- 2. INSERT LEADS INTO {table_name}")
    sql_parts.append("-" * 80)
    sql_parts.append(f"""INSERT INTO public."{table_name}" (
    triggered_company_id, 
    name, 
    title, 
    email, 
    contact_status, 
    email_subject, 
    email_body, 
    is_selected,
    created_at,
    updated_at
)
VALUES""")
    sql_parts.append(",\n".join(lead_inserts))
    sql_parts.append("""ON CONFLICT (triggered_company_id, email) DO UPDATE
SET 
  email_subject = EXCLUDED.email_subject,
  email_body = EXCLUDED.email_body,
  updated_at = NOW();\n""")
    
    sql_parts.append("COMMIT;")
    
    return "\n".join(sql_parts)


def generate_bolt_prompt(client_name: str, table_name: str, lead_count: int) -> str:
    """Generate the Bolt prompt for dashboard wiring."""
    return f"""## Bolt Prompt: Wire {client_name} Dashboard

**Goal:** Connect the "Triggered" tab to the new `{table_name}` table.

**Critical Safety Rules:**
- DO NOT DELETE any existing tables or data.
- DO NOT MODIFY the original `triggered_company_contacts` table.
- Disconnect old references and reconnect to the new table below.

**Table Name:** `{table_name}`

**Schema:** Same as `MIKE_ECKER_TRIGGERED_LEADS`:
- triggered_company_id (uuid, FK to triggered_companies.id)
- name, title, email (text)
- contact_status (text: pending/sent/replied/bounced)
- email_subject, email_body (text)
- is_selected (boolean)
- created_at, updated_at (timestamptz)

**What to Wire:**
1. Query `{table_name}` in the "Triggered" tab.
2. Join with `triggered_companies` on `triggered_company_id` for company context.
3. Use `dispatch-batch-ecker` edge function (or duplicate for this client).

**Expected Result:** {lead_count} leads displayed with full email editing and Gmail dispatch.
"""


def main():
    parser = argparse.ArgumentParser(description="Export client leads to Supabase SQL")
    parser.add_argument("--client", required=True, help="Client name (e.g., 'ACME_CORP')")
    parser.add_argument("--input", required=True, help="Path to leads JSON file")
    parser.add_argument("--output", default=os.path.expanduser("~/Desktop"), help="Output directory")
    
    args = parser.parse_args()
    
    # Load input data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    client_name = args.client.upper().replace(" ", "_")
    table_name = f"{client_name}_TRIGGERED_LEADS"
    
    # Count leads
    lead_count = sum(len(c.get("contacts", [])) for c in data.get("companies", []))
    
    # Generate SQL
    sql_content = generate_sql(client_name, data)
    sql_path = os.path.join(args.output, f"{client_name}_seed.sql")
    with open(sql_path, 'w') as f:
        f.write(sql_content)
    print(f"✓ SQL seed file: {sql_path}")
    
    # Generate Bolt prompt
    bolt_content = generate_bolt_prompt(client_name, table_name, lead_count)
    bolt_path = os.path.join(args.output, f"{client_name}_bolt_prompt.md")
    with open(bolt_path, 'w') as f:
        f.write(bolt_content)
    print(f"✓ Bolt prompt: {bolt_path}")
    
    print(f"\n{'='*60}")
    print(f"✓ Exported {lead_count} leads for {client_name}")
    print(f"✓ Table name: {table_name}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
