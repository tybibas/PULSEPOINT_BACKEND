import sys
sys.path.append('.')
from execution.monitor_companies_job import is_valid_article_url

def test_blocking():
    print("🛡️ Testing URL Validation Logic against 'Bad' Legacy Data...\n")
    
    bad_urls = [
        # The specific ZoomInfo link found in DB
        "https://www.zoominfo.com/c/captiv-creative/458382061",
        # Another directory site
        "https://clutch.co/profile/mauge",
        # Generic company page
        "https://mauge.com/about",
        # Valid looking but should pass
        "https://www.prnewswire.com/news-releases/example-news-301234.html"
    ]
    
    for url in bad_urls:
        company_name = "TestCompany"
        is_valid, reason = is_valid_article_url(url, company_name)
        
        status = "✅ PASSED (Valid)" if is_valid else f"⛔ BLOCKED ({reason})"
        print(f"URL: {url}\nResult: {status}\n")

if __name__ == "__main__":
    test_blocking()
