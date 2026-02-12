import os
import sys
from apify_client import ApifyClient
import datetime

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from resilience import retry_with_backoff
except ImportError:
    from execution.resilience import retry_with_backoff

def scout_executive_social_activity(person_name, company_name, apify_client):
    """
    Searches for recent LinkedIn/Twitter activity for a specific decision maker.
    """
    print(f"      🔍 [SocialScout] Scouting social activity for {person_name} ({company_name})...")
    
    # Targeted queries to find POSTS/TWEETS specifically
    queries = [
        f'site:linkedin.com/posts "{person_name}" "{company_name}"',
        f'site:twitter.com "{person_name}" "{company_name}"'
    ]
    
    found_signals = []
    
    for query in queries:
        try:
            # Use Google Search Scraper to minimize risk
            run_input = {
                "queries": query,
                "maxPagesPerQuery": 1,
                "resultsPerPage": 5,
                "tbs": "qdr:m2" # Last 2 months (social activity can be slightly older but still relevant)
            }
            
            # Start the actor and wait for it to finish
            @retry_with_backoff(max_retries=1, initial_delay=3)
            def _search():
                return apify_client.actor("apify/google-search-scraper").call(run_input=run_input, timeout_secs=45)
            run = _search()
            
            # Fetch results from the dataset
            for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                organic_results = item.get("organicResults", [])
                
                for res in organic_results:
                    # Extract fields from result
                    title = res.get("title", "")
                    url = res.get("url", "")
                    snippet = res.get("description", "")
                    
                    if not url:
                        continue
                    
                    # IDENTITY VERIFICATION (Strict Phase 11)
                    lower_snippet = snippet.lower()
                    lower_title = title.lower()
                    lower_text = lower_title + " " + lower_snippet
                    
                    person_parts = person_name.lower().split()
                    last_name = person_parts[-1]
                    comp_name = company_name.lower()
                    
                    # 1. Subject Check: Last name must be present
                    if last_name not in lower_text:
                        continue # Skip result, likely irrelevant
                        
                    # 2. Context Check: Company name must be present OR specialized keywords
                    # If company name is very short (e.g. "Box"), this might be noisy, but better safe.
                    is_verified = False
                    if comp_name in lower_text:
                        is_verified = True
                    
                    # 3. Assign Status
                    status = "verified" if is_verified else "ambiguous"
                    
                    found_signals.append({
                        'url': url,
                        'title': title,
                        'text': snippet,
                        'person_name': person_name,
                        'source': 'social_scout',
                        'verification_status': status
                    })
                    
        except Exception as e:
            print(f"      ⚠️ [SocialScout] Error scouting social for {person_name}: {e}")
            continue
            
    return found_signals

if __name__ == "__main__":
    # Test (requires APIFY_API_KEY in env)
    from apify_client import ApifyClient
    from dotenv import load_dotenv
    load_dotenv()
    
    client = ApifyClient(os.environ.get("APIFY_API_KEY"))
    res = scout_executive_social_activity("Kyle York", "York IE", client)
    print(f"\nFinal Results: {len(res)} found")
