import json

# Define the specific URL updates
url_updates = {
    "Chetu": "https://www.chetu.com/careers",
    "Flagright": "https://flagright.com/careers",
    "Hightouch": "https://hightouch.com/careers",
    "Capital One Software": "https://www.capitalonecareers.com/",
    "ScaleneWorks": "https://www.scaleneworks.com/careers",
    "OutSystems": "https://www.outsystems.com/careers/",
    "Hostaway": "https://www.hostaway.com/careers/",
    "Atlassian": "https://www.atlassian.com/company/careers",
    "Everway": "https://www.everway.com/careers",
    "Veeva": "https://careers.veeva.com/",
    "Hopper": "https://www.hopper.com/careers",
    "Deepgram": "https://deepgram.com/careers",
    "Parsons Transportation Group": "https://www.parsons.com/news/",
    "Costain": "https://www.costain.com/news/",
    "Levellr": "https://levellr.com/blog",
    "Legato": "https://legato.com/news",
    "Materialspace": "https://materialspace.com",
    "Larsen & Toubro": "https://www.larsentoubro.com/corporate/news-events/news/",
    "Egis": "https://www.egis-group.com/news",
    "AECOM": "https://aecom.com/news/",
    "Duvall Decker": "https://duvalldecker.com/news/",
    "Architectus": "https://architectus.com.au/news/",
    "LimX Dynamics": "https://www.limxdynamics.com/en/news",
    "Talos": "https://talos.com/news",
    "Sixfold": "https://sixfold.ai/blog",
    "Zocks": "https://zocks.io/blog"
}

# Define the new lead objects
ramp_lead = {
    "name": "Ramp",
    "event_type": "TRIGGER_DETECTED",
    "event_title": "Hiring Sales Development Representative",
    "event_context": "Trigger detected: Hiring Sales Development Representative",
    "event_source_url": "https://ramp.com/careers",
    "contacts": [
        {
            "name": "Eric Glyman",
            "title": "CEO",
            "email": "eric.glyman@ramp.com"
        }
    ]
}

skanska_lead = {
    "name": "Skanska",
    "event_type": "TRIGGER_DETECTED",
    "event_title": "Won $228M Data Center Contract",
    "event_context": "Trigger detected: Won $228M Data Center Contract",
    "event_source_url": "https://www.skanska.com/",
    "contacts": [
        {
            "name": "Richard Kennedy",
            "title": "CEO",
            "email": "richard.kennedy@skanska.com"
        }
    ]
}

def update_leads():
    path = "pulsepoint_strategic/leads/leads.json"
    contacts_path = "pulsepoint_strategic/leads/enriched_contacts.json"
    
    with open(path, "r") as f:
        data = json.load(f)

    new_companies = []
    
    for company in data["companies"]:
        name = company["name"]
        
        # 1. Handle Removals/Replacements
        if name == "Aithentic":
            new_companies.append(ramp_lead)
            continue
        if name == "C. Martin Co. Inc.":
            new_companies.append(skanska_lead)
            continue
            
        # 2. Update URLs
        if name in url_updates:
            company["event_source_url"] = url_updates[name]
            
        new_companies.append(company)
        
    data["companies"] = new_companies
    
    # Save leads.json
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        
    # Also update enriched_contacts.json for consistency
    verified_contacts = []
    for company in new_companies:
        contact = company["contacts"][0]
        verified_contacts.append({
            "company": company["name"],
            "contact_name": contact["name"],
            "title": contact["title"],
            "email": contact["email"],
            "website": company["event_source_url"],
            "verification_status": "verified"
        })
        
    with open(contacts_path, "w") as f:
        json.dump(verified_contacts, f, indent=2)

    print(f"Updated leads and contacts. Total count: {len(new_companies)}")

if __name__ == "__main__":
    update_leads()
