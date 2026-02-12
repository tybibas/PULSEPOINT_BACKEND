import os
import pickle
import json
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID')
SHEET_TITLE = 'IBEX_Master_Universe'

HEADERS = [
    'Company_Name', 'Ticker', 'Index', 'Contact_First_Name', 'Contact_Last_Name', 
    'Job_Title', 'Email_Address', 'LinkedIn_URL', 'Status', 'Last_Contacted_Date', 
    'Trigger_Type', 'Assigned_Variant', 'AI_Hook_Draft', 'Sector', 'Industry', 
    'Description', 'Website', 'Market Cap', '52-Wk Change', 'Price'
]

def ensure_ibex_universe():
    try:
        creds = None
        if os.path.exists('token.json'):
            with open('token.json', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds:
            print("No token.json found.")
            return

        service = build('sheets', 'v4', credentials=creds)

        # Check tabs
        sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheets = sheet_metadata.get('sheets', [])
        titles = [s['properties']['title'] for s in sheets]
        print(f'Tabs found: {titles}')

        if SHEET_TITLE not in titles:
            print(f'Creating {SHEET_TITLE} tab...')
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID, 
                body={'requests': [{'addSheet': {'properties': {'title': SHEET_TITLE}}}]}
            ).execute()
        else:
            print(f'{SHEET_TITLE} already exists.')

        # Prepare data
        rows = [HEADERS]
        if os.path.exists('ibex_constituents.json'):
            with open('ibex_constituents.json') as f:
                data = json.load(f)
            
            for item in data:
                # Map fields
                company_name = item.get('name', '')
                ticker = item.get('ticker', '')
                index_name = "IBEX 35"
                
                # Create row with empty values for other columns
                # We only fill Company_Name (0), Ticker (1), Index (2)
                row = [''] * len(HEADERS)
                row[0] = company_name
                row[1] = ticker
                row[2] = index_name
                
                rows.append(row)
        else:
            print("ibex_constituents.json not found.")

        # Update sheet
        print(f"Writing {len(rows)} rows to {SHEET_TITLE}...")
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, 
            range=f'{SHEET_TITLE}!A1', 
            valueInputOption='RAW', 
            body={'values': rows}
        ).execute()
        
        print('Done.')

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ensure_ibex_universe()
