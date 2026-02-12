import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

# Config
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def authenticate():
    if not os.path.exists('credentials.json'):
        print("Error: credentials.json not found.")
        return

    print("Opening browser for Google Authentication...")
    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    
    # This attempts to open a browser window on the local machine
    creds = flow.run_local_server(port=0)
    
    # Save the credentials for the next run
    with open('token.json', 'wb') as token:
        pickle.dump(creds, token)
        
    print("Authentication successful! 'token.json' created.")

if __name__ == "__main__":
    authenticate()
