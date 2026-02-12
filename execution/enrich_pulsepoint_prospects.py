import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------
ANYMAILFINDER_API_KEY = os.environ.get("ANYMAILFINDER_API_KEY")

# List of Prospects (Name, Domain, Decision Maker Name)
PROSPECTS = [
    # Original 5
    {"company": "Design Womb", "domain": "designwomb.com", "name": "Nicole LaFave"},
    {"company": "Mucca Design", "domain": "mucca.com", "name": "Matteo Bologna"},
    {"company": "Jenn David Design", "domain": "jenndavid.com", "name": "Jenn David Connolly"},
    {"company": "B&B Studio", "domain": "bandb-studio.co.uk", "name": "Shaun Bowen"}, # Domain to be verified
    {"company": "Backbone Branding", "domain": "backbonebranding.com", "name": "Stepan Azaryan"},

    # New 15
    {"company": "DD.NYC", "domain": "dd.nyc", "name": "Anjelika Kour"},
    {"company": "Lombardo", "domain": "lombardo.agency", "name": "Giuseppe Lombardo"},
    {"company": "SMAKK Studios", "domain": "smakkstudios.com", "name": "Katie Klencheski"},
    {"company": "Skidmore Studio", "domain": "skidmorestudio.com", "name": "Drew Patrick"},
    {"company": "MAVRK Studio", "domain": "mavrk.studio", "name": "Aaron Swinton"},
    {"company": "Brandettes", "domain": "brandettes.com", "name": "Nikola Cline"},
    {"company": "UMAI Marketing", "domain": "umaimarketing.com", "name": "Alison Smith"},
    {"company": "Swig Studio", "domain": "swigstudio.com", "name": "Kevin Roberson"}, 
    {"company": "Zenpack", "domain": "zenpack.us", "name": "Jeff Lin"},
    {"company": "DePersico Creative", "domain": "depersicocreative.com", "name": "Paul DePersico"},
    {"company": "Stranger & Stranger", "domain": "strangerandstranger.com", "name": "Kevin Shaw"},
    {"company": "Pearlfisher", "domain": "pearlfisher.com", "name": "Jonathan Ford"},
    {"company": "Design Sake Studio", "domain": "designsakestudio.com", "name": "Danielle McWaters"}, 
    {"company": "Grantedesigns", "domain": "grantedesigns.com", "name": "Grant Pogosyan"},
    {"company": "Meghan Mahler Design", "domain": "meghanmahlerdesign.com", "name": "Meghan Mahler"}
]

def find_verified_email(name, domain):
    """
    Uses Anymailfinder to get a verified email for a person at a domain.
    """
    url = "https://api.anymailfinder.com/v5.0/search/person.json"
    headers = {"Authorization": ANYMAILFINDER_API_KEY}
    payload = {"full_name": name, "domain": domain}

    print(f"🔍 Searching for {name} @ {domain}...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # New API structure parsing
        results = data.get('results', {})
        email = results.get('email')
        
        return email
    except Exception as e:
        print(f"❌ Error searching {name}: {e}")
        return None

import uuid

def generate_relational_sql(enriched_leads):
    """
    Generates relational SQL INSERTS for triggered_companies and LEADS.
    """
    company_inserts = []
    lead_inserts = []
    
    # Template
    subject_template = "Scrappy USC student / idea for {company}"
    body_template = """Hi {first_name},

I’m a student at USC studying automation.

I’ve been talking with boutique agency owners and noticed a specific bottleneck: you need to find new clients, but you don't have time for manual research (and mass automation feels too spammy).

My partner and I built a human-in-the-loop AI system to fix this.

It handles the heavy lifting (scanning the market for buying signals and drafting the note), but nothing sends without your approval. It does 90% of the work; you keep 100% of the control.

I'm not trying to sell you another subscription. Just figured seeing a concrete example of how to scale outreach without losing your "founder voice" could be useful clarity for the business.

Mind if I send a 60-second Loom video showing how it works?

Best, 
Ty"""

    print("📝 Generating Relational SQL...")

    for lead in enriched_leads:
        if not lead.get('email'):
            continue
            
        # Generate IDs
        company_id = str(uuid.uuid4())
        
        # Data Prep
        company = lead['company'].replace("'", "''")
        website = lead['domain'].replace("'", "''")
        contact_name = lead['name'].replace("'", "''")
        first_name = contact_name.split()[0]
        email = lead['email'].replace("'", "''")
        
        # 1. Company Insert
        company_inserts.append(f"""    (
        '{company_id}', 
        '{company}', 
        'TRIGGER_DETECTED', 
        'Matched Ideal Customer Profile', 
        'Trigger detected: High-End Packaging Agency Lookalike', 
        'https://{website}',
        NOW()
    )""")
        
        # 2. Lead Insert
        # Fill Template
        body = body_template.format(first_name=first_name, company=company)
        subject = subject_template.format(company=company)
        
        # Escape body for SQL
        body_sql = body.replace("'", "''")
        
        lead_inserts.append(f"""    (
        '{company_id}', 
        '{contact_name}', 
        'Founder/Principal', 
        '{email}', 
        'pending', 
        '{subject}', 
        '{body_sql}', 
        true,
        NOW(),
        NOW()
    )""")

    # Construct Final SQL
    sql_parts = []
    
    sql_parts.append("-- 0. CLEANUP (Delete existing duplicates to avoid double-entry)")
    
    # Get list of emails for deletion
    delete_emails = [f"'{lead['email'].replace("'", "''")}'" for lead in enriched_leads if lead.get('email')]
    if delete_emails:
        sql_parts.append(f"DELETE FROM public.\"PULSEPOINT_STRATEGIC_TRIGGERED_LEADS\" WHERE email IN ({', '.join(delete_emails)});")
        
    # Get list of companies for deletion
    delete_companies = [f"'{lead['company'].replace("'", "''")}'" for lead in enriched_leads]
    if delete_companies:
        sql_parts.append(f"DELETE FROM public.triggered_companies WHERE company IN ({', '.join(delete_companies)});")

    sql_parts.append("")
    sql_parts.append("-- 1. INSERT COMPANIES")
    sql_parts.append("INSERT INTO public.triggered_companies (id, company, event_type, event_title, event_context, event_source_url, created_at)")
    sql_parts.append("VALUES")
    sql_parts.append(",\n".join(company_inserts))
    sql_parts.append("ON CONFLICT (id) DO NOTHING;")
    sql_parts.append("")
    
    sql_parts.append("-- 2. INSERT LEADS")
    sql_parts.append('INSERT INTO public."PULSEPOINT_STRATEGIC_TRIGGERED_LEADS" (triggered_company_id, name, title, email, contact_status, email_subject, email_body, is_selected, created_at, updated_at)')
    sql_parts.append("VALUES")
    sql_parts.append(",\n".join(lead_inserts) + ";")
    
    return "\n".join(sql_parts)

def main():
    enriched_leads = []
    
    # Load cache if available to avoid re-enrichment costs, or just re-run list
    # For speed/simplicity in this context, we re-run the list logic but assume emails are found/not found based on previous run.
    # Actually, we will just re-run the Anymail logic. It's safe.
    
    print(f"🚀 Starting Enrichment for {len(PROSPECTS)} Prospects...")
    
    for prospect in PROSPECTS:
        # Check if we already have it in the internal dict (we don't persist between runs effectively here unless we save to json)
        # But we can just call the API.
        email = find_verified_email(prospect['name'], prospect['domain'])
        if email:
            print(f"   ✅ Found: {email}")
            prospect['email'] = email
            enriched_leads.append(prospect)
        else:
            print(f"   ⚠️ No email found for {prospect['name']}")
    
    # Generate SQL
    if enriched_leads:
        sql_content = generate_relational_sql(enriched_leads)
        
        # Save to file
        output_file = "/Users/tybibas/Desktop/QuantiFire IDE V3/pulsepoint_strategic/import_new_leads.sql"
        with open(output_file, "w") as f:
            f.write(sql_content)
            
        print(f"\n✅ SQL Script generated at: {output_file}")
    else:
        print("\n❌ No eligible leads to import.")

if __name__ == "__main__":
    main()
