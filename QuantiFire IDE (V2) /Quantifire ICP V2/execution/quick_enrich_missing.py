#!/usr/bin/env python3
"""
Quick enrichment: Compare DAX Universe vs DAX_Master_Universe, enrich only missing.
"""

import os
import sys
import pickle
from googleapiclient.discovery import build
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from execution.enrich_lead import find_officer_name, find_verified_email, find_contact_via_apollo

load_dotenv()

SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')

# Get creds
with open('token.json', 'rb') as token:
    creds = pickle.load(token)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# 1. Get all companies from DAX Universe (columns A=Company, B=Ticker, C=Website)
print("Reading DAX Universe...")
dax_universe = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='DAX Universe!A:C').execute()
dax_rows = dax_universe.get('values', [])[1:]  # Skip header
print(f"Found {len(dax_rows)} companies in DAX Universe")

# 2. Get companies already in DAX_Master_Universe (column A=Company)
print("Reading DAX_Master_Universe...")
master = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='DAX_Master_Universe!A:A').execute()
master_rows = master.get('values', [])[1:]  # Skip header
existing_companies = {row[0].lower().strip() for row in master_rows if row}
print(f"Already have {len(existing_companies)} companies in DAX_Master_Universe")

# 3. Find missing companies
missing = []
for row in dax_rows:
    if len(row) < 3:
        continue
    company, ticker, website = row[0], row[1], row[2]
    if company.lower().strip() not in existing_companies:
        missing.append((company, ticker, website))

print(f"\nNeed to enrich {len(missing)} missing companies")

# 4. Enrich missing companies
new_rows = []
for company, ticker, website in missing:
    print(f"\n[Processing] {company} ({ticker})")
    
    # Extract domain
    domain = website.split("//")[-1].split("/")[0].replace("www.", "") if website else None
    if not domain:
        print(f"  [Skip] No domain")
        continue
    
    # Try CFO first, then Head of IR
    for role in ["Chief Financial Officer", "Head of Investor Relations"]:
        name = find_officer_name(company, role)
        if name:
            print(f"  [Found] {name} ({role})")
            email = find_verified_email(name, domain)
            if email:
                print(f"  [Verified] {email}")
                parts = name.split(None, 1)
                first = parts[0] if parts else ''
                last = parts[1] if len(parts) > 1 else ''
                new_row = [company, ticker, 'DAX 40', first, last, role, email]
                sheet.values().append(
                    spreadsheetId=SPREADSHEET_ID,
                    range='DAX_Master_Universe!A:G',
                    valueInputOption='RAW',
                    insertDataOption='INSERT_ROWS',
                    body={'values': [new_row]}
                ).execute()
                print(f"  [Synced] {name}")
                break
        
        # Fallback: Apollo
        apollo = find_contact_via_apollo(domain, role)
        if apollo and apollo.get('email'):
            name = apollo.get('name', '')
            parts = name.split(None, 1)
            first = parts[0] if parts else ''
            last = parts[1] if len(parts) > 1 else ''
            print(f"  [Apollo] {name} ({apollo['email']})")
            new_row = [company, ticker, 'DAX 40', first, last, apollo.get('role', role), apollo['email']]
            sheet.values().append(
                spreadsheetId=SPREADSHEET_ID,
                range='DAX_Master_Universe!A:G',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body={'values': [new_row]}
            ).execute()
            print(f"  [Synced] {name}")
            break
    else:
        print(f"  [Skip] No verified contact found")

# Removed batch append at end to favor incremental

