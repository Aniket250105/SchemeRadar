import logging
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import requests
from utils.helpers import classify_domain_trust
from config.settings import REQUEST_TIMEOUT

logger = logging.getLogger("SchemeRadar.Verification")

class SourceVerifier:
    """Verifies domain authenticity and checks live application portal connectivity."""

    @staticmethod
    def verify_source(source_url: str, application_url: Optional[str] = None) -> Dict[str, Any]:
        """Classify and assess the trustworthiness of the scholarship source and destination links."""
        source_trust = classify_domain_trust(source_url)
        app_trust = classify_domain_trust(application_url) if application_url else None

        # Check domain alignment
        source_netloc = urlparse(source_url).netloc.lower()
        app_netloc = urlparse(application_url).netloc.lower() if application_url else ""

        is_cross_domain = bool(app_netloc and app_netloc != source_netloc)
        
        # Determine safety notes
        notes = []
        if source_trust["is_official"]:
            notes.append("Discovered directly on an official Government or University digital domain.")
        else:
            notes.append("Discovered on a third-party educational portal; always corroborate before applying.")

        if app_trust and app_trust["is_official"]:
            notes.append(f"Application leads directly to official authority: {app_netloc}.")
        elif is_cross_domain and not app_trust.get("is_official", False):
            notes.append("Caution: External redirect detected. Ensure you do not enter credentials on third-party sites.")

        return {
            "source_domain": source_netloc,
            "source_tier": source_trust["tier"],
            "source_is_official": source_trust["is_official"],
            "source_trust_score": source_trust["trust_score"],
            "source_badge_color": source_trust["badge_color"],
            "app_domain": app_netloc,
            "app_tier": app_trust["tier"] if app_trust else "N/A",
            "app_is_official": app_trust["is_official"] if app_trust else False,
            "is_cross_domain": is_cross_domain,
            "verification_notes": notes,
        }

    @staticmethod
    def check_link_health(url: str) -> Dict[str, Any]:
        """Perform a quick HEAD/GET request to verify the application portal is live and responding."""
        if not url or not url.startswith("http"):
            return {"accessible": False, "status_code": None, "reason": "Invalid URL"}

        try:
            # We do a lightweight HEAD request with short timeout
            resp = requests.head(url, timeout=10, allow_redirects=True, headers={"User-Agent": "SchemeRadar-HealthChecker/1.0"})
            if resp.status_code < 400:
                return {"accessible": True, "status_code": resp.status_code, "reason": "Portal responsive"}
            else:
                return {"accessible": False, "status_code": resp.status_code, "reason": f"HTTP {resp.status_code}"}
        except Exception as e:
            logger.debug(f"Link health check failed for {url}: {e}")
            return {"accessible": False, "status_code": None, "reason": "Connection timeout or portal unreachable"}

