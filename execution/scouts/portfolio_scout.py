import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from apify_client import ApifyClient
import re
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from resilience import retry_with_backoff
except ImportError:
    from execution.resilience import retry_with_backoff

def find_portfolio_url(company_name, domain, apify_client):
    """
    Uses Google Search to find the Portfolio/Work URL.
    """
    print(f"      📡 [PortfolioScout] Searching for portfolio URL via Apify: {company_name}")
    query = f'site:{domain} ("our work" OR "case studies" OR "clients" OR "portfolio")'
    
    try:
        run_input = {
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": 3
        }
        @retry_with_backoff(max_retries=1, initial_delay=3)
        def _search():
            return apify_client.actor("apify/google-search-scraper").call(run_input=run_input, timeout_secs=45)
        run = _search()
        
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            for res in item.get("organicResults", []):
                url = res.get("url", "").lower()
                # Heuristic: Check if it looks like a portfolio page
                if any(kw in url for kw in ['work', 'clients', 'case-studies', 'portfolio', 'projects']):
                    return res.get("url")
        return None
    except Exception as e:
        print(f"      ⚠️ [PortfolioScout] Apify discovery failed: {e}")
        return None

def scout_portfolio(company_name, company_website, apify_client):
    """
    Crawl the company's portfolio section and extract Client Names + Outcomes.
    """
    print(f"      🔍 [PortfolioScout] Scouting {company_name} ({company_website})...")
    
    domain = company_website.replace('https://', '').replace('http://', '').replace('www.', '').split('/')[0]
    
    portfolio_url = find_portfolio_url(company_name, domain, apify_client)
    
    if not portfolio_url:
        # Fallback guesses
        for path in ["/work", "/our-work", "/case-studies", "/clients"]:
             # Try simple construction logic if search fails
             # Note: real crawler would verify 200 OK, but Apify handles 404s gracefully
             portfolio_url = f"https://{domain}{path}"
             break # Just try the first logical one if search failed
             
    print(f"      📡 [PortfolioScout] Targeting portfolio page: {portfolio_url}")
    
    try:
        # Use Apify to scrape the portfolio page
        run_input = {
            "startUrls": [{"url": portfolio_url}],
            "maxDepth": 1, # Go one level deep to get details? Or just scrape index? 
                           # Cost tradeoff: 1 level deep = many requests. 
                           # V1: Just scrape the index page for "Client Name" cards.
            "maxPagesPerCrawl": 1 
        }
        @retry_with_backoff(max_retries=1, initial_delay=3)
        def _crawl():
            return apify_client.actor("apify/website-content-crawler").call(run_input=run_input, timeout_secs=45)
        run = _crawl()
        
        items = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        if not items:
            return []
            
        page_text = items[0].get("text", "")
        page_html = items[0].get("html", "")
        soup = BeautifulSoup(page_html, 'html.parser')
        
        found_triggers = []
        
        # Strategy: Look for "Client: X" or headings that look like brands
        # This is hard to do generically. 
        # Better approach for V1: 
        # Extract all H2/H3s and assume they are project titles/clients if short.
        
        headers = soup.find_all(['h2', 'h3', 'h4'])
        candidates = []
        for h in headers:
            text = h.get_text(strip=True)
            if 3 < len(text) < 40: # Client names are usually short
                candidates.append(text)
                
        # Filter candidates using named entity recognition (LLM) or just return top results for orchestrator to validate?
        # The orchestrator uses `process_company_scan`. We can return raw data and let the AI Prompt decide if it's a client.
        
        # We will package the whole Text content of the portfolio page
        # and let the Main AI (GPT-4o) extract the clients.
        # This is cleaner than trying to regex "Nike" out of HTML.
        
        found_triggers.append({
            'url': portfolio_url,
            'title': f"Portfolio Page: {portfolio_url}",
            'text': page_text[:8000], # Truncate to fit context
            'source': 'portfolio_scout',
            'is_portfolio': True
        })
        
        return found_triggers

    except Exception as e:
        print(f"      ⚠️ [PortfolioScout] Error scouting portfolio: {e}")
        return []
