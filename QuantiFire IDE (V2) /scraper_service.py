import os
import time
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")

class ScraperService:
    def __init__(self):
        if not APIFY_TOKEN:
            self.client = None
            print("⚠️ WARNING: APIFY_API_TOKEN not found. Scraping will fail.")
        else:
            self.client = ApifyClient(APIFY_TOKEN)

    def find_transcript_url(self, ticker, quarter, year):
        """
        Uses Apify Google Search Scraper to find the transcript URL.
        """
        if not self.client:
            return None

        # Primary cleaning: standard transcript search
        query = f"{ticker} earnings call transcript {quarter} {year} site:seekingalpha.com OR site:motleyfool.com"
        print(f"I: Searching for transcript: {query}")

        # Actor: apify/google-search-scraper
        run_input = {
            "queries": query,
            "maxPagesPerQuery": 1,
            "maxPagesPerQuery": 1,
            "resultsPerPage": 3,
            "countryCode": "us",
        }

        try:
            run = self.client.actor("apify/google-search-scraper").call(run_input=run_input)
            
            # Fetch results
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            for item in dataset_items:
                if "organicResults" in item:
                    for result in item["organicResults"]:
                        url = result.get("url", "")
                        title = result.get("title", "")
                        print(f"I: Found candidate: {title} - {url}")
                        # Basic validity check
                        if "transcript" in title.lower() or "earnings" in title.lower():
                            return url
            
            print("E: No suitable transcript URL found.")
            return None
            
        except Exception as e:
            print(f"E: Google Search Scraper failed: {e}")
            return None

    def scrape_content(self, url):
        """
        Uses Apify Website Content Crawler (Cheerio) to get text.
        """
        if not self.client or not url:
            return None

        print(f"I: Scraping content from: {url}")

        # Actor: apify/cheerio-scraper (lighter/cheaper than full browser)
        run_input = {
            "startUrls": [{"url": url}],
            "maxRequestsPerCrawl": 1,
            "pageFunction": """
                async function pageFunction(context) {
                    const { $ } = context;
                    // Extract main text content, stripping ads/nav
                    // Heuristics for SeekingAlpha/MotleyFool
                    let text = $('article').text() || $('main').text() || $('body').text();
                    return {
                        url: context.request.url,
                        title: $('title').text(),
                        content: text.trim().replace(/\\s+/g, ' ')
                    };
                }
            """
        }

        try:
            run = self.client.actor("apify/cheerio-scraper").call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            if dataset_items:
                return dataset_items[0].get("content", "")
            
            print("E: Content scrape returned no data.")
            return None

        except Exception as e:
            print(f"E: Content Scraper failed: {e}")
            return None

    def fetch_street_friction(self, ticker):
        """
        Searches for "Street Conflict" (analyst skepticism, risk notes) and returns 
        the search snippets as a context block.
        """
        if not self.client:
            return ""

        query = f"{ticker} analyst skeptical OR {ticker} dividend sustainability OR {ticker} governance risk OR {ticker} downgrade site:bloomberg.com OR site:reuters.com OR site:ft.com OR site:seekingalpha.com"
        print(f"I: Searching for Street Friction: {query}")

        run_input = {
            "queries": query,
            "maxPagesPerQuery": 1,
            "resultsPerPage": 5, # Get top 5 friction points
            "countryCode": "us",
        }

        try:
            run = self.client.actor("apify/google-search-scraper").call(run_input=run_input)
            dataset_items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            friction_text = "STREET FRICTION CONTEXT:\n"
            
            for item in dataset_items:
                if "organicResults" in item:
                    for result in item["organicResults"]:
                        title = result.get("title", "")
                        desc = result.get("description", "")
                        friction_text += f"- {title}: {desc}\n"
            
            return friction_text

        except Exception as e:
            print(f"E: Friction Search failed: {e}")
            return ""

    def parse_qa_section(self, content):
        """
        Splits the transcript into 'Prepared Remarks' and 'Q&A' sections
        using common heuristic markers.
        Returns: { "prepared": str, "qa": str }
        """
        if not content:
            return {"prepared": "", "qa": ""}

        # Common markers for Q&A start
        markers = [
            "Question-and-Answer Session",
            "Question and Answer Session",
            "open the floor for questions",
            "begin the Q&A",
            "Operator, please open the line",
            "Questions and Answers"
        ]
        
        split_index = -1
        for marker in markers:
            idx = content.find(marker)
            if idx != -1:
                split_index = idx
                break
        
        if split_index != -1:
            return {
                "prepared": content[:split_index].strip(),
                "qa": content[split_index:].strip()
            }
        
        # Fallback: specific to some Apify outputs or if no marker found
        # We might return entire content as prepared if we can't safely split
        # Or look for the first "Operator" after the first 20% of text
        return {
            "prepared": content,
            "qa": "" # Could not reliably split
        }

    def get_competitor_metrics(self, ticker):
        """
        Simulator for competitor scraping (Phase 2 optimization).
        For now, returns plausible dummy data to ensure report generation works 
        while focusing compute units on the Target company.
        """
        # In a full prod version, this would also scrape Google Finance / Yahoo Finance via Apify
        if ticker == "BP":
            return [
                {"name": "SHELL PLC", "score": 7.8},
                {"name": "TOTALENERGIES", "score": 6.5}
            ]
        
        # Default fallback
        return [
            {"name": "SECTOR PEER 1", "score": 7.2},
            {"name": "SECTOR PEER 2", "score": 6.5}
        ]

# Global Instance
scraper = ScraperService()
