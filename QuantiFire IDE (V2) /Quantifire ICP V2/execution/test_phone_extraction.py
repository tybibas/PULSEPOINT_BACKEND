
import sys
import os

# Add root to python path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.enrich_lead import find_contact_via_apollo

print("Testing find_contact_via_apollo with name...")
try:
    res = find_contact_via_apollo("google.com", "software engineer", name="Sundar Pichai")
    print("Result:", res)
except Exception as e:
    print(f"FAILED: {e}")
