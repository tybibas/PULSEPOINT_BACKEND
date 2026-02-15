
import os
import requests
import json

class EnrichmentClient:
    """
    Unified client for Multi-Source Enrichment Waterfall.
    Tiers:
    1. Anymailfinder (Primary - existing)
    2. Hunter.io (Fallback)
    3. Apollo.io (Deep fallback)
    """
    def __init__(self):
        self.amf_key = os.environ.get("ANYMAILFINDER_API_KEY")
        self.hunter_key = os.environ.get("HUNTER_API_KEY")
        self.apollo_key = os.environ.get("APOLLO_API_KEY")
        
        self.session = requests.Session()

    def find_email(self, full_name: str, domain: str, company_name: str = None) -> tuple[str | None, str | None]:
        """
        Attempts to find an email using the waterfall strategy.
        Returns: (email, source_provider)
        """
        if not full_name or not domain:
            return None, None

        # --- Tier 1: Anymailfinder ---
        if self.amf_key:
            email = self._try_anymailfinder(full_name, domain)
            if email: return email, "anymailfinder"
        
        # --- Tier 2: Hunter.io ---
        if self.hunter_key:
            email = self._try_hunter(full_name, domain)
            if email: return email, "hunter"
            
        # --- Tier 3: Apollo.io ---
        if self.apollo_key:
            email = self._try_apollo(full_name, domain, company_name)
            if email: return email, "apollo"
            
        return None, None

    def _try_anymailfinder(self, name, domain):
        try:
            resp = self.session.post(
                "https://api.anymailfinder.com/v5.0/search/person.json",
                headers={"Authorization": self.amf_key},
                json={"full_name": name, "domain": domain},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", {}).get("email")
        except Exception as e:
            print(f"      ⚠️ Anymailfinder error: {e}")
        return None

    def _try_hunter(self, name, domain):
        try:
            # Hunter splits name
            parts = name.split()
            first = parts[0]
            last = " ".join(parts[1:]) if len(parts) > 1 else ""
            
            url = f"https://api.hunter.io/v2/email-finder?domain={domain}&first_name={first}&last_name={last}&api_key={self.hunter_key}"
            resp = self.session.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                # Check confidence? Hunter returns 'score'. Maybe filter < 50?
                # For now, if they return it, we take it.
                return data.get("data", {}).get("email")
        except Exception as e:
            print(f"      ⚠️ Hunter error: {e}")
        return None

    def _try_apollo(self, name, domain, company_name):
        try:
            parts = name.split()
            first = parts[0]
            last = " ".join(parts[1:]) if len(parts) > 1 else ""
            
            payload = {
                "api_key": self.apollo_key,
                "first_name": first,
                "last_name": last,
                "domain": domain
            }
            if company_name:
                payload["organization_name"] = company_name

            resp = self.session.post(
                "https://api.apollo.io/v1/people/match",
                headers={"Content-Type": "application/json", "Cache-Control": "no-cache"},
                json=payload,
                timeout=10
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("person", {}).get("email")
        except Exception as e:
            print(f"      ⚠️ Apollo error: {e}")
        return None
