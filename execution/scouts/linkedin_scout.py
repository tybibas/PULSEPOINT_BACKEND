"""
LinkedIn Activity Scout — Direct LinkedIn post scraping via Apify.

Fetches recent posts from company pages and/or founder profiles using
Apify's LinkedIn Posts Scraper (no cookies needed). Returns standardized
scout results for the trigger analysis pipeline.

Cost: ~$0.002 per company (10 posts @ $2/1k)
"""

import os
import sys
import time
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from resilience import retry_with_backoff
except ImportError:
    from execution.resilience import retry_with_backoff


# ─── Configuration ───
MAX_COMPANY_POSTS = 10      # Max posts to fetch from company page
MAX_PERSON_POSTS = 5        # Max posts per executive profile
MAX_PEOPLE = 2              # Max executives to scout
POST_AGE_DAYS = 14          # Only consider posts from last 14 days
APIFY_LINKEDIN_ACTOR = "harvest_api/linkedin-posts-scraper"  # No-cookies actor


def _discover_linkedin_company_url(company_name: str, apify_client) -> str:
    """
    Find a company's LinkedIn page URL via Google Search.
    Returns the URL or None if not found.
    """
    query = f'site:linkedin.com/company/ "{company_name}"'
    
    try:
        @retry_with_backoff(max_retries=1, initial_delay=3)
        def _search():
            return apify_client.actor("apify/google-search-scraper").call(
                run_input={
                    "queries": query,
                    "maxPagesPerQuery": 1,
                    "resultsPerPage": 5,
                    "languageCode": "",
                    "mobileResults": False,
                    "saveHtml": False,
                    "saveHtmlToKeyValueStore": False,
                    "includeIcons": False,
                },
                timeout_secs=45
            )
        run = _search()
        
        if not run:
            return None
            
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            organic = item.get("organicResults", [])
            for res in organic:
                url = res.get("url", "")
                # Validate: must be a company page, not a person profile or post
                if "linkedin.com/company/" in url and "/in/" not in url and "/posts/" not in url:
                    # Clean the URL to the base company page
                    # e.g. "https://www.linkedin.com/company/cuttocreate/about" → "https://www.linkedin.com/company/cuttocreate"
                    parts = url.split("/company/")
                    if len(parts) == 2:
                        slug = parts[1].strip("/").split("/")[0]
                        clean_url = f"https://www.linkedin.com/company/{slug}"
                        print(f"      🔗 [LinkedInScout] Found company page: {clean_url}")
                        return clean_url
                        
    except Exception as e:
        print(f"      ⚠️ [LinkedInScout] Company URL discovery failed: {e}")
    
    return None


def _extract_username(url: str) -> str:
    """Extract username from a LinkedIn profile URL."""
    if not url: return ""
    # https://www.linkedin.com/in/satyanadella -> satyanadella
    # https://www.linkedin.com/in/satyanadella/ -> satyanadella
    parts = url.strip("/").split("/in/")
    if len(parts) == 2:
        return parts[1].split("/")[0]
    return ""

def _scrape_company_posts(company_url: str, apify_client, max_posts: int = 10) -> list:
    """
    Scrape posts from a LinkedIn Company Page using apimaestro/linkedin-company-posts.
    """
    if not company_url:
        return []
    
    print(f"      📡 [LinkedInScout] Scraping Company: {company_url}...")
    try:
        @retry_with_backoff(max_retries=1, initial_delay=5)
        def _call_company_scraper():
            return apify_client.actor("apimaestro/linkedin-company-posts").call(
                run_input={
                    "companyUrl": company_url,
                    "limit": max_posts,
                    "model": "gpt-4o-mini" # Optional optimization
                },
                timeout_secs=120
            )
        
        run = _call_company_scraper()
        if not run:
            print(f"      ⚠️ [LinkedInScout] Company scraper returned no run")
            return []
        
        posts = []
        dataset_items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        
        for item in dataset_items:
            # Handle wrapping if any (usually direct items)
            # Standardize fields
            text = item.get("text", "") or item.get("postText", "") or item.get("description", "")
            if not text: continue
            
            posts.append({
                "text": text,
                "posted_at": item.get("postedAt", "") or item.get("date", ""),
                "reactions_count": item.get("totalReactions", 0) or item.get("likesCount", 0),
                "comments_count": item.get("commentsCount", 0),
                "reposts_count": item.get("repostsCount", 0),
                "post_url": item.get("postUrl", "") or item.get("url", ""),
                "author_name": item.get("companyName", "") or item.get("author", {}).get("name", ""),
                "author_title": "Company Page",
                "images": [],
                "is_company_post": True
            })
            
        return posts
        
    except Exception as e:
        print(f"      ⚠️ [LinkedInScout] Company scraper error: {e}")
        return []


def _scrape_profile_posts(profile_urls: list, apify_client, max_posts: int = 5) -> list:
    """
    Scrape posts from LinkedIn Profiles using apimaestro/linkedin-profile-posts.
    """
    if not profile_urls:
        return []
    
    all_posts = []
    
    for url in profile_urls:
        username = _extract_username(url)
        if not username:
            print(f"      ⚠️ [LinkedInScout] Could not extract username from {url}")
            continue
            
        print(f"      📡 [LinkedInScout] Scraping Profile: {username} ({url})...")
        try:
            @retry_with_backoff(max_retries=1, initial_delay=5)
            def _call_profile_scraper():
                return apify_client.actor("apimaestro/linkedin-profile-posts").call(
                    run_input={
                        "username": username,
                        "resultsCount": max_posts,
                    },
                    timeout_secs=90
                )
            
            run = _call_profile_scraper()
            if not run:
                print(f"      ⚠️ [LinkedInScout] Profile scraper returned no run for {username}")
                continue
            
            dataset_items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
            
            # Handle potential 'data.posts' wrapping
            raw_posts = []
            if dataset_items and "data" in dataset_items[0] and "posts" in dataset_items[0]["data"]:
                 # Single item with all posts
                 raw_posts = dataset_items[0]["data"]["posts"]
            else:
                 # List of post items
                 raw_posts = dataset_items

            for post in raw_posts:
                text = post.get("text", "") or post.get("postText", "") or ""
                
                # Date normalizer
                posted_at = post.get("posted_at", "")
                if isinstance(posted_at, dict):
                    posted_at = posted_at.get("date", "") or posted_at.get("relative", "")

                stats = post.get("stats", {}) or {}
                reactions = stats.get("total_reactions") or post.get("reactionsCount") or post.get("numLikes") or 0
                comments = stats.get("comments") or post.get("commentsCount") or post.get("numComments") or 0
                reposts = stats.get("reposts") or post.get("repostsCount") or 0
                
                author_data = post.get("author", {}) or {}
                if isinstance(author_data, dict):
                    author_name = f"{author_data.get('first_name', '')} {author_data.get('last_name', '')}".strip() or author_data.get("name", "")
                    author_title = author_data.get("headline", "")
                else:
                    author_name = str(author_data)
                    author_title = ""

                all_posts.append({
                    "text": text,
                    "posted_at": posted_at,
                    "reactions_count": reactions,
                    "comments_count": comments,
                    "reposts_count": reposts,
                    "post_url": post.get("postUrl", "") or post.get("url", ""),
                    "author_name": author_name,
                    "author_title": author_title,
                    "images": [],
                    "is_company_post": False
                })
                    
        except Exception as e:
            print(f"      ⚠️ [LinkedInScout] Profile scraper error for {username}: {e}")
            continue

    return all_posts


def _parse_post_date(date_str: str) -> datetime:
    """
    Parse various LinkedIn date formats into a datetime object.
    Handles ISO format, relative time ("2h ago", "3d ago"), and common formats.
    """
    if not date_str:
        return None
    
    date_str = str(date_str).strip()
    
    # Try ISO format first
    for fmt in ["%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try relative format: "2h", "3d", "1w", "2mo"
    now = datetime.utcnow()
    lower = date_str.lower().strip()
    
    if "ago" in lower:
        lower = lower.replace("ago", "").strip()
    
    try:
        if lower.endswith("h") or lower.endswith("hr"):
            hours = int(''.join(c for c in lower if c.isdigit()))
            return now - timedelta(hours=hours)
        elif lower.endswith("d"):
            days = int(''.join(c for c in lower if c.isdigit()))
            return now - timedelta(days=days)
        elif lower.endswith("w"):
            weeks = int(''.join(c for c in lower if c.isdigit()))
            return now - timedelta(weeks=weeks)
        elif lower.endswith("mo"):
            months = int(''.join(c for c in lower if c.isdigit()))
            return now - timedelta(days=months * 30)
    except (ValueError, IndexError):
        pass
    
    return None


def scout_linkedin_activity(company_name: str, linkedin_company_url: str, 
                             lead_linkedin_urls: list, apify_client, 
                             supabase=None, company_id: str = None) -> list:
    """
    Main entry point: scout LinkedIn activity for a company.
    
    Args:
        company_name: Name of the company
        linkedin_company_url: LinkedIn company page URL (or None to auto-discover)
        lead_linkedin_urls: List of {"name": ..., "linkedin": ...} for contacts
        apify_client: Apify client instance
        supabase: Optional Supabase client (for caching discovered URL)
        company_id: Optional company ID (for caching discovered URL)
    
    Returns:
        List of scout results in standardized format for the trigger pipeline.
    """
    print(f"      🔍 [LinkedInScout] Scouting LinkedIn activity for {company_name}...")
    
    all_activities = []
    
    # 1. Company page
    if not linkedin_company_url:
        # Auto-discover the company's LinkedIn page
        linkedin_company_url = _discover_linkedin_company_url(company_name, apify_client)
        
        # Cache the discovered URL for future scans
        if linkedin_company_url and supabase and company_id:
            try:
                # Store in score_factors JSON (no schema change needed)
                existing = supabase.table("triggered_companies").select("score_factors").eq("id", company_id).execute()
                factors = existing.data[0].get("score_factors", {}) if existing.data else {}
                if not isinstance(factors, dict):
                    factors = {}
                factors["linkedin_company_url"] = linkedin_company_url
                supabase.table("triggered_companies").update({"score_factors": factors}).eq("id", company_id).execute()
                print(f"      💾 [LinkedInScout] Cached LinkedIn URL in score_factors")
            except Exception as e:
                print(f"      ⚠️ [LinkedInScout] Failed to cache URL: {e}")
    
    # 2. Scrape Company Page (if available)
    if linkedin_company_url:
        company_posts = _scrape_company_posts(linkedin_company_url, apify_client, max_posts=MAX_COMPANY_POSTS)
        all_activities.extend(company_posts)
    
    # 3. Scrape Key Executive Profiles (max 2)
    if lead_linkedin_urls:
         # Extract just the URLs from the lead dicts/strings
        profile_urls = []
        for lead in lead_linkedin_urls:
            if isinstance(lead, dict) and lead.get("linkedin"):
                profile_urls.append(lead["linkedin"])
            elif isinstance(lead, str):
                profile_urls.append(lead)
        
        # Limit to M axes
        profile_urls = profile_urls[:MAX_PEOPLE]
        
        if profile_urls:
             profile_posts = _scrape_profile_posts(profile_urls, apify_client, max_posts=MAX_PERSON_POSTS)
             all_activities.extend(profile_posts)
    
    if not all_activities:
        print(f"      ℹ️ [LinkedInScout] No LinkedIn activity found for {company_name}")
        return []
    
    print(f"      📊 [LinkedInScout] Found {len(all_activities)} raw posts")

    # 4. Filter by date (last 14 days)
    cutoff = datetime.utcnow() - timedelta(days=POST_AGE_DAYS)
    recent_posts = []
    undated_posts = []
    
    for post in all_activities:
        post_date = _parse_post_date(post.get("posted_at", ""))
        if post_date and post_date >= cutoff:
            post["parsed_date"] = post_date
            recent_posts.append(post)
        elif not post_date:
            # Include undated posts (they might be recent — let GPT decide)
            undated_posts.append(post)
    
    # Include undated posts only if we have very few dated ones
    if len(recent_posts) < 3 and undated_posts:
        recent_posts.extend(undated_posts[:3])
    
    print(f"      👉 Keeping {len(recent_posts)} posts for analysis")
    
    # 5. Convert to standardized scout results
    found_signals = []
    for post in recent_posts:
        # Build a meaningful title from the post text
        text = post.get("text", "").strip()
        title = text[:80].replace("\n", " ").strip()
        if len(text) > 80:
            title += "..."
            
        author = post.get("author_name", "Unknown")
        post_type = "Company Post" if post.get("is_company_post") else "Executive Post"
        
        # Enrich description with stats
        engagement_str = f"👍 {post.get('reactions_count', 0)}  💬 {post.get('comments_count', 0)}"
        
        found_signals.append({
            "url": post.get("post_url", ""),
            "title": f"[{post_type}] {author}: {title}",
            "text": text,
            "description": f"{text[:300]}...\n\n(Engagement: {engagement_str})",
            "published_at": post.get("posted_at", ""),
            "source": "linkedin_scout",
            "is_scouted_social": True,
            "person_name": author,
            "verification_status": "verified",  # Direct scrape = verified identity
            "engagement": {
                "reactions": post.get("reactions_count", 0),
                "comments": post.get("comments_count", 0),
                "reposts": post.get("reposts_count", 0),
            }
        })
    
    print(f"      ✅ [LinkedInScout] Returning {len(found_signals)} LinkedIn signals for analysis")
    return found_signals


# ─── Standalone Test ───
if __name__ == "__main__":
    from apify_client import ApifyClient
    from dotenv import load_dotenv
    load_dotenv()
    
    client = ApifyClient(os.environ.get("APIFY_API_KEY"))
    
    print("🔬 TEST 1: Company Page (Microsoft)")
    # See if the actor supports company pages or defaults to Satya Nadella
    results_company = scout_linkedin_activity(
        company_name="Microsoft",
        linkedin_company_url="https://www.linkedin.com/company/microsoft", 
        lead_linkedin_urls=[],
        apify_client=client
    )
    print(f"Signals found: {len(results_company)}")
    if results_company:
        print(f"Sample: {results_company[0]['title']}")
        print(f"Author: {results_company[0]['person_name']}")

    print("\n🔬 TEST 2: Executive Profile (Reid Hoffman)")
    # See if the actor works for people (Reid Hoffman is usually public)
    results_person = scout_linkedin_activity(
        company_name="LinkedIn",
        linkedin_company_url=None,
        lead_linkedin_urls=[{"name": "Reid Hoffman", "linkedin": "https://www.linkedin.com/in/reidhoffman"}],
        apify_client=client
    )
    print(f"Signals found: {len(results_person)}")
    if results_person:
        print(f"Sample: {results_person[0]['title']}")
        print(f"Author: {results_person[0]['person_name']}")
