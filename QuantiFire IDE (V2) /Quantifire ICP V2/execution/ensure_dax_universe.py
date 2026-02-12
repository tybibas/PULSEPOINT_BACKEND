import os
import pickle
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')

try:
    with open('token.json', 'rb') as token:
        creds = pickle.load(token)
    service = build('sheets', 'v4', credentials=creds)

    # Check tabs
    sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = sheet_metadata.get('sheets', [])
    titles = [s['properties']['title'] for s in sheets]
    print(f'Tabs found: {titles}')

    if 'DAX Universe' not in titles:
        print('Creating DAX Universe tab...')
        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body={'requests': [{'addSheet': {'properties': {'title': 'DAX Universe'}}}]}).execute()
        
        # Populate from json if creating new
        if os.path.exists('dax_constituents.json'):
            with open('dax_constituents.json') as f:
                data = json.load(f)
            rows = [['Company', 'Ticker', 'Website']]
            for item in data:
                rows.append([item.get('name'), item.get('ticker'), item.get('website')])
            service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range='DAX Universe!A1', valueInputOption='RAW', body={'values': rows}).execute()
            print('Populated DAX Universe from JSON')
    else:
        # Verify it has data
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range='DAX Universe!A1:A5').execute()
        if not result.get('values'):
            print('DAX Universe empty, populating...')
            if os.path.exists('dax_constituents.json'):
                with open('dax_constituents.json') as f:
                    data = json.load(f)
                rows = [['Company', 'Ticker', 'Website']]
                for item in data:
                    rows.append([item.get('name'), item.get('ticker'), item.get('website')])
                service.spreadsheets().values().update(spreadsheetId=SPREADSHEET_ID, range='DAX Universe!A1', valueInputOption='RAW', body={'values': rows}).execute()
                print('Populated DAX Universe from JSON')

except Exception as e:
    print(f"Error: {e}")
