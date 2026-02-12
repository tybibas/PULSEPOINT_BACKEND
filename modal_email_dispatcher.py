import modal
from modal.mount import Mount
from fastapi import Request, UploadFile, File
from fastapi.responses import JSONResponse
import os
import datetime
import base64
from email.mime.text import MIMEText
from supabase import create_client, Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request as GoogleRequest
from pathlib import Path

# Helper to verify paths to ignore
def should_ignore(path):
    if path.name.startswith("."): return True
    if "venv" in path.name: return True
    return False

# Define the image with Supabase and Google Auth dependencies
image = (
    modal.Image.debian_slim()
    .pip_install(
        "supabase",
        "google-auth",
        "google-auth-oauthlib",
        "google-auth-httplib2",
        "google-api-python-client",
        "python-dotenv",
        "fastapi[standard]"
    )
    .add_local_dir(
        Path(__file__).parent,
        remote_path="/root",
        ignore=should_ignore
    )
)

app = modal.App("pulsepoint-email-dispatcher")

# UTILITIES
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment.")
    return create_client(url, key)

def get_gmail_service(sender_email: str, supabase: Client):
    """
    Fetches the Refresh Token from Supabase and builds an authenticated Gmail Service.
    Auto-refreshes the access token if needed.
    """
    # 1. Fetch Token
    resp = supabase.table("gmail_oauth_tokens").select("*").eq("email", sender_email).execute()
    if not resp.data:
        raise ValueError(f"No OAuth token found for {sender_email}")
    
    token_data = resp.data[0]
    refresh_token = token_data["refresh_token"]
    client_id = os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise ValueError("Missing Gmail Client credentials in environment.")

    # 2. Build Credentials object
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.send"]
    )

    # 3. Refresh if expired
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print(f"🔄 Refreshing Access Token for {sender_email}...")
            creds.refresh(GoogleRequest())
            # Save new access token
            supabase.table("gmail_oauth_tokens").update({
                "access_token": creds.token,
                "token_expiry": creds.expiry.isoformat() if creds.expiry else None,
                "updated_at": "now()"
            }).eq("id", token_data["id"]).execute()
        else:
            raise ValueError("Token invalid and cannot be refreshed.")
            
    return build("gmail", "v1", credentials=creds)

def send_email_via_gmail(service, to, subject, body, thread_id=None):
    """Creates and sends an email message. Supports threading."""
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    
    body_payload = {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")}
    
    if thread_id:
        body_payload["threadId"] = thread_id
    
    try:
        sent_message = service.users().messages().send(
            userId="me", 
            body=body_payload
        ).execute()
        return sent_message
    except Exception as e:
        print(f"❌ Gmail Send Error: {e}")
        raise e

# MODAL FUNCTION
@app.function(
    image=image, 
    secrets=[modal.Secret.from_dotenv()],
    timeout=600 # 10 minutes allow for batch processing
)
def process_email_queue(limit: int = 30):
    print(f"🚀 Starting Email Dispatch (Limit: {limit})")
    
    supabase = get_supabase()
    
    # 1. Fetch Pending Emails
    # Order by priority or creation date
    response = supabase.table("pulsepoint_email_queue")\
        .select("*")\
        .eq("status", "pending")\
        .lte("scheduled_for", "now()")\
        .order("created_at")\
        .limit(limit)\
        .execute()
        
    emails = response.data
    if not emails:
        print("✅ No pending emails found.")
        return {"status": "success", "processed": 0}
    
    print(f"📬 Found {len(emails)} pending emails.")
    
    # Assumption: The queue row should have a user_id to identify the sender
    # We group by user_id to batch send per user
    
    # Simple approach: Identify comprehensive set of users in the batch
    user_ids = list(set([e['user_id'] for e in emails if e.get('user_id')]))
    
    # Cache services per user
    services = {}
    
    for uid in user_ids:
        if not uid: continue
        try:
             # Fetch token for this user
             token_resp = supabase.table("gmail_oauth_tokens").select("email").eq("auth_user_id", uid).limit(1).execute()
             if token_resp.data:
                 email_addr = token_resp.data[0]["email"]
                 services[uid] = get_gmail_service(email_addr, supabase)
             else:
                 print(f"⚠️ No token found for user_id {uid}")
        except Exception as e:
            print(f"❌ Failed to init service for {uid}: {e}")

    # Fallback for old rows without user_id (Backwards compatibility / Env var)
    default_service = None
    default_sender = os.environ.get("SENDER_EMAIL_ADDRESS")
    if default_sender:
        try:
            default_service = get_gmail_service(default_sender, supabase)
        except:
             pass

    # 2. Process Batch
    success_count = 0
    fail_count = 0
    
    for email in emails:
        try:
            print(f"👉 Sending to {email['email_to']}...")
            
            # Update status to processing
            supabase.table("pulsepoint_email_queue")\
                .update({"status": "processing"})\
                .eq("id", email["id"])\
                .execute()
                
            # Determine Service
            uid = email.get('user_id')
            active_service = services.get(uid) if uid else default_service
            
            if not active_service:
                raise ValueError("No valid Gmail service for this user.")

            # Send (Pass thread_id if available)
            thread_id = email.get("thread_id") 
            result = send_email_via_gmail(
                active_service, 
                email["email_to"], 
                email["email_subject"], 
                email["email_body"],
                thread_id=thread_id
            )
            
            # Extract IDs from response
            sent_thread_id = result.get("threadId")
            sent_message_id = result.get("id")
            
            # Update success with tracking info
            supabase.table("pulsepoint_email_queue")\
                .update({
                    "status": "sent", 
                    "sent_at": "now()",
                    "attempts": email["attempts"] + 1,
                    "thread_id": sent_thread_id,
                    "provider_message_id": sent_message_id
                })\
                .eq("id", email["id"])\
                .execute()
            
            print(f"   ✅ Sent. (Thread ID: {sent_thread_id})")
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            fail_count += 1
            # Update failure
            supabase.table("pulsepoint_email_queue")\
                .update({
                    "status": "failed", 
                    "last_error": str(e),
                    "attempts": email["attempts"] + 1
                })\
                .eq("id", email["id"])\
                .execute()

    print(f"🏁 Batch Complete. Success: {success_count}, Failed: {fail_count}")
    return {"status": "success", "processed": len(emails), "sent": success_count, "failed": fail_count}

# WEB ENDPOINT
@app.function(image=image)
@modal.web_endpoint(method="POST")
def trigger_dispatch(item: dict = None):
    """
    Webhook exposed to the dashboard.
    Call with POST payload (optional): {"limit": 50}
    """
    limit = 30
    if item and "limit" in item:
        limit = item["limit"]
        
    print(f"🔔 Received Dispatch Trigger via Webhook (Limit: {limit})")
    
    # Spawn the worker in the background (Non-blocking for the HTTP request?)
    # Or blocking if we want to return the result. 
    # For a dispatch button, blocking 10-20 seconds is okay, but 30 emails might take longer.
    # We will use .spawn() to run in background and return "Started".
    
    # process_email_queue.spawn(limit=limit)
    # return JSONResponse({"status": "started", "message": "Email dispatch started in background."})
    
    # Actually, user might want confirmation. Let's block if it's < 5, spawn if > 5?
    # Let's just block for now so we see logs in the response for debugging, 
    # unless it times out the HTTP request. Modal web endpoints verify quickly.
    
    # SAFE APPROACH: Run remotely and wait for result (up to 60s HTTP timeout)
    # If 30 emails take 1s each, that's 30s. It might fit.
    
    job = process_email_queue.remote(limit=limit)
    return JSONResponse(content=job)

# CRON JOB (Runs every 15 minutes to check for scheduled emails)
@app.function(
    image=image, 
    schedule=modal.Cron("*/15 * * * *"),
    secrets=[modal.Secret.from_dotenv()],
    timeout=600
)
def scheduled_dispatcher():
    print("⏰ Cron Trigger: Checking for scheduled emails...")
    process_email_queue.remote(limit=50) # Process up to 50 due emails
