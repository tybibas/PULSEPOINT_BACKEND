#!/usr/bin/env python3
"""
Export Ecker Design Co. leads to CSV for Supabase import.

Matches schema: public."MIKE_ECKER_TRIGGERED_LEADS"

Note: triggered_company_id is a foreign key to triggered_companies table.
You'll need to create entries in triggered_companies first, then use those IDs here.
"""

import csv
import uuid
import os
from datetime import datetime

# Output path
OUTPUT_CSV = "/Users/tybibas/Desktop/MIKEECKER.csv"

# Generate deterministic UUIDs for companies (so they can be referenced)
# In production, these would come from the triggered_companies table
COMPANY_UUIDS = {
    "Longfellow Real Estate Partners": str(uuid.uuid5(uuid.NAMESPACE_DNS, "longfellow.lfrep.com")),
    "Carrier Johnson + Culture": str(uuid.uuid5(uuid.NAMESPACE_DNS, "carrierjohnson.com")),
    "Trammell Crow Company": str(uuid.uuid5(uuid.NAMESPACE_DNS, "trammellcrow.com")),
}

# Lead data from enrichment
LEADS = [
    # Longfellow Real Estate Partners
    {
        "company": "Longfellow Real Estate Partners",
        "name": "Peter Fritz",
        "title": "Managing Director, San Diego",
        "email": "pfritz@lfrep.com",
        "email_subject": "Making SOVA the Campus Everyone Wants to Visit",
        "email_body": """Hi Peter,

Saw that Centerpark Labs just won Life Science Campus of the Year – congrats to the whole team. Creating award-winning spaces is no small feat.

As you continue shaping projects like SOVA and Bioterra, I wanted to share how hand-painted murals are helping similar campuses become destinations, not just buildings. We've been working with commercial developers across San Diego to create lobby experiences that tenants actually take photos in front of.

I have some quick concepts for how environmental art could elevate your tenant amenity spaces. Would it be useful to see a mood board tailored to your project's vibe?

Cheers,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Longfellow Real Estate Partners",
        "name": "Brandon Maddox",
        "title": "Senior Project Manager",
        "email": "bmaddox@lfrep.com",
        "email_subject": "Making SOVA the Campus Everyone Wants to Visit",
        "email_body": """Hi Brandon,

Saw that Centerpark Labs just won Life Science Campus of the Year – congrats to the whole team. Creating award-winning spaces is no small feat.

As you continue shaping projects like SOVA and Bioterra, I wanted to share how hand-painted murals are helping similar campuses become destinations, not just buildings. We've been working with commercial developers across San Diego to create lobby experiences that tenants actually take photos in front of.

I have some quick concepts for how environmental art could elevate your tenant amenity spaces. Would it be useful to see a mood board tailored to SOVA's vibe?

Cheers,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Longfellow Real Estate Partners",
        "name": "Eric Hotovy",
        "title": "Project Executive",
        "email": "ehotovy@lfrep.com",
        "email_subject": "Art That Meets Your Construction Timeline",
        "email_body": """Hi Eric,

With Bioterra hitting completion as San Diego's first all-electric life science building, you're setting a new standard for sustainability and design.

As Project Executive, you know that the "finish line" is really about tenant experience. We create hand-painted murals and environmental graphics that turn sustainable spaces into vibrant destinations.

Think original art that highlights the building's mission – installed on your schedule, not an artist's schedule.

I'd love to share some examples of how we've helped similar green developments create spaces tenants remember. Worth a quick call?

Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Longfellow Real Estate Partners",
        "name": "Daniel Mejia",
        "title": "Senior Project Manager",
        "email": "dmejia@lfrep.com",
        "email_subject": "Making SOVA the Campus Everyone Wants to Visit",
        "email_body": """Hi Daniel,

Saw that Centerpark Labs just won Life Science Campus of the Year – congrats to the whole team. Creating award-winning spaces is no small feat.

As you continue shaping projects like SOVA and Bioterra, I wanted to share how hand-painted murals are helping similar campuses become destinations, not just buildings. We've been working with commercial developers across San Diego to create lobby experiences that tenants actually take photos in front of.

I have some quick concepts for how environmental art could elevate your tenant amenity spaces. Would it be useful to see a mood board tailored to your current projects?

Cheers,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Longfellow Real Estate Partners",
        "name": "Nick Frasco",
        "title": "Partner, West Region",
        "email": "nfrasco@lfrep.com",
        "email_subject": "Art That Drives Leasing Velocity",
        "email_body": """Hi Nick,

As Partner overseeing West Region operations for Longfellow, you're shaping some of the most exciting life science campuses in San Diego.

I wanted to share how hand-painted murals are helping developers like you differentiate in a competitive leasing market. A signature mural in the lobby becomes the photo op, the conversation starter, the thing prospective tenants remember.

With your portfolio of SOVA, Bioterra, and Biovista, there's real opportunity to create spaces that set the standard for the region.

Would a quick mood board for one of your properties be useful?

Best,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    
    # Carrier Johnson + Culture
    {
        "company": "Carrier Johnson + Culture",
        "name": "Jackie Angel",
        "title": "Principal & Director of Operations",
        "email": "jangel@carrierjohnson.com",
        "email_subject": "A Go-To Partner for Custom Environmental Art",
        "email_body": """Hi Jackie,

With the recent leadership transition and focus on strategic growth, it feels like an exciting new chapter for Carrier Johnson.

I run Ecker Design Co., and we do hand-painted murals and environmental graphics for commercial and educational spaces. As Director of Operations, having reliable creative partners who deliver on time and budget is key.

Rather than sourcing existing art or managing individual artists, we offer a turnkey solution for original, site-specific pieces.

Would it be useful to have a go-to for hand-crafted environmental art? I'd love to share our portfolio and discuss how we could support your teams.

Cheers,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Carrier Johnson + Culture",
        "name": "David Huchteman",
        "title": "Chief Executive Officer",
        "email": "deh@carrierjohnson.com",
        "email_subject": "Custom Murals That Elevate Your Design Vision",
        "email_body": """Hi David,

Congratulations on your appointment as CEO. It's an exciting time for Carrier Johnson as you lead the firm's next chapter in San Diego and beyond.

As you set the strategic direction, I wanted to introduce Ecker Design Co. We create hand-painted murals and custom environmental graphics for commercial and institutional spaces.

Unlike sign shops or art consultants sourcing existing work, we design and execute original pieces tailored to each project's architecture and brand story.

I'd love to show you some examples of how we've helped architects translate design intent into memorable moments. Worth a quick conversation?

Best,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Carrier Johnson + Culture",
        "name": "Claudia Escala",
        "title": "Co-President",
        "email": "cescala@carrierjohnson.com",
        "email_subject": "A Creative Partner for Your Commercial Projects",
        "email_body": """Hi Claudia,

Congratulations on the Co-President role. The firm's work shaping San Diego's commercial architecture continues to impress.

I run Ecker Design Co., and we specialize in hand-painted murals and environmental graphics for commercial and educational spaces. We often partner with architecture firms to specify custom art that becomes the signature moment of a building.

Rather than sourcing existing art, we create original, site-specific pieces – and we deliver on schedule, which I know matters as much as the design.

I'd love to share our portfolio and explore how we might support your upcoming projects. Worth a quick call?

Cheers,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    {
        "company": "Carrier Johnson + Culture",
        "name": "Marin Gertler",
        "title": "Chief Design Officer",
        "email": "mgertler@carrierjohnson.com",
        "email_subject": "Custom Murals That Elevate Your Design Vision",
        "email_body": """Hi Marin,

Congratulations on being named Chief Design Officer. It's fantastic to see the focus on design leadership at Carrier Johnson.

We create hand-painted murals and custom environmental graphics for commercial and institutional spaces. Unlike sign shops or art consultants sourcing existing work, we design and execute original pieces tailored to each project's architecture and brand story.

I'd love to show you some examples of how we've helped architects translate design intent into memorable moments within their buildings. Worth a quick conversation?

Best,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
    
    # Trammell Crow Company
    {
        "company": "Trammell Crow Company",
        "name": "Christopher Tipre",
        "title": "Principal, San Diego",
        "email": "ctipre@trammellcrow.com",
        "email_subject": "Art That Accelerates Leasing",
        "email_body": """Hi Christopher,

I saw that Vista Sorrento Labs is officially complete – congrats on delivering TCC's first ground-up life science project in the county.

As you look to lease up that space and plan future developments, I wanted to share how hand-painted murals are helping developers differentiate in a competitive market. A signature lobby mural becomes the photo op, the conversation starter, and the thing prospective tenants remember.

I've seen it work for other Class A life science projects. Worth a quick call to share some examples?

Best,
Mike Ecker
Ecker Design Co.
eckerdesignco.com""",
    },
]

# CSV columns matching Supabase schema (EXACT MATCH to reference)
CSV_COLUMNS = [
    "id",
    "triggered_company_id",
    "name",
    "title",
    "email",
    "contact_status",
    "email_subject",
    "email_body",
    "thread_id",
    "last_message_id",
    "last_sent_at",
    "nudge_count",
    "next_nudge_at",
    "replied_at",
    "bounced_at",
    "is_selected",
    "created_at",
    "updated_at",
    "linkedin_url",
    "linkedin_profile_picture_url",
    "last_linkedin_interaction_at",
    "video_pitch_sent",
    "linkedin_comment_draft",
    "video_script",
    "loom_link"
]

def main():
    print("=" * 60)
    print("EXPORTING LEADS TO SUPABASE CSV")
    print("=" * 60)
    
    rows = []
    
    for lead in LEADS:
        company = lead["company"]
        company_id = COMPANY_UUIDS.get(company, str(uuid.uuid4()))
        
        # Populate row with defaults for missing fields to match schema
        row = {
            "id": str(uuid.uuid4()),
            "triggered_company_id": company_id,
            "name": lead["name"],
            "title": lead.get("title", ""),
            "email": lead["email"],
            "contact_status": "pending",
            "email_subject": lead.get("email_subject", ""),
            "email_body": lead.get("email_body", ""),
            
            # Empty/Default fields
            "thread_id": "",
            "last_message_id": "",
            "last_sent_at": "",
            "nudge_count": "0",
            "next_nudge_at": "",
            "replied_at": "",
            "bounced_at": "",
            "is_selected": "true",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "linkedin_url": "",
            "linkedin_profile_picture_url": "",
            "last_linkedin_interaction_at": "",
            "video_pitch_sent": "false",
            "linkedin_comment_draft": "",
            "video_script": "",
            "loom_link": ""
        }
        rows.append(row)
        print(f"  ✓ {lead['name']} ({lead['email']})")
    
    # Write CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n{'='*60}")
    print(f"✓ Exported {len(rows)} leads to: {OUTPUT_CSV}")
    print(f"{'='*60}")
    
    # Also print the company UUIDs for triggered_companies table reference
    print("\n⚠️  IMPORTANT: SQL IMPORT RECOMMENDED (seed_mike_ecker_data.sql)") 
    print("   If using CSV, ensure companies exist first.")

if __name__ == "__main__":
    main()
