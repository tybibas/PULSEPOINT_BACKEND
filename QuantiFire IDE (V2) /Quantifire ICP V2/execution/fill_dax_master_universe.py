#!/usr/bin/env python3
"""
Quick script to populate DAX_Master_Universe tab with contacts.
Columns A-G: Company_Name, Ticker, Index, Contact_First_Name, Contact_Last_Name, Job_Title, Email_Address
"""

import json
import os
import pickle
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')

# Get creds
creds = None
if os.path.exists('token.json'):
    with open('token.json', 'rb') as token:
        creds = pickle.load(token)

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Create tab if not exists
try:
    spreadsheet = sheet.get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = spreadsheet.get('sheets', [])
    titles = [s['properties']['title'] for s in sheets]
    if 'DAX_Master_Universe' not in titles:
        sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': [{'addSheet': {'properties': {'title': 'DAX_Master_Universe'}}}]}).execute()
        print('Created tab: DAX_Master_Universe')
except Exception as e:
    print(f'Tab error: {e}')

# Load dashboard queue (has DAX contacts)
with open('dashboard_queue.json', 'r') as f:
    queue_data = json.load(f)

# Build rows
headers = ['Company_Name', 'Ticker', 'Index', 'Contact_First_Name', 'Contact_Last_Name', 'Job_Title', 'Email_Address']
rows = [headers]

for item in queue_data:
    if item.get('index_name') != 'DAX':
        continue
    company = item.get('company', '')
    ticker = item.get('ticker', '')
    contacts = item.get('contacts', [])
    
    for c in contacts:
        name = c.get('name', '')
        parts = name.split(None, 1)
        first_name = parts[0] if parts else ''
        last_name = parts[1] if len(parts) > 1 else ''
        role = c.get('role', '')
        email = c.get('email', '')
        
        # Skip blanks and generic/invalid entries
        if email and first_name and 'Investor Relations' not in first_name and '@https' not in email:
            rows.append([company, ticker, 'DAX 40', first_name, last_name, role, email])

# Clear and update sheet
sheet.values().clear(spreadsheetId=SPREADSHEET_ID, range='DAX_Master_Universe').execute()
sheet.values().update(spreadsheetId=SPREADSHEET_ID, range='DAX_Master_Universe!A1', valueInputOption='RAW', body={'values': rows}).execute()

print(f'Synced {len(rows)-1} contacts to DAX_Master_Universe')
