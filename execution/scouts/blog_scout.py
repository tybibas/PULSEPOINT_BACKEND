import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from newspaper import Article
import datetime
import re

def find_sitemaps(base_url):
    """Stage 1: Discover sitemaps via common paths and robots.txt."""
    print(f"      📡 [BlogScout] Searching for sitemaps: {base_url}")
    sitemaps = []
    
    # 1. Common paths
    paths = ["/sitemap.xml", "/post-sitemap.xml", "/sitemap_index.xml", "/blog/sitemap.xml"]
    for path in paths:
        target = urljoin(base_url, path)
        try:
            r = requests.head(target, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                sitemaps.append(target)
        except: continue
        
    # 2. robots.txt
    try:
        r = requests.get(urljoin(base_url, "/robots.txt"), timeout=5)
        if r.status_code == 200:
            matches = re.findall(r'^Sitemap:\s*(.+)$', r.text, re.IGNORECASE | re.MULTILINE)
            for m in matches:
                sitemaps.append(m.strip())
    except: pass
    
    return list(set(sitemaps))

def find_feeds(blog_url):
    """Stage 2: Discover RSS/Atom feeds."""
    print(f"      📡 [BlogScout] Searching for feeds: {blog_url}")
    feeds = []
    paths = ["/feed", "/rss", "/rss.xml", "/blog/feed", "/blog/rss"]
    for path in paths:
        target = urljoin(blog_url, path)
        try:
            r = requests.head(target, timeout=5, allow_redirects=True)
            if r.status_code == 200:
                feeds.append(target)
        except: continue
        
    # Link tags
    try:
        r = requests.get(blog_url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for link in soup.find_all('link', rel=['alternate', 'sitemap']):
            href = link.get('href')
            type_ = link.get('type', '').lower()
            if href and ('rss' in type_ or 'atom' in type_ or 'xml' in type_):
                feeds.append(urljoin(blog_url, href))
    except: pass
    
    return list(set(feeds))

def find_blog_url_via_apify(company_name, domain, apify_client, widen=False):
    """Stage 3: Multi-pattern Google Search with auto-widening."""
    
    # OPTIMIZATION: Check common paths first to save Apify calls
    if not widen:
        base = f"https://{domain}"
        common_paths = ["/blog", "/insights", "/news", "/articles", "/press"]
        print(f"      🕵️ [BlogScout] Checking common paths for {domain}...")
        for path in common_paths:
            try:
                target = urljoin(base, path)
                r = requests.head(target, timeout=3, allow_redirects=True)
                if r.status_code == 200:
                    print(f"      ✅ Found blog path: {target}")
                    return target
            except: continue

    print(f"      📡 [BlogScout] Searching via Google (Widen: {widen}): {company_name}")
    
    if not widen:
        # Strict pattern
        queries = [
            f'site:{domain} (blog OR insights OR news OR perspectives)',
            f'site:{domain} (category OR tag) (blog OR insights)'
        ]
    else:
        # Widened pattern (remove site: constraint or use more general terms)
        queries = [
            f'"{domain}" (blog OR insights OR news OR article OR category) -jobs -careers',
            f'related:{domain} blog'
        ]
    
    try:
        run_input = {
            "queries": "\n".join(queries),
            "maxPagesPerQuery": 1,
            "resultsPerPage": 5
        }
        run = apify_client.actor("apify/google-search-scraper").call(run_input=run_input)
        
        results = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            for res in item.get("organicResults", []):
                url = res.get("url", "").lower()
                if any(kw in url for kw in ['blog', 'insight', 'news', 'perspective', 'article', 'resource', 'category', 'tag']):
                    if not any(bad in url for bad in ['linkedin', 'facebook', 'twitter', 'instagram', 'youtube']):
                        results.append(res.get("url"))
        
        if not widen and len(results) < 3:
            print(f"      ⚠️ Insufficient results ({len(results)}). Widening search...")
            return find_blog_url_via_apify(company_name, domain, apify_client, widen=True)
            
        return results[0] if results else None
    except Exception as e:
        print(f"      [BlogScout] Search failed: {e}")
        return None

def scout_latest_blog_posts(company_name, company_website, apify_client):
    """
    Refined BlogScout:
    1. Sitemap/RSS Priority.
    2. Discovery Hubs (/blog, /testimonials) -> capture primary content.
    3. Multi-pattern search + widening.
    4. Early stop at 10 valid posts.
    """
    print(f"      🔍 [BlogScout] Scouting {company_name}...")
    
    domain = urlparse(company_website).netloc or company_website.split('/')[0]
    base_url = f"https://{domain}"
    
    # --- Step 1: Discover Blog/Hub URL ---
    blog_url = find_blog_url_via_apify(company_name, domain, apify_client)
    if not blog_url:
        blog_url = urljoin(base_url, "/blog")
        print(f"      ⚠️ No blog found, using fallback: {blog_url}")
    
    # --- Step 2: Extract Content from Hub URL (Primary) ---
    print(f"      📡 [BlogScout] Capturing Hub Content: {blog_url}")
    found_triggers = []
    
    try:
        hub_article = Article(blog_url)
        hub_article.download()
        hub_article.parse()
        if len(hub_article.text) > 500: # Significant content on page
             found_triggers.append({
                'url': blog_url,
                'title': hub_article.title or "Recent Insights",
                'text': hub_article.text,
                'publish_date': None, # Hubs usually don't have a single date
                'source': 'direct_hub_capture'
            })
    except: pass
    
    # --- Step 3: Discover specific post links ---
    article_links = []
    
    # Sitemap Discovery
    sitemaps = find_sitemaps(base_url)
    for sm in sitemaps:
        try:
            r = requests.get(sm, timeout=10)
            soup = BeautifulSoup(r.text, 'xml')
            for loc in soup.find_all('loc'):
                url = loc.text.strip()
                if domain in url and any(kw in url.lower() for kw in ['/blog/', '/insights/', '/post/', '/articles/']):
                    article_links.append(url)
            if len(article_links) >= 30: break
        except: continue
        
    # RSS Discovery
    if len(article_links) < 5:
        feeds = find_feeds(blog_url)
        for feed in feeds:
            try:
                r = requests.get(feed, timeout=10)
                soup = BeautifulSoup(r.text, 'xml')
                for item in soup.find_all(['item', 'entry']):
                    link = item.find(['link', 'id'])
                    url = link.text.strip() if link else None
                    if url and domain in url:
                        article_links.append(url)
                if len(article_links) >= 30: break
            except: continue
            
    # Restrained Crawl fallback
    if len(article_links) < 5:
        print(f"      📡 [BlogScout] Falling back to restrained crawl...")
        try:
            run_input = {
                "startUrls": [{"url": blog_url}],
                "maxDepth": 2,
                "maxPagesPerCrawl": 25,
                "excludePatterns": ["**/category/**", "**/tag/**", "**/page/**", "**?**"]
            }
            run = apify_client.actor("apify/website-content-crawler").call(run_input=run_input)
            for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                url = item.get("url")
                if url and domain in url and url not in article_links:
                    if not any(bad in url.lower() for bad in ['/page/', '/tag/', '/category/']):
                        article_links.append(url)
        except: pass
        
    # --- Step 4: Final Extraction ---
    print(f"      📄 [BlogScout] Found {len(article_links)} links. Filtering...")
    
    for url in list(set(article_links)):
        if len(found_triggers) >= 11: break # 10 posts + 1 hub
        
        try:
            art = Article(url)
            art.download()
            art.parse()
            
            pub_date = art.publish_date
            if pub_date:
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=datetime.timezone.utc)
                now = datetime.datetime.now(datetime.timezone.utc)
                if (now - pub_date).days <= 30: # 30 days window
                    found_triggers.append({
                        'url': url,
                        'title': art.title,
                        'text': art.text,
                        'publish_date': pub_date.isoformat(),
                        'source': 'direct_post'
                    })
            else:
                 # Orchestrator handles undated posts via AI
                 found_triggers.append({
                    'url': url,
                    'title': art.title,
                    'text': art.text,
                    'publish_date': None,
                    'source': 'direct_post'
                })
        except: continue
        
    return found_triggers

if __name__ == "__main__":
    pass
