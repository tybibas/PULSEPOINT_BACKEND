
from execution.monitor_companies_job import is_valid_article_url, extract_date_from_text

# Test ZoomInfo Block
url = "https://www.zoominfo.com/c/punch-media/98550139"
valid, reason = is_valid_article_url(url, "Greentarget")
print(f"ZoomInfo URL: {url}")
print(f"Result: {valid}, Reason: {reason}")

# Test Date Extraction (With Header Noise)
text = """
Home | News | Contact | Monday, February 9, 2026
------------------------------------------------
Greentarget rebrands to GT Sage
...
Published: 16 April 2025
...
"""
from datetime import datetime
date_obj, date_str = extract_date_from_text(text)
print(f"Extracted Date: {date_str}")
