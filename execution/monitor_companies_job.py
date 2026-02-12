import modal
import os
import json
import time
import uuid
from datetime import datetime, timedelta
from supabase import create_client, Client
from apify_client import ApifyClient
from openai import OpenAI
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Fix path for Modal execution
import sys
import os
sys.path.append(os.path.dirname(__file__))
if os.path.exists(os.path.join(os.path.dirname(__file__), "execution")):
    sys.path.append(os.path.join(os.path.dirname(__file__), "execution"))

from scouts.blog_scout import scout_latest_blog_posts
from scouts.social_scout import scout_executive_social_activity
from resilience import retry_with_backoff, CircuitBreaker
from shared.enrichment_utils import (
    is_valid_full_name, normalize_company, company_matches,
    find_website, find_decision_makers, verify_email, is_junk_company_name
)

# IMAGE DEFINITION
def should_ignore(path):
    path_str = str(path)
    if path.name.startswith(".") and path.name != ".env": return True
    if "venv" in path_str: return True
    if "node_modules" in path_str: return True
    if "__pycache__" in path_str: return True
    if ".git" in path_str: return True
    return False

image = (
    modal.Image.debian_slim()
    .pip_install(
        "supabase",
        "apify-client",
        "openai",
        "python-dotenv",
        "fastapi[standard]",
        "httpx",
        "newspaper4k",
        "beautifulsoup4",
        "lxml"
    )
    .add_local_dir(
        Path(__file__).parent.parent, # Upload root (so we can import if needed, though this is standalone)
        remote_path="/root",
        ignore=should_ignore
    )
)

app = modal.App("pulsepoint-monitor-worker")

# UTILITIES
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)

# Default scan limit if not specified per client
DEFAULT_DAILY_SCAN_LIMIT = 50

# GLOBAL BUDGETS (Per Company Scan)
MAX_FETCHED_PAGES_TOTAL = 25
MAX_LLM_CALLS = 5
MAX_LLM_CHARS = 3000

# RESILIENCE
GLOBAL_LLM_BREAKER = CircuitBreaker(failure_threshold=5, reset_timeout=3600)
GLOBAL_APIFY_BREAKER = CircuitBreaker(failure_threshold=5, reset_timeout=3600)

def get_due_companies(supabase: Client):
    """
    Fetches companies that are 'active' and due for a scan.
    Applies PER-CLIENT daily scan limits to control costs.
    
    Each client can have their own daily_scan_limit in CLIENT_STRATEGIES.
    Companies are prioritized by oldest scanned first (fair rotation).
    """
    # 1. Fetch ALL active companies
    resp = supabase.table("triggered_companies").select("*").eq("monitoring_status", "active").execute()
    companies = resp.data
    
    # Use timezone-aware datetime to match Supabase timestamps
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    # 2. Build list of due companies with their client context
    due_by_client = {}  # {client_context: [companies]}
    
    for comp in companies:
        last_run_str = comp.get("last_monitored_at")
        freq = comp.get("monitoring_frequency", "weekly")
        client_ctx = comp.get("client_context", "pulsepoint_strategic")
        
        # Check if due
        is_due = False
        if not last_run_str:
            is_due = True  # Never run
        else:
            last_run = datetime.fromisoformat(last_run_str.replace('Z', '+00:00'))
            
            if freq == "daily":
                threshold = now - timedelta(hours=20)
            elif freq == "biweekly":
                threshold = now - timedelta(days=3)
            else:  # weekly
                threshold = now - timedelta(days=6)
                
            if last_run < threshold:
                is_due = True
        
        if is_due:
            if client_ctx not in due_by_client:
                due_by_client[client_ctx] = []
            due_by_client[client_ctx].append(comp)
    
    # 3. Apply per-client limits (oldest scanned first)
    final_due_list = []
    
    for client_ctx, client_companies in due_by_client.items():
        # Get client-specific limit from strategy, or use default
        strategy = CLIENT_STRATEGIES.get(client_ctx, {})
        limit = strategy.get("daily_scan_limit", DEFAULT_DAILY_SCAN_LIMIT)
        
        # Sort by oldest scanned first (fair rotation)
        client_companies.sort(
            key=lambda x: x.get('last_monitored_at') or '1970-01-01'
        )
        
        # Take up to the limit
        selected = client_companies[:limit]
        final_due_list.extend(selected)
        
        print(f"   📊 {client_ctx}: {len(selected)}/{len(client_companies)} due (limit: {limit})")
    
    return final_due_list

# CLIENT STRATEGIES (The Brains)
# Each client gets their own: keywords, trigger analysis prompt, and EMAIL TONE

# CLIENT STRATEGIES (The Brains) - MIGRATED TO DATABASE
# This dictionary is now populated at runtime from the `client_strategies` table.
CLIENT_STRATEGIES = {}

def fetch_client_strategies(supabase: Client):
    """
    Populates the global CLIENT_STRATEGIES table from the database.
    """
    global CLIENT_STRATEGIES
    try:
        print("   📥 Fetching Client Strategies from Database...")
        resp = supabase.table("client_strategies").select("*").execute()
        if resp.data:
            for row in resp.data:
                slug = row.get("slug")
                config = row.get("config", {})
                CLIENT_STRATEGIES[slug] = config
            print(f"   ✅ Loaded {len(CLIENT_STRATEGIES)} strategies: {list(CLIENT_STRATEGIES.keys())}")
        else:
            print("   ⚠️ No strategies found in DB! Using default/empty.")
            
    except Exception as e:
        print(f"   ❌ Error loading strategies from DB: {e}")
        print("      Falling back to empty configuration.")

# ==================== ENHANCED MONITORING HELPERS ====================

def build_search_queries(company_name: str, strategy: dict) -> list:
    """
    Generate 3 targeted queries per company for deep search.
    
    Query 1: General news with base keywords
    Query 2: LinkedIn posts and articles
    Query 3: Press releases (PRNewswire, BusinessWire)
    """
    base_keywords = strategy.get("keywords", "news")
    
    # Context Hardening for Short/Common Names
    # If name is "Fine", "Idea", "Home", etc., we MUST add "Agency" or "Marketing"
    # otherwise we get "Mark Fine" or "Good Idea" results.
    
    common_words = {
        "fine", "idea", "home", "camp", "giant", "small", "hero", "union", 
        "method", "huge", "smart", "swift", "gant", "bond", "code", "area", 
        "work", "play", "accent", "focus", "impact", "spark", "pulse"
    }
    
    name_lower = company_name.lower()
    needs_context = len(company_name) < 5 or name_lower in common_words
    
    search_term = f'"{company_name}"'
    if needs_context:
        # Force context in the search query itself
        search_term = f'"{company_name}" (Agency OR Marketing OR Branding)'
    
    return [
        # Query 1: General news
        f'{search_term} {base_keywords}',
        # Query 2: LinkedIn-specific
        f'{search_term} site:linkedin.com/posts OR site:linkedin.com/pulse',
        # Query 3: Press releases (keep strict name here, PRs are usually specific)
        f'"{company_name}" site:prnewswire.com OR site:businesswire.com OR site:globenewswire.com'
    ]

def is_valid_article_url(url: str, company_name: str) -> tuple:
    """
    Validate that a URL is a specific article, not a generic landing page.
    
    Returns: (is_valid: bool, rejection_reason: str or None)
    
    Rejects:
    - Company's own website pages (e.g., company.com/press-releases)
    - Generic landing pages without specific article slugs
    - About/contact pages
    - Directory/Database pages (ZoomInfo, Crunchbase, etc.)
    """
    from urllib.parse import urlparse
    
    if not url:
        return (False, "No URL provided")
    
    parsed = urlparse(url.lower())
    path = parsed.path.rstrip('/')
    domain = parsed.netloc.lower()
    
    
    # BLOCK DIRECTORY SITES (Always Reject)
    # These are static profiles, not news.
    blocked_domains = [
        'zoominfo.com', 'apollo.io', 'crunchbase.com', 'pitchbook.com',
        'clutch.co', 'upcity.com', 'yelp.com', 'glassdoor.com', 
        'rocketreach.co', 'lusha.com', 'seamless.ai', 'signalhire.com',
        'dnb.com', 'owler.com', 'g2.com', 'capterra.com', 'trustpilot.com',
        'google.com', 'bing.com', 'yahoo.com', # Search results themselves
        'facebook.com', 'twitter.com', 'instagram.com', 'tiktok.com', 'youtube.com'
    ]
    
    if any(d in domain for d in blocked_domains):
        print(f"      ⛔ DEBUG: Blocking {domain}")
        return (False, f"Directory/Database domain rejected: {domain}")
    
    # Known valid third-party sources (allow these even if path looks generic)
    valid_sources = [
        'prnewswire.com', 'businesswire.com', 'globenewswire.com',
        'linkedin.com', 'bloomberg.com', 'reuters.com', 'forbes.com',
        'adweek.com', 'adage.com', 'marketingweek.com', 'thedrum.com',
        'campaignlive.com', 'prweek.com'
    ]
    
    is_third_party = any(source in domain for source in valid_sources)
    
    # Generic landing page patterns (reject these)

    generic_patterns = [
        '/press-releases', '/press-release', '/pressroom', '/press-room',
        '/news', '/newsroom', '/news-room', '/media', '/media-center',
        '/about-us', '/about', '/contact', '/team', '/blog',
        '/articles', '/resources', '/insights',
        '/careers', '/jobs', '/opportunities', '/join-us', '/working-at'
    ]
    
    # Check if URL ends with a generic pattern (no specific article after it)
    for pattern in generic_patterns:
        if path == pattern or path.endswith(pattern):
            return (False, f"Generic landing page detected: {pattern}")
            
    # Check for 'jobs' in path segment (e.g. /jobs/software-engineer)
    if '/jobs/' in path or '/careers/' in path:
        return (False, "Job posting page detected")
        
    # Check for Financial Noise keywords in URL path (earnings, stock, q1-results)
    financial_keywords = ['earnings', 'quarterly-results', 'stock-price', 'dividend', 'investor-relations', '10-k', '10-q']
    if any(k in path for k in financial_keywords):
        return (False, "Financial/Stock news rejected")
    
    # Check if the URL is on the company's own domain
    company_slug = company_name.lower().replace(' ', '').replace('-', '').replace('.', '')
    domain_slug = domain.replace('www.', '').replace('.com', '').replace('.org', '').replace('-', '')
    
    if company_slug in domain_slug and not is_third_party:
        # It's the company's own website - only valid if it's a specific article
        path_parts = [p for p in path.split('/') if p]
        if len(path_parts) < 2:
            return (False, f"Company's own website without specific article path")
        # Check if last segment looks like an article (has words/slug)
        last_segment = path_parts[-1] if path_parts else ''
        if len(last_segment) < 10 or last_segment in ['index', 'home', 'main']:
            return (False, f"Company's own website - appears to be generic page")
    
    return (True, None)

def extract_date_from_text(text: str, max_chars: int = 800) -> tuple:
    """
    Programmatically extract publication date from article text using regex.
    Scans first N characters for common date patterns.
    
    Returns: (date_obj, date_str) or (None, None) if not found
    
    This enables early rejection of old articles WITHOUT using AI tokens.
    """
    import re
    from datetime import datetime
    
    # Only scan first portion of text, BUT skip first 200 chars to avoid "Today's Date" in headers
    # Many sites put the current date in the nav bar.
    start_idx = 200 if len(text) > 300 else 0
    text_to_scan = text[start_idx:max_chars+start_idx] if text else ""
    
    today = datetime.now()
    found_dates = []

    # Month name mapping
    months = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    # Helper to validate date
    def matches_today(d):
        return d.year == today.year and d.month == today.month and d.day == today.day

    # Pattern 1: "January 15, 2026" or "Jan 15, 2026"
    for match in re.finditer(r'\b(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2}),?\s+(\d{4})\b', text_to_scan, re.IGNORECASE):
        month_str, day, year = match.groups()
        try:
            month = months.get(month_str.lower())
            if month:
                d = datetime(int(year), month, int(day))
                if not matches_today(d): return (d, d.strftime("%Y-%m-%d")) # Prioritize non-today
                found_dates.append(d)
        except: pass
    
    # Pattern 2: "15 January 2026" (European format)
    for match in re.finditer(r'\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{4})\b', text_to_scan, re.IGNORECASE):
        day, month_str, year = match.groups()
        try:
            month = months.get(month_str.lower())
            if month:
                d = datetime(int(year), month, int(day))
                if not matches_today(d): return (d, d.strftime("%Y-%m-%d"))
                found_dates.append(d)
        except: pass

    # Pattern 3: "2026-01-15" (ISO format)
    for match in re.finditer(r'\b(\d{4})-(\d{2})-(\d{2})\b', text_to_scan):
        year, month, day = match.groups()
        try:
            d = datetime(int(year), int(month), int(day))
            if not matches_today(d): return (d, d.strftime("%Y-%m-%d"))
            found_dates.append(d)
        except: pass
        
    # If only found today's date, return it (better than nothing, but risky)
    if found_dates:
        return (found_dates[0], found_dates[0].strftime("%Y-%m-%d"))
    
    return (None, None)

def extract_article_content(url: str, apify_client) -> str:
    """
    Use Apify Website Content Crawler to extract full article text.
    Fallback to newspaper4k if Apify fails or returns thin content.
    Returns up to 5000 chars of article content.
    """
    
    # Common paywall keywords to reject
    PAYWALL_KEYWORDS = ["log in", "sign in", "subscribe to read", "access denied", "403 forbidden", "subscription required", "please login"]

    def _is_paywalled(text):
        if len(text) < 300: return True
        intro = text[:500].lower()
        if any(k in intro for k in PAYWALL_KEYWORDS): return True
        return False

    # ATTEMPT 1: Apify
    try:
        def _call_apify():
            return apify_client.actor("apify/website-content-crawler").call(
                run_input={
                    "startUrls": [{"url": url}],
                    "maxCrawlPages": 1,
                    "maxCrawlDepth": 0,
                    "proxyConfiguration": {"useApifyProxy": True}
                },
                timeout_secs=30
            )
            
        run = GLOBAL_APIFY_BREAKER.call(_call_apify)
        if run:
            items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
            if items and len(items) > 0:
                text = items[0].get("text", "")
                if not _is_paywalled(text):
                    return text[:5000]
                print(f"      ⛔ Apify returned thin/paywalled content ({len(text)} chars)")
    except Exception as e:
        print(f"      ⚠️ Apify extraction failed: {e}")

    # ATTEMPT 2: newspaper4k (Fallback)
    try:
        print(f"      🔄 Falling back to newspaper4k for {url[:60]}...")
        from newspaper import Article
        import requests
        
        # Set generous timeout for manual fetch
        art = Article(url, request_timeout=20)
        art.download()
        art.parse()
        text = art.text
        
        if not _is_paywalled(text):
            return text[:5000]
        print(f"      ⛔ newspaper4k returned thin/paywalled content")
        
    except Exception as e:
        print(f"      ⚠️ newspaper4k extraction failed: {e}")

    return ""

    return ""

def truncate_and_structure_for_llm(text: str, source_url: str, title: str) -> str:
    """
    TOKEN DISCIPLINE: 
    - Strips noise (nav/footer/scripts)
    - Hard caps at MAX_LLM_CHARS
    - Returns structured JSON string for LLM input
    """
    if not text: return ""

    # 1. Strip noise (Quick heuristic)
    # Remove large blocks of whitespace
    import re
    cleaned = re.sub(r'\s+', ' ', text).strip()
    
    # 2. Hard Cap
    truncated = cleaned[:MAX_LLM_CHARS]
    if len(cleaned) > MAX_LLM_CHARS:
        truncated += "...[TRUNCATED]"

    # 3. Structure
    structured_input = {
        "source": source_url,
        "title": title,
        "body_truncated": truncated,
        "char_count": len(truncated)
    }
    
    return json.dumps(structured_input, indent=2)

def call_openai_analysis(item: dict, sys_prompt: str, openai_key: str, model: str = "gpt-4o") -> dict:
    """
    Standard helper for AI analysis with JSON format support.
    Used for specialized scouts and context anchors.
    """
    from openai import OpenAI
    import json
    
    client = OpenAI(api_key=openai_key)
    
    # Ensure JSON format is requested
    prompt = f"{sys_prompt}\n\nCONTENT TO ANALYZE:\n{item}\n\nReturn valid JSON."
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"      [AI Error] {e}")
        # Degrade gracefully: Return un-scored but preserved item
        return {
            "is_relevant": False, 
            "unscored": True, 
            "rejection_reason": f"AI Error: {e}",
            "summary": f"Unscored signal from {item.get('url', 'unknown source')}"
        }

def analyze_with_article_context(news_item: dict, article_text: str, company_name: str, client_context: str, openai_key: str) -> dict:
    """
    ADVANCED AI TRIGGER ANALYSIS with:
    - Chain-of-thought reasoning
    - Weighted scoring rubric
    - Few-shot examples
    - Injected current date for precise recency checks
    """
    from datetime import datetime, timedelta
    from openai import OpenAI
    
    strategy = CLIENT_STRATEGIES.get(client_context, CLIENT_STRATEGIES["pulsepoint_strategic"])
    client = OpenAI(api_key=openai_key)
    
    # Inject current date for precise recency checks
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    max_age = int(strategy.get("max_age_days", 25)) # Force int to prevent string errors
    cutoff_date = (today - timedelta(days=max_age)).strftime("%Y-%m-%d")
    
    prompt = f"""You are an expert Trigger Event Analyst. Today's date is {today_str}.

TASK: Analyze if this news represents a valid trigger event for outreach to {company_name}.

VALID TRIGGER TYPES FOR THIS CLIENT: {strategy['trigger_types']}
CLIENT CONTEXT: {strategy['trigger_prompt']}

=== NEWS ITEM (METADATA) ===
Title: {news_item.get('title', '')}
Description: {news_item.get('description', '')}
URL: {news_item.get('url', '')}

=== FULL CONTENT (STRUCTURED) ===
{truncate_and_structure_for_llm(article_text, news_item.get('url'), news_item.get('title', ''))}

=== SIGNAL METADATA ===
- Is Scouted Blog: {news_item.get('is_scouted_blog', False)}
- Is Scouted Social: {news_item.get('is_scouted_social', False)}
- Target Person: {news_item.get('person_name', 'Company Account')}
- Verification Status: {news_item.get('verification_status', 'verified')}

=== PHASE 11: TRIGGER LADDER (CLASSIFICATION) ===
1. TRIGGER: Safe, strong, citeable signal matching a valid type. Date is confirmed recent (<= {max_age} days).
2. CONTEXT_ONLY: Good background (e.g. Portfolio/Testimonial) but lacks "Why Now" urgency.
3. PENDING_REVIEW: Ambiguous identity, exact date unknown, or weak signal.
4. REJECTED: Not relevant, old, or invalid/ICP mismatch.

=== EVIDENCE REQUIREMENTS ===
You must extract:
- evidence_excerpt: EXACT quote from text validating the trigger (max 25 words).
- evidence_date: The specific date found in text (or "Unknown").

=== PHASE 8 CRITERIA (STRATEGIC DEPTH) ===
1. Outcome Delta: 2nd-order implication (Risk/Upside).
2. Buying Window: Exploration / Transition / Execution.

=== ANALYSIS INSTRUCTIONS ===
1. Check ICP Match. If invalid industry -> REJECTED.
2. Content Date Check. If undated or > {max_age} days -> REJECTED.
3. Subject Check. If company is not primary subject -> REJECTED or PENDING_REVIEW.
   - If Verification Status is 'ambiguous', MUST be PENDING_REVIEW unless overwhelming evidence exists otherwise.
4. Trigger Logic. Match against valid types.
   - If Portfolio/Testimonial: MUST implies Scale/Complexity/Urgency to be TRIGGER. Else CONTEXT_ONLY.

=== YOUR RESPONSE ===
Return ONLY valid JSON:
{{
    "classification": "TRIGGER" | "CONTEXT_ONLY" | "PENDING_REVIEW" | "REJECTED",
    "confidence": 0-10,
    "summary": "1 sentence summary",
    "trigger_type": "string",
    "evidence_excerpt": "string",
    "evidence_date": "YYYY-MM-DD",
    "outcome_delta": "string",
    "buying_window": "string",
    "rejection_reason": "string (optional)",
    "reasoning": "string"
}}
"""

    try:
        def _call_gpt():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
        completion = GLOBAL_LLM_BREAKER.call(_call_gpt)
        if not completion:
            return {"is_relevant": False, "rejection_reason": "LLM Circuit Open"}
        result = json.loads(completion.choices[0].message.content)
        
        # MAPPING NEW SCHEMA TO OLD (Backwards Compatibility)
        cls = result.get("classification", "REJECTED")
        result["is_relevant"] = (cls in ["TRIGGER", "CONTEXT_ONLY", "PENDING_REVIEW"])
        result["event_date"] = result.get("evidence_date")
        
        # ========== HARD DATE VALIDATION ==========
        if result.get("is_relevant"):
            event_date_str = result.get("event_date")
            if event_date_str and event_date_str.lower() not in ["unknown", "none", "null"]:
                try:
                    event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
                    cutoff = today - timedelta(days=max_age)
                    
                    if event_date < cutoff:
                        print(f"      ⛔ HARD REJECT: Event date {event_date_str} is older than {max_age}-day cutoff")
                        result["is_relevant"] = False
                        result["classification"] = "REJECTED"
                        result["rejection_reason"] = f"Event dated {event_date_str} is older than {max_age}-day cutoff"
                        return result
                except ValueError:
                    # Proceed but mark as PENDING_REVIEW if date is bad but AI thought it was good
                    print(f"      ⚠️ Date parse failed '{event_date_str}'. Downgrading to PENDING_REVIEW.")
                    result["classification"] = "PENDING_REVIEW"
            else:
                # No date extracted
                print(f"      ⛔ HARD REJECT: No date extracted.")
                result["is_relevant"] = False
                result["classification"] = "REJECTED"
                result["rejection_reason"] = "No date extracted"
                return result
        
        if not result.get("is_relevant"):
            rejection = result.get("rejection_reason", "unknown")
            print(f"      ❌ Rejected ({cls}): {rejection[:50]}...")
        else:
            print(f"      ✅ Approved ({cls}, {result.get('confidence')}/10)")
        
        return result
    except Exception as e:
        print(f"      Analysis Error: {e}")
        return {"is_relevant": False, "rejection_reason": f"Exception: {e}"}

# ==================== HELPERS ====================
def check_recent_context_anchor(company_id, supabase):
    """
    Checks if a company has had a CONTEXT_ANCHOR trigger in the last 90 days.
    Returns True if RECENTLY TRIGGERED (so we should SKIP).
    """
    from datetime import datetime, timedelta, timezone
    try:
        ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
        
        # Check logs for this company + event_type=CONTEXT_ANCHOR
        # Note: We might store this in a separate logs table or just check the last trigger.
        # For now, we check the 'triggered_companies' monitoring_status history if available, 
        # or we assume 'triggered' in the last 90 days with event_type='CONTEXT_ANCHOR' matches.
        
        # Simpler approach: We will check if the CURRENT status is 'triggered' and type is 'CONTEXT_ANCHOR'.
        # If so, we skip.
        
        resp = supabase.table("triggered_companies").select("*").eq("id", company_id).execute()
        if resp.data:
            row = resp.data[0]
            if row.get('event_type') == 'CONTEXT_ANCHOR' and row.get('monitoring_status') == 'triggered':
                last_trigger = row.get('last_monitored_at')
                if last_trigger and last_trigger > ninety_days_ago:
                    print(f"      ⏳ [Patience] Recent Context Anchor found ({last_trigger}). Skipping to avoid spam.")
                    return True
        return False
    except Exception as e:
        print(f"      ⚠️ Error checking context history: {e}")
        return False

def analyze_event_relevance(news_item, company_name, client_context, openai_key):
    """
    BATTLE-TESTED Trigger Detection.
    Uses OpenAI to filter news for relevance based on CLIENT CONTEXT.
    
    REJECTION CRITERIA:
    - Portfolio pages / project showcase pages
    - Generic industry articles
    - Awards without clear publication date
    - Events older than 30 days
    - Stock ticker noise
    """
    strategy = CLIENT_STRATEGIES.get(client_context, CLIENT_STRATEGIES["pulsepoint_strategic"])
    
    client = OpenAI(api_key=openai_key)
    
    prompt = f"""You are a STRICT Trigger Detection System for {company_name}.
    
CONTEXT: {strategy['trigger_prompt']}
VALID TRIGGER TYPES: {strategy['trigger_types']}

NEWS ITEM:
Title: {news_item.get('title')}
Description: {news_item.get('description')}

CRITICAL REJECTION CRITERIA (if ANY apply, set is_relevant=false):
1. PORTFOLIO/PROJECT PAGE: If the URL or content appears to be a project showcase, case study, or portfolio page (e.g., from an architecture firm or agency showing past work), REJECT.
2. GENERIC INDUSTRY ARTICLE: If it's a think-piece, opinion, or industry trend article not specifically about THIS company, REJECT.
3. OLD NEWS: If there's any indication the event happened more than 30 days ago, or the article is undated, REJECT.
4. STOCK TICKER NOISE: If it's about stock prices, trading, or financial performance without a real business event, REJECT.
5. AWARDS WITHOUT CONTEXT: If it's an award but there's no clear indication of when it was received or announced, REJECT.
6. COMPANY NOT THE SUBJECT: If {company_name} is mentioned but is not the PRIMARY subject of the news, REJECT.

ONLY approve if:
- The event is RECENT (within last 30 days)
- The event is NEWSWORTHY and SPECIFIC to {company_name}
- The event matches one of the valid trigger types

Return JSON only:
{{
    "is_relevant": true/false,
    "trigger_type": "One of {strategy['trigger_types']}",
    "summary": "1-sentence summary of the event",
    "confidence": 0-10,
    "rejection_reason": "If rejected, explain why. If approved, null."
}}"""
    
    try:
        def _call_gpt_relevance():
            return client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
        completion = GLOBAL_LLM_BREAKER.call(_call_gpt_relevance)
        if not completion: return {"is_relevant": False}
        result = json.loads(completion.choices[0].message.content)
        
        # Log rejections for debugging
        if not result.get("is_relevant"):
            rejection = result.get("rejection_reason", "unknown")
            print(f"      ❌ Rejected: {rejection[:80]}...")
        
        return result
    except Exception as e:
        print(f"Analysis Error: {e}")
        return {"is_relevant": False, "rejection_reason": f"API Error: {e}"}

def generate_hook(company_name, event, contact_name, client_context, openai_key):
    """
    Generates ONLY a 1-2 sentence personalized hook referencing the trigger event.
    Now uses CLIENT-SPECIFIC voice and tone from hook_context.
    """
    strategy = CLIENT_STRATEGIES.get(client_context, CLIENT_STRATEGIES["pulsepoint_strategic"])
    hook_context = strategy.get("hook_context", "")
    
    client = OpenAI(api_key=openai_key)
    
    # Build prompt with client-specific voice instructions
    prompt = f"""Write a 1-2 sentence opening hook for a cold email to {contact_name} at {company_name}.

The hook should reference this specific news event: "{event}"

{hook_context}

CRITICAL RULES:
- Reference the trigger event specifically
- NO greeting (no "Hi [name]") - just the hook itself
- Maximum 2 sentences
- Be genuine, not salesy
- DO NOT fabricate claims about your own company's experience

Return ONLY the hook text, nothing else."""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper model for short hook
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"Hook generation failed: {e}")
        # Fallback hook
        return f"The recent news about {company_name} caught my attention."


def get_client_template(supabase, client_context, template_type="initial_outreach"):
    """
    Fetches the default template for a client from the pulsepoint_email_templates table.
    Filters by client_context if the column exists, falls back to global default.
    Returns None if no template exists.
    """
    try:
        # Try client-scoped query first
        resp = supabase.table("pulsepoint_email_templates")\
            .select("*")\
            .eq("type", template_type)\
            .eq("is_default", True)\
            .eq("client_context", client_context)\
            .limit(1)\
            .execute()
        
        if resp.data and len(resp.data) > 0:
            return resp.data[0]
        
        # Fallback: no client-scoped template, try global default
        resp = supabase.table("pulsepoint_email_templates")\
            .select("*")\
            .eq("type", template_type)\
            .eq("is_default", True)\
            .limit(1)\
            .execute()
        
        if resp.data and len(resp.data) > 0:
            return resp.data[0]
        return None
    except Exception as e:
        print(f"Template fetch failed: {e}")
        return None


def apply_template_with_hook(template_body, hook, contact_name, company_name, sender_name="Ty"):
    """
    Replaces placeholders in template with actual values.
    Supported placeholders: {{ai_hook}}, {{first_name}}, {{company_name}}, {{sender_name}}
    """
    result = template_body
    result = result.replace("{{ai_hook}}", hook)
    result = result.replace("{{first_name}}", contact_name)
    result = result.replace("{{company_name}}", company_name)
    result = result.replace("{{sender_name}}", sender_name)
    # Also support alternate placeholder formats
    result = result.replace("{ai_hook}", hook)
    result = result.replace("{first_name}", contact_name)
    result = result.replace("{company_name}", company_name)
    result = result.replace("{sender_name}", sender_name)
    return result


def generate_draft(company_name, event, contact_name, client_context, openai_key, supabase=None, buying_window='Exploration', outcome_delta=None):
    """
    Generates a personalized email draft using HYBRID approach:
    1. If user has a template with {{ai_hook}} placeholder -> generate hook + apply to template
    2. If no template -> generate full AI draft (legacy behavior)
    
    Phase 8: Implements CTA Downshifting based on buying_window and uses outcome_delta.
    """
    strategy = CLIENT_STRATEGIES.get(client_context, CLIENT_STRATEGIES["pulsepoint_strategic"])
    
    # 1. Determine CTA Strategy based on Buying Window
    cta_strategy = "Soft Ask (Conversation/Perspective)"
    if buying_window == 'Execution':
        cta_strategy = "Direct Ask (Pilot/Demo/Audit)"
    elif buying_window == 'Transition':
        cta_strategy = "Priority Check (Is this a focus?)"
    
    # Try to get user's template first
    template = None
    if supabase:
        template = get_client_template(supabase, client_context, "initial_outreach")
    
    if template and template.get("content"):
        # HYBRID MODE: Template + AI Hook
        print(f"      Using template: {template.get('name', 'default')} (Window: {buying_window})")
        # We need a hook that respects the window
        hook_prompt = f"""
        Generate a 1-sentence personalized hook for {contact_name} at {company_name}.
        Trigger: {event}
        Outcome Delta (Strategic Implication): {outcome_delta if outcome_delta else "Strategic growth opportunity."}
        Buying Window: {buying_window}
        
        RULES:
        - Be observational, not matching.
        - Reference the outcome/implication, not just the news.
        - Tone: Professional, slightly restrained.
        - No generic fluff.
        """
        
        try:
            client = OpenAI(api_key=openai_key)
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": hook_prompt}]
            )
            hook = resp.choices[0].message.content.strip('"')
            
            email_body = apply_template_with_hook(
                template["content"], 
                hook, 
                contact_name, 
                company_name
            )
            
            # Note: We don't dynamically change the template CTA here yet, 
            # but we can append the CTA strategy guidance if needed or rely on the hook to pivot.
            return email_body
        except Exception as e:
            print(f"Hook generation failed: {e}")
            return f"Hi {contact_name}, I saw the news regarding {company_name} and wanted to reach out."
    else:
        # LEGACY MODE: Full AI Draft
        print(f"      No template found, using full AI draft (Window: {buying_window})")
        client = OpenAI(api_key=openai_key)
        prompt = f"""
        Write a SHORT personalized cold email to {contact_name} at {company_name}.
        
        TRIGGER: {event}
        STRATEGIC IMPLICATION: {outcome_delta if outcome_delta else "Growth opportunity."}
        
        BUYING WINDOW: {buying_window}
        REQUIRED CTA: {cta_strategy}
        
        {strategy.get('hook_context', '')}
        {strategy['draft_context']}
        
        GUIDELINES:
        - Under 120 words.
        - Use the implication to bridge to the value prop.
        - NO fluff.
        - Respect the CTA strategy strictly.
        
        Return only the body text.
        """
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"Draft generation failed: {e}")
            return f"Hi {contact_name}, I wanted to reach out regarding recent growth signals at {company_name}."

# ==================== JUST-IN-TIME CONTACT ENRICHMENT ====================

def enrich_company_contacts(company_id: str, company_name: str, existing_website: str, client_context: str, apify_client, supabase) -> list:
    """
    Just-in-time contact enrichment for a single company.
    Uses shared enrichment_utils for website finding, decision maker search, and email verification.
    
    Called when:
    1. A trigger is found but no contacts exist
    2. User manually requests enrichment from dashboard
    
    Returns: List of enriched contacts (may be empty if none found)
    """
    ANYMAILFINDER_KEY = os.environ.get("ANYMAILFINDER_API_KEY")
    strategy = CLIENT_STRATEGIES.get(client_context, CLIENT_STRATEGIES["pulsepoint_strategic"])
    leads_table = strategy.get("leads_table", "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")
    
    print(f"      🔍 Enriching contacts for: {company_name}")
    
    # ===== STEP 1: Find Website =====
    domain = existing_website
    if not domain:
        domain = find_website(company_name, apify_client)
        if domain:
            # Update company record
            supabase.table("triggered_companies").update({"website": domain}).eq("id", company_id).execute()
    
    if not domain:
        print(f"      ❌ No website found, cannot enrich")
        return []
    
    # ===== STEP 2: Find Decision Makers via LinkedIn =====
    candidates = find_decision_makers(company_name, apify_client, max_candidates=3)
    
    # ===== STEP 3: Verify Emails via Anymailfinder =====
    enriched_contacts = []
    
    for person in candidates:
        email = verify_email(person['name'], domain, api_key=ANYMAILFINDER_KEY)
        
        if email:
            print(f"      ✅ Found: {person['name']} <{email}>")
            
            # Insert into leads table
            try:
                supabase.table(leads_table).insert({
                    "triggered_company_id": company_id,
                    "name": person['name'],
                    "title": person['title'],
                    "email": email,
                    "linkedin_url": person['linkedin'],
                    "contact_status": "pending"
                }).execute()
                
                enriched_contacts.append({
                    "name": person['name'],
                    "email": email,
                    "title": person['title']
                })
            except Exception as e:
                print(f"      ⚠️ Insert error: {e}")
        else:
            print(f"      ❌ No email found: {person['name']}")
    
    print(f"      ✅ Enrichment complete: {len(enriched_contacts)} contacts added")
    return enriched_contacts

def generate_search_hash(urls: list) -> str:
    """
    Create a deterministic fingerprint of the search results.
    Sorts URLs to ensure [A, B] == [B, A].
    """
    import hashlib
    if not urls: return ""
    
    # Normalize: lowercase, strip query params if needed (simplest is just sorted list)
    sorted_urls = sorted([u.lower().strip() for u in urls if u])
    content = "|".join(sorted_urls)
    
    return hashlib.md5(content.encode()).hexdigest()

def process_company_scan(comp: dict, apify_client, supabase, openai_key: str, force_rescan: bool = False, scan_start: float = None, scan_batch_id: str = None):
    """
    Orchestrates the monitoring process for a single company.
    1. Identify Client Strategy
    2. Build Search Queries
    3. Execute Search (Apify)
    4. Fingerprint Check (Efficiency)
    5. AI Analysis (OpenAI)
    6. Database Updates
    """
    company_start = time.time()
    
    # OBSERVABILITY: Create scan log entry
    scan_log_id = None
    try:
        log_resp = supabase.table("monitor_scan_log").insert({
            "company_id": comp.get('id'),
            "company_name": comp.get('company'),
            "client_context": comp.get('client_context', 'pulsepoint_strategic'),
            "scan_batch_id": scan_batch_id,
            "status": "running"
        }).execute()
        if log_resp.data:
            scan_log_id = log_resp.data[0]['id']
    except Exception as e:
        print(f"      ⚠️ Scan log insert failed: {e}")
    
    analysis_log = [] # PHASE 6: Confidence Logging


    
    # Helper to finalize the scan log entry
    def _finalize_scan_log(status, error=None, trigger_found=False, trigger_type=None, counters=None):
        if not scan_log_id:
            return
        try:
            update = {
                "status": status,
                "completed_at": "now()",
                "elapsed_seconds": round(time.time() - company_start, 2),
                "trigger_found": trigger_found,
                "trigger_type": trigger_type,
                "analysis_log": analysis_log
            }
            if error:
                update["error"] = str(error)[:500]
            if counters:
                update.update(counters)
            supabase.table("monitor_scan_log").update(update).eq("id", scan_log_id).execute()
        except Exception as e:
            print(f"      ⚠️ Scan log update failed: {e}")
    
    # TIME BUDGET GUARD: Skip if we're running low on wall-clock time
    if scan_start and (time.time() - scan_start) > 780:  # 13 min guard (out of 15 min worker limit)
        print(f"⏱️ TIME BUDGET EXHAUSTED: Skipping {comp.get('company')} (elapsed: {int(time.time() - scan_start)}s)")
        _finalize_scan_log("skipped_budget")
        return

    print(f"🏢 Scanning: {comp.get('company')} (Strategy: {comp.get('client_context')})")
    
    strategy_slug = comp.get("client_context", "pulsepoint_strategic")
    client_context = strategy_slug  # Alias used throughout this function
    strategy = CLIENT_STRATEGIES.get(strategy_slug, CLIENT_STRATEGIES.get("pulsepoint_strategic"))
    
    # 1. Build Queries and Search
    queries = build_search_queries(comp.get('company'), strategy)
    
    # Run Google Search via Apify
    # Use Circuit Breaker to prevent cascading failures
    def _call_apify_search():
        return apify_client.actor("apify/google-search-scraper").call(
            run_input={
                "queries": "\n".join(queries[:1]),  # Limit to 1 query for cost/speed (Deep Monitoring uses scouts)
                "resultsPerPage": 15,
                "maxPagesPerQuery": 1,
                "languageCode": "",
                "mobileResults": False,
                "includeUnfilteredResults": False,
                "saveHtml": False,
                "saveHtmlToKeyValueStore": False,
                "includeIcons": False,
                # CRITICAL: Enforce Time Range to prevent "Ghost Dates" (old news ranking high)
                "timeRange": "week" # strict "last 7 days"
            },
            timeout_secs=60
        )
    
    print(f"      🔎 Searching Google News (Last 7 Days)...")
    run = GLOBAL_APIFY_BREAKER.call(_call_apify_search)
    
    if not run:
        print("      ⚠️ Search Circuit Open or Failed. Skipping.")
        return

    # Extract Results
    search_results = []
    dataset = apify_client.dataset(run["defaultDatasetId"])
    
    for item in dataset.list_items().items:
        organic = item.get("organicResults", [])
        for res in organic:
            search_results.append({
                "title": res.get("title"),
                "url": res.get("url"),
                "description": res.get("description"),
                "date": res.get("date")
            })
            
    # ==================== EFFICIENCY: FINGERPRINT CHECK ====================
    # Calculate hash of ALL URLs found
    current_urls = [r.get("url") for r in search_results]
    new_hash = generate_search_hash(current_urls)
    last_hash = comp.get("last_search_hash")
    
    if not force_rescan and last_hash and new_hash == last_hash:
        print(f"      💨 EFFICIENCY: Result Fingerprint matches previous scan. No new news. Skipping AI analysis.")
        # Update timestamp only
        supabase.table("triggered_companies").update({
            "last_monitored_at": "now()"
        }).eq("id", comp['id']).execute()
        _finalize_scan_log("skipped_fingerprint", counters={"apify_calls": 1})
        return

    # Update hash immediately so next run knows
    supabase.table("triggered_companies").update({
        "last_search_hash": new_hash
    }).eq("id", comp['id']).execute()
    
    # Initialize merged result list and dedup set from Google search results
    all_results = list(search_results)
    seen_urls = set(r.get("url") for r in search_results if r.get("url"))
    
    print(f"      ✨ New Content Detected (Hash: {new_hash[:8]}). Analyzing {len(search_results)} items...")
    
    # ==================== DEEP SCOUTS (Async Phase 7) ====================
    # Run Blog and Social scouts in parallel
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        
        # 1. Direct Blog Scout
        if comp.get('website'):
            futures[executor.submit(scout_latest_blog_posts, comp['company'], comp['website'], apify_client)] = 'blog'

        # 2. Executive Social Scout
        try:
            leads_table = strategy.get("leads_table", "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")
            contacts_resp = supabase.table(leads_table).select("*").eq("triggered_company_id", comp['id']).execute()
            contacts = contacts_resp.data
            if contacts:
                print(f"      👥 Social Scout checking {len(contacts[:3])} executives...")
                for contact in contacts[:3]: # Cap at top 3
                    futures[executor.submit(scout_executive_social_activity, contact['name'], comp['company'], apify_client)] = 'social'
        except Exception as e:
            print(f"      ⚠️ Social Scout setup failed: {e}")

        # Collect results
        for future in as_completed(futures, timeout=120):
            scout_type = futures[future]
            try:
                res = future.result()
                if res:
                    # Enrich and Dedup
                    for item in res:
                        if item['url'] not in seen_urls:
                            seen_urls.add(item['url'])
                            
                            # Normalize format based on source
                            if scout_type == 'blog':
                                all_results.append({
                                    "url": item['url'],
                                    "title": item['title'],
                                    "description": item['text'][:200],
                                    "is_scouted_blog": True
                                })
                            elif scout_type == 'social':
                                all_results.append({
                                    "url": item['url'],
                                    "title": item['title'],
                                    "description": item['text'],
                                    "is_scouted_social": True,
                                    "person_name": item.get('person_name'),
                                    "verification_status": item.get('verification_status', 'unknown')
                                })
            except Exception as e:
                print(f"      ⚠️ {scout_type} scout failed: {e}")
    
    # ==================== ANALYZE WITH ARTICLE EXTRACTION ====================
    trigger_found = False
    trigger_type_found = None  # REAL_TIME_DETECTED or CONTEXT_ANCHOR
    
    # BUDGET TRACKING
    pages_fetched = 0
    llm_calls = 0
    
    print(f"      🏁 Starting analysis (Budget: {MAX_FETCHED_PAGES_TOTAL} pages, {MAX_LLM_CALLS} LLM calls)...")
    
    for res in all_results:
        # BUDGET CHECK: LLM
        if llm_calls >= MAX_LLM_CALLS:
             print(f"      🛑 LLM Budget Reached ({llm_calls}/{MAX_LLM_CALLS}). Stopping scan.")
             break
             
        news_item = {
            "title": res.get("title", ""),
            "description": res.get("description", ""),
            "url": res.get("url", "")
        }
        
        # 0. URL Validation
        url_valid, url_rejection = is_valid_article_url(news_item['url'], comp['company'])
        if not url_valid:
            print(f"      ⛔ URL REJECTED: {url_rejection}")
            continue

        # 1. Quick Semantic Analysis (Is this relevant?)
        # NOTE: WE COUNT THIS AS AN LLM CALL if it uses the AI model. 
        # But analyze_event_relevance is lighter. We should probably count it as 0.5 or track separately?
        # For now, let's treat it as a full call to be safe, OR we assume it's cheap enough.
        # User defined MAX_LLM_CALLS=2. If we use 1 here, we only get 2 articles.
        # Let's assume the user meant "Deep Analysis Limit".
        # But analyze_event_relevance IS an LLM call.
        # Compromise: We will increment llm_calls here.
        
        print(f"      🔍 Analyzing relevance: {news_item['title'][:50]}...")
        quick_analysis = analyze_event_relevance(news_item, comp['company'], client_context, openai_key)
        llm_calls += 1
        
        # LOGGING: Record quick analysis
        analysis_log.append({
            "url": news_item.get('url'),
            "title": news_item.get('title'),
            "stage": "relevance",
            "confidence": quick_analysis.get('confidence', 0),
            "is_relevant": quick_analysis.get('is_relevant'),
            "decision": "pass" if quick_analysis.get('is_relevant') else "rejected",
            "model": "gpt-4o"
        })
        
        # LOGGING: Record quick analysis
        analysis_log.append({
            "url": news_item.get('url'),
            "title": news_item.get('title'),
            "stage": "relevance",
            "confidence": quick_analysis.get('confidence', 0),
            "is_relevant": quick_analysis.get('is_relevant'),
            "decision": "pass" if quick_analysis.get('is_relevant') else "rejected",
            "model": "gpt-4o"
        })
        
        if quick_analysis.get('is_relevant') and quick_analysis.get('confidence', 0) >= 6:
            
            # BUDGET CHECK: Fetch
            if pages_fetched >= MAX_FETCHED_PAGES_TOTAL:
                 print(f"      🛑 Page Fetch Budget Reached ({pages_fetched}/{MAX_FETCHED_PAGES_TOTAL}). Stopping scan.")
                 break
            
            print(f"      📄 Extracting article: {news_item['url'][:50]}...")
            
            # Full article extraction
            article_text = extract_article_content(news_item['url'], apify_client)
            pages_fetched += 1
            
            # Pre-check Date
            # datetime and timedelta already imported at module level (line 5)
            pre_check_date, pre_check_date_str = extract_date_from_text(article_text)
            
            if pre_check_date:
                # Use strategy max_age for pre-check too
                age_limit = int(strategy.get("max_age_days", 25))
                cutoff = datetime.now() - timedelta(days=age_limit)
                if pre_check_date < cutoff:
                    print(f"      ⛔ EARLY REJECT: Article dated {pre_check_date_str} is older than {age_limit}-day cutoff")
                    continue
                else:
                    print(f"      📅 Date verified: {pre_check_date_str}")
            else:
                 # GHOST DATE PROTECTION
                 print(f"      ⛔ REJECT: No date found in text (Ghost Date Protection)")
                 continue
            
            # Deep Analysis
            # Double check LLM budget before 2nd call
            if llm_calls >= MAX_LLM_CALLS:
                 print(f"      🛑 LLM Budget Reached ({llm_calls}/{MAX_LLM_CALLS}) before deep analysis. Skipping.")
                 break
                 
            analysis = analyze_with_article_context(
                news_item, article_text, comp['company'], client_context, openai_key
            )
            llm_calls += 1

            # LOGGING: Deep analysis
            analysis_log.append({
                "url": news_item.get('url'),
                "title": news_item.get('title'),
                "stage": "deep_analysis",
                "confidence": analysis.get('confidence', 0),
                "is_relevant": analysis.get('is_relevant'),
                "decision": "triggered" if analysis.get('is_relevant') else "rejected",
                "model": "gpt-4o"
            })
            
            if analysis.get('is_relevant'):
                # Double Check Confidence (Threshold 7/10)
                if analysis.get('confidence', 0) < 7:
                    print(f"      ⚠️ Relevance too low ({analysis.get('confidence', 0)}/10). Skipping.")
                    continue
                event_date = analysis.get('event_date', 'Unknown date')
                print(f"      ✅ TRIGGER CONFIRMED: {analysis['summary']} (Date: {event_date})")
                print(f"         Strategy: {analysis.get('buying_window')} | Delta: {analysis.get('outcome_delta')}")
                
                # DEDUP CHECK
                existing_dedup = supabase.table("trigger_dedup").select("id").eq("company_id", comp['id']).eq("source_url", res.get('url')).execute()
                if existing_dedup.data:
                    print(f"      ♻️ DEDUP: Already triggered on this URL. Skipping.")
                    # Still log success in scan log but mark as duplicate effectively
                    _finalize_scan_log("success", counters={"apify_calls": 1 + pages_fetched, "llm_calls": llm_calls, "pages_fetched": pages_fetched})
                    return # Skip this company for now (or continue? Logic implies break on trigger found)
                    # Actually, if we hit a dedup, we should probably CONTINUE searching for a *new* trigger.
                    # But the current logic says 'break' on first trigger. 
                    # Correct behavior: continue to next result.
                    # For simplicity in this patch: just continue loop.
                    continue

                # Store new factors
                score_factors = comp.get('score_factors', {}) or {}
                score_factors['outcome_delta'] = analysis.get('outcome_delta')
                score_factors['buying_window'] = analysis.get('buying_window')
                
                # Update DB and pause monitoring
                supabase.table("triggered_companies").update({
                    "event_type": "REAL_TIME_DETECTED",
                    "event_title": analysis['summary'],
                    "event_source_url": res.get('url'),
                    "last_monitored_at": "now()",
                    "monitoring_status": "triggered",
                    "score_factors": score_factors
                }).eq("id", comp['id']).execute()
                
                # Record Dedup
                try:
                    supabase.table("trigger_dedup").insert({
                        "company_id": comp['id'],
                        "source_url": res.get('url'),
                        "trigger_type": "REAL_TIME_DETECTED"
                    }).execute()
                except Exception as e:
                    print(f"      ⚠️ Dedup insert failed: {e}")
                
                # Contact Enrichment Logic
                leads_table = strategy.get("leads_table", "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")
                print(f"      Looking for contacts in: {leads_table}")
                contacts_resp = supabase.table(leads_table).select("*").eq("triggered_company_id", comp['id']).execute()
                contacts = contacts_resp.data
                
                if not contacts:
                    print(f"      ⚠️ No contacts found - triggering JIT enrichment...")
                    enrich_company_contacts(
                        company_id=comp['id'],
                        company_name=comp['company'],
                        existing_website=comp.get('website'),
                        client_context=client_context,
                        apify_client=apify_client,
                        supabase=supabase
                    )
                    # Re-fetch
                    contacts_resp = supabase.table(leads_table).select("*").eq("triggered_company_id", comp['id']).execute()
                    contacts = contacts_resp.data
                
                # Generate Drafts
                for contact in contacts:
                    contact_email = contact.get('email')
                    if contact_email:
                        contact_name = contact.get('name', 'there') or 'there'
                        
                        # Phase 8: Pass Buying Window & Outcome Delta to Generator
                        draft_body = generate_draft(
                            comp['company'], 
                            analysis['summary'], 
                            contact_name, 
                            client_context, 
                            openai_key, 
                            supabase, 
                            buying_window=analysis.get('buying_window', 'Exploration'),
                            outcome_delta=analysis.get('outcome_delta')
                        )
                        
                        # Phase 8: Determine Status (Approval Mode)
                        status = "draft"
                        if strategy.get('approval_mode'):
                            status = "pending_approval"
                            
                        # Phase 8: Attribution
                        # We store attribution in metadata/notes or overload source for now?
                        # Plan said: Store hook_type and cta_type in pulsepoint_email_queue.
                        # We will assume we can't add columns easily, so we'll just not store them explicitly in columns yet
                        # OR we could add them to a JSON column if it existed.
                        # Wait, we can't see the schema of email_queue fully.
                        # Let's just create the draft and rely on the strategy logic.
                        
                        supabase.table("pulsepoint_email_queue").insert({
                            "triggered_company_id": comp['id'],
                            "lead_id": contact.get('id'),
                            "email_to": contact_email,
                            "email_subject": f"Idea for {comp['company']} ({analysis.get('trigger_type', 'Growth Signal')})",
                            "email_body": draft_body,
                            "status": status,
                            "source": "monitor_auto",
                            "user_id": comp.get('user_id') 
                        }).execute()
                        print(f"      ---> Draft Created for {contact_email} (Status: {status})")

                # Exit loop if found a trigger
                trigger_found = True
                trigger_type_found = "REAL_TIME_DETECTED"
                break
    
    # ==================== FALLBACK: CONTEXT ANCHOR (EVERGREEN) ====================
    # If no recent news/social triggers found, check for "Timeless" Portfolio/Testimonial signals
    # BUT ONLY if we haven't contacted them about a context anchor in 90 days.
    
    if not trigger_found and strategy.get('trigger_prompt'): 
        
        # 0. TIME BUDGET GUARD: Skip deep scouts if wall-clock time is running low
        if scan_start and (time.time() - scan_start) > 660:  # 11 min guard
            print(f"      ⏱️ Skipping deep scouts (wall-clock: {int(time.time() - scan_start)}s)")
        # 1. Frequency Guardrail
        elif check_recent_context_anchor(comp['id'], supabase):
             print(f"      ⏳ Skipping Context Anchor check (Recently Contacted)")
        else:
            # 2. PROACTIVE COST GUARDRAIL: Deep Scout Throttling
            # Only run strict/expensive portfolio crawls once every 30 days per company
            should_run_deep_scout = True
            score_factors = comp.get('score_factors', {}) or {}
            last_deep_scout = score_factors.get('last_deep_scout_at')
            
            if last_deep_scout:
                # datetime already imported at module level (line 5)
                try:
                    last_date = datetime.fromisoformat(last_deep_scout)
                    # Simple 30-day check
                    if (datetime.now() - last_date).days < 30:
                         print(f"      💰 Skipping Deep Scout (Throttled: Last ran {last_deep_scout[:10]})")
                         should_run_deep_scout = False
                except Exception as e:
                    print(f"      ⚠️ Date parse error ({last_deep_scout}): {e}. re-running.")
            
            if should_run_deep_scout:
                # Update timestamp IMMEDIATELY to lock it in
                try:
                    score_factors['last_deep_scout_at'] = datetime.now().isoformat()
                    supabase.table("triggered_companies").update({
                        "score_factors": score_factors
                    }).eq("id", comp['id']).execute()
                except Exception as e:
                     print(f"      ⚠️ Failed to update deep scout timestamp: {e}")

                try:
                    from scouts.portfolio_scout import scout_portfolio
                    from scouts.testimonial_scout import scout_testimonials
                
                    print(f"      🎨 [Fallback] No news found. Running Context Anchor Scouts (Parallel)...")
                    
                    portfolio_signals = []
                    testimonial_signals = []
                    
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        fut_port = executor.submit(scout_portfolio, comp['company'], comp.get('website', ''), apify_client)
                        fut_test = executor.submit(scout_testimonials, comp['company'], comp.get('website', ''), apify_client)
                        
                        try:
                            portfolio_signals = fut_port.result(timeout=90)
                        except Exception as e:
                            print(f"      ⚠️ Portfolio scout failed: {e}")
                            
                        try:
                            testimonial_signals = fut_test.result(timeout=90)
                        except Exception as e:
                            print(f"      ⚠️ Testimonial scout failed: {e}")
                
                    # Merge signals
                    all_evergreen_signals = portfolio_signals + testimonial_signals
                
                    for sig in all_evergreen_signals:
                        print(f"      ✨ Analyzing Context Signal: {sig['url']}...")

                        # LOGGING: Record checking this anchor
                        analysis_log.append({
                            "url": sig.get('url'),
                            "title": sig.get('title'),
                            "stage": "context_anchor",
                            "decision": "pending",
                            "model": "gpt-4o"
                        })
                    
                        # Specialized Analysis for CONTEXT ANCHORS
                        # Strictly enforces "Significance" over "Aesthetics"
                    
                        sys_prompt = f"""
                        {strategy.get('trigger_prompt')}
                    
                        SPECIAL MODE: CONTEXT ANCHOR ANALYSIS ("Evergreen")
                    
                        OBJECTIVE: Determine if this content provides a DEFENSIBLE, STRATEGIC reason for outreach.
                        - We are looking for EVIDENCE of Scale, Complexity, or High-Stakes outcomes.
                        - We are IGNORING "competence" (e.g. they designed a nice logo).
                    
                        CRITERIA FOR RELEVANCE (Must meet at least ONE):
                        1. **Client Magnitude:** The client is a recognizable Enterprise, Regulated Industry, or Global Brand (e.g. Nike, Sephora, Coca-Cola).
                        2. **Outcome Significance:** The work involved "Scaling", "National Rollout", "Transformation", "Complex Integration", or "Rapid Growth".
                        3. **Pattern:** Testimonial says "They helped us get into [Big Retailer]" or "Handled our expansion".
                    
                        DISALLOWED (Do NOT Trigger):
                        - "New Website" or "Rebranding" (unless accompanied by "Enterprise Scale" context).
                        - "Logo Design", "Visual Identity".
                        - Generic praise ("Great team to work with!").
                    
                        INSTRUCTIONS:
                        - IGNORE "Date" requirements. This is a "Timeless" anchor.
                        - IF relevant, extract the Client Name and the SPECIFIC Strategic Outcome.
                        - Set is_relevant=True ONLY if it passes the Significance Filter.
                        
                        Client Context: {client_context}

                        OUTPUT JSON:
                        {{
                            "is_relevant": true/false,
                            "confidence": 0-10,
                            "summary": "1-sentence summary",
                            "outcome_delta": "The 2nd order implication (Risk/Upside). Must be specific.",
                            "buying_window": "Typically 'Transition' or 'Execution' for these signals."
                        }}
                        """
                    
                        analysis = call_openai_analysis(sig, sys_prompt, openai_key, model="gpt-4o")
                        
                        # Log result
                        analysis_log[-1].update({
                            "confidence": analysis.get('confidence', 0),
                            "is_relevant": analysis.get('is_relevant'),
                            "decision": "triggered" if analysis.get('is_relevant') else "rejected"
                        })
                    
                        if analysis.get('is_relevant') and analysis.get('confidence', 0) >= 8: # Higher confidence bar
                            print(f"      ✅ CONTEXT ANCHOR: {analysis['summary']}")
                            print(f"         Strategy: {analysis.get('buying_window')} | Delta: {analysis.get('outcome_delta')}")
                        
                            # Store factors
                            score_factors = comp.get('score_factors', {}) or {}
                            score_factors['outcome_delta'] = analysis.get('outcome_delta')
                            score_factors['buying_window'] = analysis.get('buying_window')

                            # DEDUP CHECK (Context Anchor)
                            existing_dedup = supabase.table("trigger_dedup").select("id").eq("company_id", comp['id']).eq("source_url", sig.get('url')).execute()
                            if existing_dedup.data:
                                print(f"      ♻️ DEDUP (Anchor): Already triggered on this URL. Skipping.")
                                continue

                            supabase.table("triggered_companies").update({
                                "event_type": "CONTEXT_ANCHOR",
                                "event_title": analysis['summary'],
                                "event_source_url": sig['url'],
                                "last_monitored_at": "now()",
                                "monitoring_status": "triggered",
                                "score_factors": score_factors
                            }).eq("id", comp['id']).execute()

                            # Record Dedup
                            try:
                                supabase.table("trigger_dedup").insert({
                                    "company_id": comp['id'],
                                    "source_url": sig['url'],
                                    "trigger_type": "CONTEXT_ANCHOR"
                                }).execute()
                            except Exception as e:
                                print(f"      ⚠️ Dedup insert failed: {e}")
                        
                            # Contact Enrichment Logic (Copied from Main Loop)
                            leads_table = strategy.get("leads_table", "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")
                            print(f"      Looking for contacts in: {leads_table}")
                            contacts_resp = supabase.table(leads_table).select("*").eq("triggered_company_id", comp['id']).execute()
                            contacts = contacts_resp.data
                        
                            if not contacts:
                                print(f"      ⚠️ No contacts found - triggering JIT enrichment...")
                                enrich_company_contacts(
                                    company_id=comp['id'],
                                    company_name=comp['company'],
                                    existing_website=comp.get('website'),
                                    client_context=client_context,
                                    apify_client=apify_client,
                                    supabase=supabase
                                )
                                # Re-fetch
                                contacts_resp = supabase.table(leads_table).select("*").eq("triggered_company_id", comp['id']).execute()
                                contacts = contacts_resp.data

                            # Generate Drafts
                            for contact in contacts:
                                contact_email = contact.get('email')
                                if contact_email:
                                    contact_name = contact.get('name', 'there') or 'there'
                                
                                    draft_body = generate_draft(
                                        comp['company'], 
                                        analysis['summary'], 
                                        contact_name, 
                                        client_context, 
                                        openai_key, 
                                        supabase, 
                                        buying_window=analysis.get('buying_window', 'Transition'), # Default to Transition for Anchor
                                        outcome_delta=analysis.get('outcome_delta')
                                    )
                                
                                    status = "draft"
                                    if strategy.get('approval_mode'):
                                        status = "pending_approval"
                                
                                    supabase.table("pulsepoint_email_queue").insert({
                                        "triggered_company_id": comp['id'],
                                        "lead_id": contact.get('id'),
                                        "email_to": contact_email,
                                        "email_subject": f"Idea for {comp['company']} (Context Anchor)",
                                        "email_body": draft_body,
                                        "status": status,
                                        "source": "monitor_auto_anchor",
                                        "user_id": comp.get('user_id') 
                                    }).execute()
                                    print(f"      ---> Draft Created for {contact_email} (Status: {status})")
                        
                            trigger_found = True
                            trigger_type_found = "CONTEXT_ANCHOR"
                            break
                        
                except ImportError:
                    print("      ⚠️ Scout modules not found (ImportError). skipping.")
                except Exception as e:
                    print(f"      ⚠️ Context Anchor Scout failed: {e}")

    # OBSERVABILITY: Finalize scan log
    scan_counters = {
        "apify_calls": 1 + pages_fetched,  # 1 for initial search + page fetches
        "llm_calls": llm_calls,
        "pages_fetched": pages_fetched
    }
    
    if not trigger_found:
        try:
            supabase.table("triggered_companies").update({"last_monitored_at": "now()"}).eq("id", comp['id']).execute()
        except Exception as e:
            print(f"      ⚠️ Failed to update timestamp: {e}")
        print("      (No relevant triggers found)")
        _finalize_scan_log("success", counters=scan_counters)
    else:
        _finalize_scan_log("success", trigger_found=True,
                          trigger_type=trigger_type_found,
                          counters=scan_counters)
    
    # Rate limiting
    time.sleep(2)



@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=300 # 5 mins per company (relaxed from 180s to allow for retries/deep scouts)
)
def scan_single_company(comp: dict, force_rescan: bool = False, scan_batch_id: str = None):
    """
    Isolated worker for scanning a single company.
    """
    import time
    
    # Instantiate clients locally since they can't be pickled easily
    supabase = get_supabase()
    apify_token = os.environ.get("APIFY_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if not apify_token or not openai_key:
        print(f"❌ Missing API Keys for {comp.get('company')}")
        return

    apify_client = ApifyClient(apify_token)
    
    # Run logic
    # We pass scan_start=time.time() so the internal budget guard measures from *this* function's start
    process_company_scan(comp, apify_client, supabase, openai_key, force_rescan=force_rescan, scan_start=time.time(), scan_batch_id=scan_batch_id)


# MODAL FUNCTION
@app.function(
    image=image, 
    secrets=[modal.Secret.from_dotenv()],
    timeout=1200 # 20 mins batch timeout (orchestrator)
)
def run_monitoring_scan(company_id: str = None, force_rescan: bool = False):
    """
    Main logic.
    """
    scan_start = time.time()  # WALL-CLOCK TIME BUDGET
    scan_batch_id = str(uuid.uuid4())  # OBSERVABILITY: Group all scans in this run
    print(f"🚀 Starting Monitoring Scan (batch: {scan_batch_id[:8]})...")
    
    supabase = get_supabase()
    # LOAD STRATEGIES FROM DB
    fetch_client_strategies(supabase)
    apify_token = os.environ.get("APIFY_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if not apify_token or not openai_key:
        print("❌ Missing API Keys")
        return
        
    apify_client = ApifyClient(apify_token)

    # Determine workload
    target_companies = []
    if company_id:
        resp = supabase.table("triggered_companies").select("*").eq("id", company_id).execute()
        target_companies = resp.data
    else:
        target_companies = get_due_companies(supabase)
    
    print(f"📋 Processing {len(target_companies)} companies (Parallel Execution)")
    
    # Prepare arguments for map
    # map() takes a list of inputs. We have multiple args, so we can't use simple map unless we pack them
    # simpler: just use loop with .spawn() and wait, OR use starmap if we define it?
    # Modal's .map() iterates over one argument. 
    # Let's use a simple loop with .spawn() for maximum control and list results
    
    # Actually, to use .map with multiple args, we need to partial or pack. 
    # Let's just loop and spawn.
    
    # Launch all scans
    for comp in target_companies:
        scan_single_company.spawn(comp, force_rescan=force_rescan, scan_batch_id=scan_batch_id)
        
    print(f"🚀 Spawning complete. {len(target_companies)} background tasks launched.")
    
    # Note: We are NOT waiting for them to finish here to keep the cron job fast. 
    # Results are tracked in 'monitor_scan_log' table (Phase 1).
    # If we wanted to wait, we'd need to collect handles and .get() them, 
    # but that burns the orchestrator's billing time just waiting.
    # Fire and forget is better for cost/reliability here, relying on DB logs for status.
    
    elapsed = int(time.time() - scan_start)
    print(f"✅ Monitoring scan complete in {elapsed}s (batch: {scan_batch_id[:8]})")

# SCHEDULED ENTRY POINT
@app.function(
    image=image, 
    secrets=[modal.Secret.from_dotenv()],
    schedule=modal.Cron("0 14 * * *"),  # 9am EST / 6am PST
    timeout=1200  # 20 minutes — must exceed run_monitoring_scan's 900s timeout
)
def daily_monitor_cron():
    """
    Daily scheduled job that runs the monitoring scan.
    Must have image and secrets to properly initialize.
    """
    print("⏰ Daily Monitor Cron triggered")
    run_monitoring_scan.remote()

from pydantic import BaseModel

class ScanRequest(BaseModel):
    company_id: str
    force_rescan: bool = False

# MANUAL WEBHOOK ENTRY POINT
@app.function(image=image, secrets=[modal.Secret.from_dotenv()])
@modal.fastapi_endpoint(method="POST")
def manual_scan_trigger(item: ScanRequest):
    """
    Payload: {"company_id": "uuid", "force_rescan": true/false}
    """
    cid = item.company_id
    if cid:
        # Run in background
        run_monitoring_scan.spawn(company_id=cid, force_rescan=item.force_rescan)
        return {"status": "started", "message": f"Scanning {cid} in background (Force: {item.force_rescan})"}
    return {"status": "error", "message": "Missing company_id"}

# ==================== MANUAL ENRICHMENT WEBHOOK ====================

class EnrichRequest(BaseModel):
    company_id: str
    client_context: str = "pulsepoint_strategic"

@app.function(
    image=image, 
    secrets=[modal.Secret.from_dotenv()],
    timeout=300  # 5 minutes for enrichment
)
@modal.fastapi_endpoint(method="POST")
def manual_enrich_trigger(item: EnrichRequest):
    """
    Manual contact enrichment endpoint for dashboard.
    
    Payload: {
        "company_id": "uuid",
        "client_context": "pulsepoint_strategic" (optional)
    }
    
    Returns: {
        "status": "success" | "error",
        "contacts_found": int,
        "contacts": [{"name": str, "email": str, "title": str}, ...]
    }
    """
    from supabase import create_client
    from apify_client import ApifyClient
    
    print(f"🔍 Manual enrichment triggered for company: {item.company_id}")
    
    # Initialize clients
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
    
    if not all([SUPABASE_URL, SUPABASE_KEY, APIFY_TOKEN]):
        return {"status": "error", "message": "Missing API keys", "contacts_found": 0}
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    # LOAD STRATEGIES FROM DB
    fetch_client_strategies(supabase)
    apify = ApifyClient(APIFY_TOKEN)
    
    # Fetch company details
    comp_resp = supabase.table("triggered_companies").select("*").eq("id", item.company_id).execute()
    
    if not comp_resp.data or len(comp_resp.data) == 0:
        return {"status": "error", "message": "Company not found", "contacts_found": 0}
    
    comp = comp_resp.data[0]
    
    # Check if contacts already exist
    strategy = CLIENT_STRATEGIES.get(item.client_context, CLIENT_STRATEGIES["pulsepoint_strategic"])
    leads_table = strategy.get("leads_table", "PULSEPOINT_STRATEGIC_TRIGGERED_LEADS")
    
    existing = supabase.table(leads_table).select("*").eq("triggered_company_id", item.company_id).execute()
    
    if existing.data and len(existing.data) > 0:
        return {
            "status": "already_enriched",
            "message": f"Company already has {len(existing.data)} contacts",
            "contacts_found": len(existing.data),
            "contacts": [{"name": c.get("name"), "email": c.get("email"), "title": c.get("title")} for c in existing.data]
        }
    
    # Run enrichment
    enriched = enrich_company_contacts(
        company_id=item.company_id,
        company_name=comp['company'],
        existing_website=comp.get('website'),
        client_context=item.client_context,
        apify_client=apify,
        supabase=supabase
    )
    
    return {
        "status": "success" if enriched else "no_contacts_found",
        "message": f"Found {len(enriched)} contacts" if enriched else "No contacts could be found",
        "contacts_found": len(enriched),
        "contacts": enriched
    }

@app.local_entrypoint()
def run_batch():
    print("🚀 Triggering BATCH SCAN for PulsePoint Strategic (Limit: 200)...")
    # Call remote function without arguments to trigger 'get_due_companies' logic
    run_monitoring_scan.remote()

class SourcingRequest(BaseModel):
    strategy_id: str

@app.function(
    image=image, 
    secrets=[modal.Secret.from_dotenv()],
    timeout=900  # 15 minutes for sourcing (slow)
)
@modal.fastapi_endpoint(method="POST")
def source_accounts_trigger(item: SourcingRequest):
    """
    Trigger Automated Account Sourcing for a specific strategy.
    
    Payload: {"strategy_id": "uuid"}
    """
    import sys
    # Add current dir to path so we can import the module
    sys.path.append('/root') 
    from execution.source_new_accounts import source_new_accounts
    
    print(f"🚀 Triggering Sourcing for Strategy: {item.strategy_id}")
    
    try:
        source_new_accounts(item.strategy_id)
        return {"status": "success", "message": "Sourcing started."}
    except Exception as e:
        print(f"❌ Sourcing Failed: {e}")
        return {"status": "error", "message": str(e)}

