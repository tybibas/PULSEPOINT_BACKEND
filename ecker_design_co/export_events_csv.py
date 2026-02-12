#!/usr/bin/env python3
"""
Export Ecker Design Co. Trigger Events to CSV for Supabase import.

Matches schema: public."triggered_events" (implied) or just a raw CSV for import.
Schema assumptions:
- id (uuid)
- triggered_company_id (uuid)
- title (text)
- description (text)
- url (text)
- event_date (date)
- event_type (text)
"""

import csv
import uuid
import os

# Output path
OUTPUT_CSV = "/Users/tybibas/Desktop/mike_ecker_triggered_events.csv"

# Consistent UUIDs from previous step
COMPANY_UUIDS = {
    "Longfellow Real Estate Partners": "13f70ac8-764d-5e9b-a0a7-ce30aa5ee5dc",
    "Carrier Johnson + Culture": "2e6a837a-9c1c-5e66-8635-36c3bbb9c486",
    "Trammell Crow Company": "e917116e-42b0-5a90-87f2-6aff977e814f",
}

EVENTS = [
    {
        "company": "Longfellow Real Estate Partners",
        "title": "Centerpark Labs Named Life Science Campus of the Year",
        "description": "Awarded by San Diego Business Journal for transforming the 256,000 sq ft campus into a premier life science destination.",
        "url": "https://lfrep.com/centerpark-labs-named-life-science-campus-of-the-year/",
        "event_date": "2024-09-24",
        "event_type": "AWARD",
    },
    {
        "company": "Longfellow Real Estate Partners",
        "title": "Bioterra Completion (First All-Electric Life Science Building)",
        "description": "Completion of 323,000 sq ft life science project in Sorrento Mesa, noted as San Diego's first all-electric HVAC life sciences building.",
        "url": "https://bioterrasd.com/",
        "event_date": "2025-10-01", 
        "event_type": "MILESTONE",
    },
    {
        "company": "Carrier Johnson + Culture",
        "title": "David Huchteman Appointed CEO",
        "description": "Appointed as Chief Executive Officer effective Jan 28, 2026 to lead strategic growth in San Diego, Los Angeles, and Seattle.",
        "url": "https://carrierjohnson.com/news/",
        "event_date": "2026-01-28",
        "event_type": "LEADERSHIP_CHANGE",
    },
    {
        "company": "Trammell Crow Company",
        "title": "Vista Sorrento Labs Completion",
        "description": "Completion of 116,000 sq ft speculative lab/office project in Sorrento Valley - TCC's first ground-up life science development in San Diego.",
        "url": "https://trammellcrow.com/projects/vista-sorrento-labs",
        "event_date": "2024-06-15",
        "event_type": "MILESTONE",
    }
]

CSV_COLUMNS = [
    "id",
    "triggered_company_id",
    "title",
    "description",
    "url",
    "event_date",
    "event_type"
]

def main():
    print("=" * 60)
    print("EXPORTING EVENTS TO SUPABASE CSV")
    print("=" * 60)
    
    rows = []
    
    for evt in EVENTS:
        company = evt["company"]
        company_id = COMPANY_UUIDS.get(company)
        
        if not company_id:
            print(f"Skipping {company} - No UUID found")
            continue
            
        row = {
            "id": str(uuid.uuid4()),
            "triggered_company_id": company_id,
            "title": evt["title"],
            "description": evt["description"],
            "url": evt["url"],
            "event_date": evt["event_date"],
            "event_type": evt["event_type"]
        }
        rows.append(row)
        print(f"  ✓ {evt['title']} ({company})")
    
    # Write CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n{'='*60}")
    print(f"✓ Exported {len(rows)} events to: {OUTPUT_CSV}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
