import os
import json
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

# Config
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID") 
FTSE_FILE = "ftse_constituents.json"
DAX_FILE = "dax_constituents.json"
QUEUE_FILE = "dashboard_queue.json"
MASTER_UNIVERSE_FILE = "master_universe_queue.json"

def get_event_significance(event_type: str) -> str:
    """
    Returns a human-readable explanation of why an event type is significant.
    This helps the admin understand at a glance why the company was triggered.
    """
    if not event_type:
        return ""
    
    event_lower = event_type.lower()
    
    # Map event types to significance explanations
    significance_map = {
        "cfo appointment": "New financial leadership = fresh mandate to review IR strategy & perception gaps",
        "capital markets day": "Board presents strategy to analysts—high risk of narrative misalignment",
        "investor conference": "Public-facing investor event—perception audit timing is ideal",
        "perception study": "Company is actively reviewing how market perceives them—warm lead",
        "perception report": "Company is actively reviewing how market perceives them—warm lead",
        "stock drop": "Share price decline creates urgency for IR narrative reset",
        "head of ir": "New IR leadership = reset opportunity for perception strategy",
        "investor relations": "IR activity signals openness to engagement",
    }
    
    # Check for matches (handle combined types like "CFO Appointment / Capital Markets Day")
    explanations = []
    for key, explanation in significance_map.items():
        if key in event_lower:
            explanations.append(explanation)
    
    if explanations:
        return " | ".join(explanations[:2])  # Limit to 2 explanations max for readability
    
    return "Strategic event detected—review for outreach opportunity"


def get_creds():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: credentials.json not found. Cannot auth with Google.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def ensure_tab_exists(sheet, spreadsheet_id, title):
    try:
        spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        titles = [s['properties']['title'] for s in sheets]
        
        if title not in titles:
            print(f"Creating tab: {title}")
            req = {
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': title
                            }
                        }
                    }
                ]
            }
            sheet.batchUpdate(spreadsheetId=spreadsheet_id, body=req).execute()
    except Exception as e:
        print(f"Error checking/creating tab {title}: {e}")

def update_sheet(sheet, spreadsheet_id, range_name, values):
    body = {'values': values}
    try:
        # Clear the entire sheet content to avoid leftovers
        clear_range = range_name.split('!')[0] # Get 'SheetName' from 'SheetName!A1'
        sheet.values().clear(spreadsheetId=spreadsheet_id, range=clear_range).execute()
        sheet.values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption="RAW", body=body).execute()
    except Exception as e:
        print(f"Error updating {range_name}: {e}")

def format_header(sheet, spreadsheet_id, title):
    """
    Applies bold formatting and freezes the first row.
    """
    try:
        # Get sheet ID (gridId)
        spreadsheet = sheet.get(spreadsheetId=spreadsheet_id).execute()
        sheets = spreadsheet.get('sheets', [])
        sheet_id = None
        for s in sheets:
            if s['properties']['title'] == title:
                sheet_id = s['properties']['sheetId']
                break
        
        if sheet_id is None:
            return

        requests = [
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_id,
                        "startRowIndex": 0,
                        "endRowIndex": 1
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "textFormat": {
                                "bold": True
                            }
                        }
                    },
                    "fields": "userEnteredFormat.textFormat.bold"
                }
            },
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "frozenRowCount": 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            }
        ]
        
        sheet.batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
        print(f"Formatted header for {title}")
        
    except Exception as e:
        print(f"Error formatting {title}: {e}")

def read_sheet(sheet, spreadsheet_id, range_name):
    try:
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    except Exception as e:
        print(f"Error reading {range_name}: {e}")
        return []

def sync_to_sheet():
    if not SPREADSHEET_ID:
        print("Error: GOOGLE_SHEET_ID not set in .env")
        return

    creds = get_creds()
    if not creds:
        return

    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    
    # Ensure tabs
    ensure_tab_exists(sheet, SPREADSHEET_ID, "Universe")
    ensure_tab_exists(sheet, SPREADSHEET_ID, "DAX Universe")
    ensure_tab_exists(sheet, SPREADSHEET_ID, "Triggered")

    # 1. Load Data
    ftse_data = []
    if os.path.exists(FTSE_FILE):
        with open(FTSE_FILE, 'r') as f:
            ftse_data = json.load(f)
            
    dax_data = []
    if os.path.exists(DAX_FILE):
        with open(DAX_FILE, 'r') as f:
            dax_data = json.load(f)
            
    queue_data = []
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r') as f:
            queue_data = json.load(f)

    # 2. Sync FTSE Universe
    univ_headers = ["Name", "Ticker", "Sector", "Industry", "Description", "Website", "Market Cap", "52-Wk Change", "Price"]
    univ_rows = []
    for c in ftse_data:
        change = c.get('fifty_two_week_change', 0)
        if change is None: change = 0
        fmt_change = f"{change*100:+.1f}%"
        
        univ_rows.append([
            c.get("name"),
            c.get("ticker"),
            c.get("sector"),
            c.get("industry"),
            c.get("description"),
            c.get("website"),
            c.get("market_cap"),
            fmt_change,
            c.get("current_price")
        ])
    
    update_sheet(sheet, SPREADSHEET_ID, "Universe!A1", [univ_headers] + univ_rows)
    print(f"Synced {len(univ_rows)} rows to Universe.")
    
    # 3. Sync DAX Universe
    dax_rows = []
    for c in dax_data:
        change = c.get('fifty_two_week_change', 0)
        if change is None: change = 0
        fmt_change = f"{change*100:+.1f}%"
        
        dax_rows.append([
            c.get("name"),
            c.get("ticker"),
            c.get("sector"),
            c.get("industry"),
            c.get("description"),
            c.get("website"),
            c.get("market_cap"),
            fmt_change,
            c.get("current_price")
        ])
    
    update_sheet(sheet, SPREADSHEET_ID, "DAX Universe!A1", [univ_headers] + dax_rows)
    print(f"Synced {len(dax_rows)} rows to DAX Universe.")

    # 4. Sync Triggered (Split by Index)
    ensure_tab_exists(sheet, SPREADSHEET_ID, "Triggered") # For FTSE (default)
    ensure_tab_exists(sheet, SPREADSHEET_ID, "DAX Triggered") # For DAX
    
    trig_headers = ["Company", "Ticker", "Event Type", "News Link", "Event Details", "Detected At", "Stock Perf.", "Contacts", "Draft Email 1", "Draft Email 2", "Draft Email 3", "Status", "Linkedin Profile 1", "Linkedin Profile 2", "Linkedin Profile 3"]
    
    ftse_rows = []
    dax_rows = []
    
    for item in queue_data:
        # Determine index
        # 'index_name' might be explicit from enrich_lead, or implicit
        idx = item.get("index_name", "FTSE")
        
        # Format Contacts
        contacts = item.get("contacts", [])
        if not contacts and item.get("contact"): # Legacy fallback
             contacts = [item.get("contact")]
             
        contact_str = ""
        for c in contacts:
            contact_str += f"{c.get('name')} ({c.get('role', 'IR')}) <{c.get('email')}>\n"
        
        # Extract draft emails (up to 3)
        email_drafts = item.get("email_drafts", [])
        
        # Format each draft with contact name header
        draft_1 = ""
        draft_2 = ""
        draft_3 = ""
        
        if len(email_drafts) >= 1:
            d = email_drafts[0]
            draft_1 = f"TO: {d.get('contact_name')} ({d.get('contact_role')})\nEMAIL: {d.get('contact_email')}\n\n{d.get('draft', '')}"
        elif item.get("draft_hook"):  # Backwards compatibility
            draft_1 = item.get("draft_hook", "")
            
        if len(email_drafts) >= 2:
            d = email_drafts[1]
            draft_2 = f"TO: {d.get('contact_name')} ({d.get('contact_role')})\nEMAIL: {d.get('contact_email')}\n\n{d.get('draft', '')}"
            
        if len(email_drafts) >= 3:
            d = email_drafts[2]
            draft_3 = f"TO: {d.get('contact_name')} ({d.get('contact_role')})\nEMAIL: {d.get('contact_email')}\n\n{d.get('draft', '')}"
        
        event = item.get("event", {})
        
        # Format Event Title with Context (Title + Description + URL)
        e_title = event.get("title", "")
        e_desc = event.get("description", "")
        e_url = event.get("url", "")
        e_type = event.get("event_type", "")
        
        # Truncate description slightly if massive
        if len(e_desc) > 200: e_desc = e_desc[:200] + "..."
        
        # === ENHANCED EVENT TYPE WITH SIGNIFICANCE ===
        # Add significance explanation based on event type
        event_significance = get_event_significance(e_type)
        rich_event_type = f"{e_type}\n({event_significance})" if event_significance else e_type
        
        # === ENHANCED EVENT DETAILS ===
        # Construct rich text cell with title and description (URL now in separate column)
        rich_event_info = f"📌 {e_title}\n\n📰 {e_desc}"

        row = [
            item.get("company"),
            item.get("ticker"),
            rich_event_type,
            e_url,  # Dedicated News Link column for easy clicking
            rich_event_info,
            event.get("detected_at"),
            item.get("performance", "N/A"),
            contact_str.strip(),
            draft_1,
            draft_2,
            draft_3,
            item.get("status"),
            contacts[0].get("linkedin", "") if len(contacts) > 0 else "",
            contacts[1].get("linkedin", "") if len(contacts) > 1 else "",
            contacts[2].get("linkedin", "") if len(contacts) > 2 else ""
        ]
        
        if idx == "DAX":
            dax_rows.append(row)
        else:
            ftse_rows.append(row)
        
    update_sheet(sheet, SPREADSHEET_ID, "Triggered!A1", [trig_headers] + ftse_rows)
    update_sheet(sheet, SPREADSHEET_ID, "DAX Triggered!A1", [trig_headers] + dax_rows)
    
    # Apply formatting
    format_header(sheet, SPREADSHEET_ID, "Universe")
    format_header(sheet, SPREADSHEET_ID, "DAX Universe")
    format_header(sheet, SPREADSHEET_ID, "Triggered")
    format_header(sheet, SPREADSHEET_ID, "DAX Triggered")
    
    print(f"Synced {len(ftse_rows)} rows to Triggered (FTSE).")
    print(f"Synced {len(dax_rows)} rows to DAX Triggered.")
    
    # 5. Sync DAX_Master_Universe (Merge Mode)
    TARGET_TAB = "DAX_Master_Universe"
    ensure_tab_exists(sheet, SPREADSHEET_ID, TARGET_TAB)
    
    # Load updates from queue
    master_updates = {}
    if os.path.exists(MASTER_UNIVERSE_FILE):
        with open(MASTER_UNIVERSE_FILE, 'r') as f:
            queue_list = json.load(f)
            # Index by Email for matching
            for item in queue_list:
                email = item.get("Email_Address")
                if email:
                    master_updates[email.lower()] = item
    
    if not master_updates:
        print("No updates in queue file.")
    else:
        # Read existing sheet data
        current_data = read_sheet(sheet, SPREADSHEET_ID, f"{TARGET_TAB}!A1:Z")
        
        if not current_data:
            # If empty, Initialize with headers
            headers = ["Company_Name", "Ticker", "Index", "First_Name", "Last_Name", "Role", "Email_Address", "AI_Hook_Draft", "Context_Snippet", "Status"]
            final_rows = [headers]
        else:
            headers = current_data[0]
            final_rows = list(current_data) # Copy
            
            # Identify columns
            try:
                col_map = {name: i for i, name in enumerate(headers)}
                
                # Check Email Column
                email_idx = col_map.get("Email_Address")
                if email_idx is None:
                    email_idx = col_map.get("Email")
                
                if email_idx is None:
                    print("Error: Could not find Email column in DAX_Master_Universe. Cannot merge.")
                else:
                    # Update rows
                    hook_idx = col_map.get("AI_Hook_Draft")
                    if hook_idx is None:
                        headers.append("AI_Hook_Draft")
                        hook_idx = len(headers) - 1
                        final_rows[0] = headers
                    
                    # Iterate rows (skipping header)
                    for i in range(1, len(final_rows)):
                        row = final_rows[i]
                        while len(row) <= hook_idx:
                            row.append("")
                            
                        row_email = row[email_idx].strip().lower() if len(row) > email_idx else ""
                        
                        if row_email in master_updates:
                            item = master_updates[row_email]
                            row[hook_idx] = item.get("AI_Hook_Draft", "")
                            # Update Context too?
                            ctx_idx = col_map.get("Context_Snippet")
                            if ctx_idx and ctx_idx < len(row):
                                row[ctx_idx] = item.get("Context_Snippet", "")
                            print(f"Updated hook for {row_email}")
                            
                    # Add NEW rows
                    existing_emails = set()
                    for r in final_rows[1:]:
                        if len(r) > email_idx:
                            existing_emails.add(r[email_idx].strip().lower())
                            
                    for email, item in master_updates.items():
                        if email not in existing_emails:
                            # Append new row
                            new_row = [""] * len(headers)
                            # Fill known cols
                            for col_name, val in item.items():
                                c_idx = col_map.get(col_name)
                                if c_idx is not None:
                                    new_row[c_idx] = str(val)
                            final_rows.append(new_row)
                            print(f"Appended new contact: {email}")

            except Exception as e:
                print(f"Error processing headers/merge: {e}")
                
        # Write back full table
        update_sheet(sheet, SPREADSHEET_ID, f"{TARGET_TAB}!A1", final_rows)
        format_header(sheet, SPREADSHEET_ID, TARGET_TAB)
        print(f"Synced {len(final_rows)-1} rows to {TARGET_TAB} (Merged).")


if __name__ == "__main__":
    sync_to_sheet()
