#!/usr/bin/env python3
"""
Enrich missing DAX companies and append to DAX_Master_Universe tab.
Only processes companies not already in the sheet.
"""

import json
import os
import sys
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from execution.enrich_lead import find_officer_name, find_verified_email, find_contact_via_apollo, normalize_name

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
DAX_FILE = 'dax_constituents.json'

# Get creds
creds = None
if os.path.exists('token.json'):
    with open('token.json', 'rb') as token:
        creds = pickle.load(token)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Load DAX companies
with open(DAX_FILE, 'r') as f:
    dax_data = json.load(f)
print(f"Loaded {len(dax_data)} DAX companies")

# Get existing companies from sheet
try:
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range='DAX_Master_Universe!A:A').execute()
    existing_rows = result.get('values', [])
    existing_companies = {row[0].lower().strip() for row in existing_rows[1:] if row}  # Skip header
    print(f"Already have {len(existing_companies)} companies in sheet")
except:
    existing_companies = set()

# Find missing companies
missing = [c for c in dax_data if c['name'].lower().strip() not in existing_companies]
print(f"Need to enrich {len(missing)} missing companies")

# Enrich and collect new rows
new_rows = []
for company_data in missing:
    company = company_data.get('name')
    ticker = company_data.get('ticker')
    website = company_data.get('website', '')
    
    print(f"\n[Processing] {company} ({ticker})")
    
    # Extract domain
    domain = None
    if website:
        domain = website.split("//")[-1].split("/")[0].replace("www.", "")
    
    if not domain:
        print(f"  [Skip] No domain")
        continue
    
    # Try to find at least one contact (prioritize CFO, then IR)
    found = False
    for role in ["Chief Financial Officer", "Head of Investor Relations"]:
        if found:
            break
            
        # Primary: Google + Anymailfinder
        name = find_officer_name(company, role)
        if name:
            print(f"  [Primary] Found {name} ({role})")
            email = find_verified_email(name, domain)
            if email:
                print(f"  [Verified] {email}")
                parts = name.split(None, 1)
                first_name = parts[0] if parts else ''
                last_name = parts[1] if len(parts) > 1 else ''
                new_rows.append([company, ticker, 'DAX 40', first_name, last_name, role, email])
                found = True
                break
        
        # Fallback: Apollo
        if not found:
            print(f"  [Apollo] Trying {role}...")
            apollo = find_contact_via_apollo(domain, role)
            if apollo and apollo.get('email'):
                name = apollo.get('name', '')
                parts = name.split(None, 1)
                first_name = parts[0] if parts else ''
                last_name = parts[1] if len(parts) > 1 else ''
                print(f"  [Apollo] Found {name} ({apollo['email']})")
                new_rows.append([company, ticker, 'DAX 40', first_name, last_name, apollo.get('role', role), apollo['email']])
                found = True
                break
    
    if not found:
        print(f"  [Skip] No contact found")

# Append new rows to sheet
if new_rows:
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='DAX_Master_Universe!A:G',
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body={'values': new_rows}
    ).execute()
    print(f"\n=== Appended {len(new_rows)} new contacts ===")
else:
    print("\nNo new contacts to add")
