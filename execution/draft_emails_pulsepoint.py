import json
import os

def draft_emails():
    leads_path = "pulsepoint_strategic/leads/leads.json"
    contacts_path = "pulsepoint_strategic/leads/enriched_contacts.json"
    
    with open(leads_path, 'r') as f:
        leads_data = json.load(f)
        
    with open(contacts_path, 'r') as f:
        contacts_list = json.load(f)
        contacts_map = {c['company']: c for c in contacts_list}

    processed_count = 0
    cohort_a_count = 0
    cohort_b_count = 0

    for company in leads_data.get("companies", []):
        company_name = company.get("name")
        contact_info = contacts_map.get(company_name)
        
        if not contact_info:
            print(f"Skipping {company_name}: No contact info")
            continue
            
        first_name = contact_info['contact_name'].split()[0]
        event_title = company.get("event_title", "")
        
        # Determine Cohort based on Event Title
        is_hiring = "Hiring" in event_title
        
        # STRATEGY A: HIRING (Replacement)
        if is_hiring:
            role_hiring = event_title.replace("Hiring ", "")
            subject_line = f"USC Student / Alternative to your {role_hiring} hire"
            email_body = f"""Hi {first_name},

I’m a student at USC studying automation.

I saw you are hiring for a {role_hiring} to grind out outreach. My system actually found that job post automatically—which is exactly how I found you.

I built a "Sniper Engine" that listens for buying signals (like your hiring post) and instantly drafts the outreach for you.

Basically, it automates the 3 hours of research a human SDR does, so you just have to click "Approve." It gives you the output of 2 reps for 1/10th the cost.

I’m not trying to sell a subscription. I just want to show a founder how to replace "Spray and Pray" with "Sniper Operations."

Mind if I send a 60-second Loom showing the backend?

Best,
Ty"""
            cohort_a_count += 1

        # STRATEGY B: PROJECT WIN / FUNDING (Growth Partner)
        else:
            # Clean up the project name from the event title
            project_name = event_title
            
            # Use specific "Project Name" formatting for clearer emails
            if "Won" in project_name:
                project_name = project_name.replace("Won ", "")
            
            subject_line = f"Your {project_name} case study"
            email_body = f"""Hi {first_name},

I’m a student at USC studying automation.

I saw the announcement for {project_name} and wanted to reach out—congratulations.

I’ve been studying high-end firms and noticed a specific bottleneck: sustaining the momentum from a "flagship win" usually requires bloating your sales overhead to find the next one.

My partner and I built a "Sniper Engine" to fix this.

It scans for market signals to time outreach perfectly. In fact, my system flagged your project this morning—which is exactly how I found you.

I’m not trying to sell a subscription. I just want to show you how this same engine can identify developers who need exactly what you just delivered.

Mind if I run a quick scan and send you a list of 5 companies that fit that criteria?

Best, 
Ty"""
            cohort_b_count += 1

        # Populate Contact Data
        company["contacts"] = [{
            "name": contact_info['contact_name'],
            "title": contact_info['title'],
            "email": contact_info['email'],
            "email_subject": subject_line,
            "email_body": email_body
        }]
        processed_count += 1

    # Save updated leads.json
    with open(leads_path, 'w') as f:
        json.dump(leads_data, f, indent=2)
        
    print(f"COMPLETE: Drafted {processed_count} emails.")
    print(f"Cohort A (Hiring): {cohort_a_count}")
    print(f"Cohort B (Wins):   {cohort_b_count}")

if __name__ == "__main__":
    draft_emails()
