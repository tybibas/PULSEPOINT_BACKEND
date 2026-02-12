
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

url = "https://york.ie"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

try:
    print(f"Fetching {url}...")
    # use a session to handle cookies/redirects
    session = requests.Session()
    response = session.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    
    # Print the first 1000 chars to see if it's a block page
    print("Content Preview:")
    print(response.text[:1000])
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)
    print(f"Found {len(links)} links.")
    
    for link in links:
        text = " ".join(link.get_text().split()).lower()
        href = link['href']
        if 'blog' in text or 'blog' in href.lower():
            print(f"MATCH: {text} -> {href}")
            
except Exception as e:
    print(f"Error: {e}")
