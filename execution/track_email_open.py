"""
Email Open Tracking Webhook
Receives tracking pixel requests and logs email opens to Supabase.
"""
import modal
import os
from supabase import create_client
from pathlib import Path

# Modal App
app = modal.App("email-tracker")

# Image with dependencies
image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "supabase",
    "python-dotenv",
    "fastapi[standard]"
)

# 1x1 Transparent GIF (base64 decoded)
TRANSPARENT_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x21, 0xf9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])

def get_supabase():
    """Initialize Supabase client."""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv(path=Path(__file__).parent.parent)]
)
@modal.fastapi_endpoint(method="GET")
def track_open(id: str = None):
    """
    Tracking pixel endpoint.
    Called when email is opened and the 1x1 image is loaded.
    
    Usage: GET /track_open?id={tracking_id}
    Returns: 1x1 transparent GIF
    """
    from fastapi.responses import Response
    
    if not id:
        return Response(
            content=TRANSPARENT_GIF,
            media_type="image/gif",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
    
    try:
        supabase = get_supabase()
        
        # First, check if this is the first open
        result = supabase.table("pulsepoint_email_queue")\
            .select("opened_at, open_count")\
            .eq("tracking_id", id)\
            .execute()
        
        if result.data:
            current = result.data[0]
            new_count = (current.get("open_count") or 0) + 1
            
            update_data = {"open_count": new_count}
            
            # Only set opened_at on first open
            if not current.get("opened_at"):
                update_data["opened_at"] = "now()"
            
            supabase.table("pulsepoint_email_queue")\
                .update(update_data)\
                .eq("tracking_id", id)\
                .execute()
            
            print(f"📬 Email opened: {id} (open #{new_count})")
        else:
            print(f"⚠️ Unknown tracking ID: {id}")
            
    except Exception as e:
        print(f"❌ Tracking error: {e}")
    
    # Always return the transparent GIF
    return Response(
        content=TRANSPARENT_GIF,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv(path=Path(__file__).parent.parent)]
)
@modal.fastapi_endpoint(method="GET")  
def track_click(id: str = None, url: str = None):
    """
    Link click tracking endpoint.
    Called when user clicks a tracked link.
    
    Usage: GET /track_click?id={tracking_id}&url={original_url}
    Returns: 302 Redirect to original URL
    """
    from fastapi.responses import RedirectResponse
    
    if not url:
        url = "https://pulsepoint.com"  # Fallback
    
    if id:
        try:
            supabase = get_supabase()
            
            result = supabase.table("pulsepoint_email_queue")\
                .select("clicked_at, click_count")\
                .eq("tracking_id", id)\
                .execute()
            
            if result.data:
                current = result.data[0]
                new_count = (current.get("click_count") or 0) + 1
                
                update_data = {"click_count": new_count}
                
                if not current.get("clicked_at"):
                    update_data["clicked_at"] = "now()"
                
                supabase.table("pulsepoint_email_queue")\
                    .update(update_data)\
                    .eq("tracking_id", id)\
                    .execute()
                
                print(f"🔗 Link clicked: {id} -> {url}")
                
        except Exception as e:
            print(f"❌ Click tracking error: {e}")
    
    return RedirectResponse(url=url, status_code=302)
