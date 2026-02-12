import json
import argparse
import os

def find_emails(client_slug):
    file_path = f"{client_slug}/leads/enriched_contacts.json"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r') as f:
        contacts = json.load(f)

    for contact in contacts:
        if contact.get('email'):
            continue
        
        name = contact.get('contact_name', '')
        website = contact.get('website', '')
        
        if not name or not website:
            contact['verification_status'] = 'missing_info'
            continue
            
        # Basic Clean
        website = website.lower().replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
        
        parts = name.lower().split()
        if len(parts) >= 2:
            first = parts[0]
            last = parts[-1]
            
            # Pattern Guessing: first.last@domain.com
            email = f"{first}.{last}@{website}"
            contact['email'] = email
            contact['verification_status'] = 'pattern_guessed'
            print(f"Guessed email for {name}: {email}")
        else:
            contact['verification_status'] = 'name_format_error'

    with open(file_path, 'w') as f:
        json.dump(contacts, f, indent=2)
    
    print(f"Updated {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", help="Client slug (e.g. pulsepoint_strategic)", default="pulsepoint_strategic")
    args = parser.parse_args()
    
    find_emails(args.client)
