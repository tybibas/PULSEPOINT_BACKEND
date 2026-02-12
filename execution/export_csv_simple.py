import json
import csv
import os
import argparse

def export_csv():
    client_slug = "pulsepoint_strategic"
    input_file = f"{client_slug}/leads/leads.json"
    output_path = os.path.expanduser(f"~/Desktop/PULSEPOINT_STRATEGIC_leads.csv")

    with open(input_file, 'r') as f:
        data = json.load(f)

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

    print(f"Exported CSV to {output_path}")

if __name__ == "__main__":
    export_csv()
