import json
import csv
import os
import argparse
import uuid
import datetime

def generate_company_uuid(seed_string: str) -> str:
    """Generate deterministic UUID from a seed string (must much export_client_leads.py)."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed_string))

def export_companies_csv():
    client_slug = "pulsepoint_strategic"
    input_file = f"{client_slug}/leads/leads.json"
    output_path = os.path.expanduser(f"~/Desktop/PULSEPOINT_STRATEGIC_companies.csv")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Columns: id, company, event_type, event_title, event_context, event_source_url, created_at
    headers = [
        "id", "company", "event_type", "event_title", "event_context", 
        "event_source_url", "created_at"
    ]

    current_time = datetime.datetime.now().isoformat()

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for company in data.get("companies", []):
            company_name = company.get("name")
            company_id = generate_company_uuid(company_name)
            
            row = [
                company_id,                             # id
                company_name,                           # company
                company.get("event_type", ""),          # event_type
                company.get("event_title", ""),         # event_title
                company.get("event_context", ""),       # event_context
                company.get("event_source_url", ""),    # event_source_url
                current_time                            # created_at
            ]
            writer.writerow(row)

    print(f"Exported Companies CSV to {output_path}")

if __name__ == "__main__":
    export_companies_csv()
