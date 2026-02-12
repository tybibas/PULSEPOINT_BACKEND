import json
import pandas as pd
import os
from datetime import datetime

INPUT_FILE = '.tmp/targets_with_contacts.json'
OUTPUT_DIR = 'deliverables'

def format_targets(json_file):
    if not os.path.exists(json_file):
        # Fallback
        json_file = '.tmp/qualified_targets.json'
        
    if not os.path.exists(json_file):
        print(f"Input file {json_file} does not exist.")
        return

    with open(json_file, 'r') as f:
        data = json.load(f)

    if not data:
        print("No qualified targets found.")
        return

    formatted_rows = []
    for company in data:
        # Determine Geography
        ticker = company.get('Ticker', '')
        exchange = company.get('Exchange', '')
        
        geo = "EU"
        if ticker.endswith('.L'):
            geo = "UK"
        elif exchange == "NMS" or exchange == "NYQ" or ticker.endswith('.US'):
            geo = "US-NY"

        # Format contacts
        contacts_str = ""
        if 'Contacts' in company and company['Contacts']:
             import json as j
             contacts_str = j.dumps(company['Contacts'])

        # Map Directive Fields
        row = {
            'Company Name': company.get('Company'),
            'Ticker(s)': ticker,
            'Exchange': exchange,
            'Market Cap (approx.)': company.get('MarketCap'),
            'Geography': geo,
            'IR Leader(s)': "TBD",
            'Core Strategic Narrative': company.get('Core_Strategic_Narrative'),
            'Primary Interpretation Risk': company.get('Primary_Interpretation_Risk'),
            'Why This Company Is a Strong QuantiFire Fit': company.get('Why_Fits'),
            'Confidence Score': company.get('Confidence_Score'),
            'Contacts': contacts_str
        }
        formatted_rows.append(row)

    df = pd.DataFrame(formatted_rows)
    
    # Ensure columns order
    cols = [
        'Company Name', 'Ticker(s)', 'Exchange', 'Market Cap (approx.)', 'Geography',
        'IR Leader(s)', 'Core Strategic Narrative', 'Primary Interpretation Risk',
        'Why This Company Is a Strong QuantiFire Fit', 'Confidence Score', 'Contacts'
    ]
    
    # Add missing columns
    for c in cols:
        if c not in df.columns:
            df[c] = ""
            
    df = df[cols]
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = f"{OUTPUT_DIR}/Target_List_{date_str}.csv"
    
    df.to_csv(output_path, index=False)
    print(f"Successfully created {output_path} with {len(df)} targets.")

if __name__ == "__main__":
    format_targets(INPUT_FILE)
