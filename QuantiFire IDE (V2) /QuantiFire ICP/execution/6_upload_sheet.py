import json
import gspread
from google.oauth2.service_account import Credentials
import os
import pandas as pd

INPUT_FILE = '.tmp/targets_with_contacts.json'
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1ZGKgZz6XlCpTdUV4ACnMCUsx7Nxf1qNaQ5V4VwPrJRI/edit?gid=0#gid=0'

def upload_to_sheet(contacts_file):
    if not os.path.exists(contacts_file):
        print(f"{contacts_file} not found. Run previous steps first.")
        return

    # Check for credentials
    creds_file = 'credentials.json'
    if not os.path.exists(creds_file):
        print("Error: credentials.json not found in root directory. Cannot authenticate with Google Sheets.")
        print("Please place your Service Account credentials in credentials.json.")
        return

    # Authenticate
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        credentials = Credentials.from_service_account_file(creds_file, scopes=scopes)
        client = gspread.authorize(credentials)
        
        # Open Sheet
        try:
            sheet = client.open_by_url(SPREADSHEET_URL)
            worksheet = sheet.get_worksheet(0) # First sheet
        except Exception as e:
            print(f"Error opening sheet: {e}")
            return

        with open(contacts_file, 'r') as f:
            data = json.load(f)

        if not data:
            print("No data to upload.")
            return

        # Prepare rows for Sheet
        rows = []
        headers = [
            'Company Name', 'Ticker(s)', 'Exchange', 'Market Cap (approx.)', 'Geography',
            'IR Leader(s)', 'Core Strategic Narrative', 'Primary Interpretation Risk',
            'Why This Company Is a Strong QuantiFire Fit', 'Confidence Score', 'Contacts'
        ]
        
        rows.append(headers)
        
        for company in data:
            contacts_str = ""
            if 'Contacts' in company:
                # Format contacts as a readable string
                c_list = company['Contacts']
                # AMF response usually has 'email', 'name', etc.
                # Assuming list of dicts or single dict
                import json as j
                contacts_str = j.dumps(c_list) # Dump json for now to preserve structure

            row = [
                company.get('Company', ''),
                company.get('Ticker', ''),
                company.get('Exchange', ''),
                company.get('MarketCap', ''),
                "UK/EU", # Placeholder or derived
                "TBD",
                company.get('Core_Strategic_Narrative', ''),
                company.get('Primary_Interpretation_Risk', ''),
                company.get('Why_Fits', ''),
                company.get('Confidence_Score', ''),
                contacts_str
            ]
            rows.append(row)

        # Clear and update
        worksheet.clear()
        worksheet.update('A1', rows)
        print(f"Successfully uploaded {len(rows)-1} rows to Google Sheet.")
        
    except Exception as e:
        print(f"Google Sheets Upload Error: {e}")

if __name__ == "__main__":
    upload_to_sheet(INPUT_FILE)
