import json
import csv
import os
import argparse
import uuid
import datetime

def generate_company_uuid(seed_string: str) -> str:
    """Generate deterministic UUID from a seed string (must match export_client_leads.py)."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, seed_string))

def export_csv_supabase_format():
    client_slug = "pulsepoint_strategic"
    input_file = f"{client_slug}/leads/leads.json"
    output_path = os.path.expanduser(f"~/Desktop/PULSEPOINT_STRATEGIC_leads_supabase.csv")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Columns based on MIKE_ECKER_TRIGGERED_LEADS_rows (1).csv
    headers = [
        "id", "triggered_company_id", "name", "title", "email", "contact_status", 
        "email_subject", "email_body", "thread_id", "last_message_id", "last_sent_at", 
        "nudge_count", "next_nudge_at", "replied_at", "bounced_at", "is_selected", 
        "created_at", "updated_at", "linkedin_url", "linkedin_profile_picture_url", 
        "last_linkedin_interaction_at", "video_pitch_sent", "linkedin_comment_draft", 
        "video_script", "loom_link", "intent_score"
    ]

    current_time = datetime.datetime.now().isoformat()

    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        for company in data.get("companies", []):
            company_name = company.get("name")
            # Generate deterministic UUID for company to match the SQL seed
            company_id = generate_company_uuid(company_name)

            for contact in company.get("contacts", []):
                # Unique ID for each lead
                lead_id = str(uuid.uuid4())
                
                row = [
                    lead_id,                                # id
                    company_id,                             # triggered_company_id
                    contact.get("name"),                    # name
                    contact.get("title"),                   # title
                    contact.get("email"),                   # email
                    "pending",                              # contact_status
                    contact.get("email_subject"),           # email_subject
                    contact.get("email_body"),              # email_body
                    "",                                     # thread_id
                    "",                                     # last_message_id
                    "",                                     # last_sent_at
                    "0",                                    # nudge_count
                    "",                                     # next_nudge_at
                    "",                                     # replied_at
                    "",                                     # bounced_at
                    "true",                                 # is_selected
                    current_time,                           # created_at
                    current_time,                           # updated_at
                    "",                                     # linkedin_url
                    "",                                     # linkedin_profile_picture_url
                    "",                                     # last_linkedin_interaction_at
                    "false",                                # video_pitch_sent
                    "",                                     # linkedin_comment_draft
                    "",                                     # video_script
                    "",                                     # loom_link
                    "MEDIUM"                                # intent_score
                ]
                writer.writerow(row)

    print(f"Exported Supabase-compatible CSV to {output_path}")

if __name__ == "__main__":
    export_csv_supabase_format()
