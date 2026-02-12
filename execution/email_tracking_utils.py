"""
Email Tracking Utilities
Helper functions for adding tracking to emails.
"""

# Tracking Pixel Base URL (update after deployment)
TRACKING_BASE_URL = "https://ty-1239--email-tracker-track-open.modal.run"


def get_tracking_pixel_html(tracking_id: str) -> str:
    """
    Generate HTML for a 1x1 tracking pixel.
    Inject this at the END of the email body (HTML format).
    
    Args:
        tracking_id: UUID from pulsepoint_email_queue.tracking_id
        
    Returns:
        HTML string for invisible tracking image
    """
    return f'''<img src="{TRACKING_BASE_URL}?id={tracking_id}" width="1" height="1" style="display:none;visibility:hidden;border:0;height:1px;width:1px;" alt="" />'''


def wrap_link_with_tracking(original_url: str, tracking_id: str) -> str:
    """
    Wrap a URL with click tracking.
    Replace original links with this tracked version.
    
    Args:
        original_url: The original destination URL
        tracking_id: UUID from pulsepoint_email_queue.tracking_id
        
    Returns:
        Tracked URL that redirects through our server
    """
    import urllib.parse
    encoded_url = urllib.parse.quote(original_url, safe='')
    return f"{TRACKING_BASE_URL.replace('track-open', 'track-click')}?id={tracking_id}&url={encoded_url}"


def inject_tracking_into_email(html_body: str, tracking_id: str, track_links: bool = False) -> str:
    """
    Inject tracking pixel into an HTML email body.
    Optionally wrap all links with click tracking.
    
    Args:
        html_body: The original HTML email content
        tracking_id: UUID for tracking
        track_links: Whether to also track link clicks
        
    Returns:
        Modified HTML with tracking injected
    """
    import re
    
    modified_body = html_body
    
    # Optionally wrap links with tracking
    if track_links:
        # Find all href attributes and wrap them
        def replace_link(match):
            original_url = match.group(1)
            # Don't track mailto: or tel: links
            if original_url.startswith(('mailto:', 'tel:', '#')):
                return match.group(0)
            tracked_url = wrap_link_with_tracking(original_url, tracking_id)
            return f'href="{tracked_url}"'
        
        modified_body = re.sub(r'href="([^"]+)"', replace_link, modified_body)
    
    # Inject tracking pixel before closing </body> or at the end
    tracking_pixel = get_tracking_pixel_html(tracking_id)
    
    if '</body>' in modified_body.lower():
        # Insert before </body>
        modified_body = re.sub(
            r'(</body>)',
            f'{tracking_pixel}\\1',
            modified_body,
            flags=re.IGNORECASE
        )
    else:
        # Just append to the end
        modified_body += tracking_pixel
    
    return modified_body


# Example usage for Bolt/Edge Functions:
"""
// TypeScript (Supabase Edge Function or Bolt frontend)

import { createClient } from '@supabase/supabase-js';

const TRACKING_BASE_URL = 'https://ty-1239--email-tracker-track-open.modal.run';

function getTrackingPixelHtml(trackingId: string): string {
  return `<img src="${TRACKING_BASE_URL}?id=${trackingId}" width="1" height="1" style="display:none;" alt="" />`;
}

async function sendEmailWithTracking(emailId: string, htmlBody: string) {
  const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_KEY!);
  
  // Get the tracking_id for this email
  const { data: email } = await supabase
    .from('pulsepoint_email_queue')
    .select('tracking_id')
    .eq('id', emailId)
    .single();
  
  // Inject tracking pixel
  const trackedBody = htmlBody + getTrackingPixelHtml(email.tracking_id);
  
  // Send via Gmail API with trackedBody...
  // After sending, store the gmail_message_id and gmail_thread_id
}
"""
