import re
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from core.models import ScamCheckResult
from services.tinyfish_client import TinyFishClient
from utils.helpers import classify_domain_trust, is_safe_url

logger = logging.getLogger("SchemeRadar.ScamChecker")

class ScamChecker:
    """Investigates suspicious scholarships, WhatsApp forwards, and dubious application portals.
    Adheres strictly to nuanced fraud assessment rules:
    - Distinguishes official portal 2FA from individual OTP sharing.
    - Treats fee requests as a strong warning indicator (not guaranteed fraud for private exams).
    - Blocks unsafe URLs (localhost, private network RFC1918 IPs, unsupported schemes).
    - Identifies domain impersonation and cross-references official .gov.in sources.
    """

    def __init__(self, tinyfish_client: TinyFishClient):
        self.tinyfish = tinyfish_client

    def check(self, input_text: str) -> ScamCheckResult:
        """Alias for investigate() for backward compatibility."""
        return self.investigate(input_text)

    def investigate(self, input_text: str) -> ScamCheckResult:
        """Run multi-step scam investigation using heuristics and TinyFish live corroboration."""
        red_flags: List[str] = []
        warning_indicators: List[str] = []
        legit_indicators: List[str] = []
        evidence: List[str] = []
        official_sources_found: List[str] = []
        recommendations: List[str] = []

        raw_lower = input_text.lower()

        # Step 1: Detect and validate extracted URLs
        urls = re.findall(r"https?://[^\s<>\"']+", input_text)
        safe_urls = []
        for u in urls:
            if not is_safe_url(u):
                red_flags.append(
                    f"Dangerous URL detected: '{u}'. Targets an unsafe scheme, localhost, or private RFC1918 IP address. Critical security hazard."
                )
            else:
                safe_urls.append(u)

        primary_url = safe_urls[0] if safe_urls else None

        # Step 2: Payment and Fee Demands (Warning Indicator)
        fee_triggers = [
            "registration fee", "processing fee", "application charge", "security deposit",
            "pay ₹", "pay rs", "transfer fee", "refundable deposit", "pay to activate", "fee of"
        ]
        has_fee_demand = False
        for trigger in fee_triggers:
            if trigger in raw_lower:
                has_fee_demand = True
                warning_indicators.append(
                    f"Registration / processing fee mentioned ('{trigger}'). Warning: Genuine Indian central and state government scholarships are 100% free of charge."
                )
                break

        # Step 3: Sensitive Credentials & OTP Distinction
        # Distinguish entering OTP into an official portal from sharing that OTP with an individual
        share_otp_match = re.search(
            r"\b(share|send|forward|tell|give|submit|whatsapp)\b[^\.\n]{0,35}\b(otp|password|pin|credential)\b",
            raw_lower,
        )
        share_dest_match = re.search(
            r"\b(otp|password|pin)\b[^\.\n]{0,35}\b(on whatsapp|to whatsapp|over phone|to caller|to agent|with individual|with anyone|on link)\b",
            raw_lower,
        )

        if share_otp_match or share_dest_match:
            red_flags.append(
                "Requests sharing confidential OTP / password with an individual or via chat. Critical phishing / credential theft red flag."
            )
        elif any(t in raw_lower for t in ["otp verification", "aadhaar otp", "enter otp on portal", "verify with otp", "2fa", "two-factor"]):
            legit_indicators.append(
                "Mentions standard portal OTP two-factor verification. Remember: Enter OTP ONLY on verified official websites, never share it with anyone."
            )

        # Financial credential requests (always critical red flag)
        fin_cred_triggers = ["atm pin", "cvv", "bank password", "net banking password", "upi pin"]
        for trigger in fin_cred_triggers:
            if trigger in raw_lower:
                red_flags.append(
                    f"Requests banking PIN / CVV / financial secret ('{trigger}'). Definite phishing indicator."
                )
                break

        # Step 4: Domain Trust and Lookalike Impersonation Check
        if primary_url:
            parsed = urlparse(primary_url)
            domain = parsed.netloc.lower()
            trust = classify_domain_trust(domain)

            if trust["is_official"]:
                legit_indicators.append(
                    f"URL domain '{domain}' is an authenticated official tier: {trust['tier']}."
                )
            else:
                # Impersonation checks e.g. "scholarship-gov-in.com" or "pm-scholarship-portal.xyz"
                impersonation_hints = ["gov-in", "scholarship-nic", "ssp-karnataka", ".xyz", ".top", ".buzz", "pm-scholarship", "free-scholarship"]
                if any(h in domain for h in impersonation_hints) and not (domain.endswith(".gov.in") or domain.endswith(".nic.in")):
                    red_flags.append(
                        f"Deceptive lookalike domain detected ('{domain}'). Imitates an official government portal using typosquatting/suspicious TLD."
                    )
                else:
                    evidence.append(f"Domain '{domain}' is an independent third-party website (not an official government portal).")

            if primary_url.startswith("http://"):
                warning_indicators.append("Insecure plain HTTP connection (lacks TLS/HTTPS encryption).")

        # Step 5: Fake urgency or viral message patterns
        urgency_triggers = ["forward to 10 friends", "forward to all groups", "last 2 hours left to claim", "100% guaranteed selection"]
        for trigger in urgency_triggers:
            if trigger in raw_lower:
                warning_indicators.append(f"High-pressure viral wording detected: '{trigger}'.")
                break

        # Step 6: TinyFish Live Web Corroboration
        search_phrase = self._extract_searchable_entity(input_text, primary_url)
        if search_phrase and self.tinyfish.is_configured:
            evidence.append(f"Investigating public government existence with TinyFish for: '{search_phrase}'")
            query = f"official portal {search_phrase} scholarship eligibility site:.gov.in OR site:.nic.in"
            search_res = self.tinyfish.search_schemes(query, limit=4)
            
            if search_res.get("success") and search_res.get("results"):
                for r in search_res["results"]:
                    r_url = r.get("url", "")
                    r_title = r.get("title", "")
                    if ".gov.in" in r_url or ".nic.in" in r_url or ".ac.in" in r_url:
                        official_sources_found.append(r_url)
                        legit_indicators.append(f"Corroborated by official government portal: {r_title} ({urlparse(r_url).netloc})")
            else:
                evidence.append("No authoritative government portals found corroborating this specific scholarship.")

        # Step 7: Formulate Nuanced Verdict
        all_warnings = red_flags + warning_indicators

        if len(red_flags) >= 1 or (has_fee_demand and len(warning_indicators) >= 2):
            verdict = "Suspicious"
            confidence = min(0.95, 0.70 + len(red_flags) * 0.1)
            evidence.append("Critical red flags identified indicating potential fraud, credential phishing, or deception.")
            recommendations.extend([
                "DO NOT pay any registration or processing fees. Genuine government schemes do not charge fees.",
                "NEVER share OTPs, passwords, or UPI/banking PINs with anyone over WhatsApp, phone, or third-party forms.",
                "Only apply through official portals (e.g. scholarships.gov.in or ssp.postmatric.karnataka.gov.in).",
                "Do not forward this message to classmates or student groups."
            ])
        elif len(official_sources_found) >= 1 and len(red_flags) == 0:
            verdict = "Likely legitimate"
            confidence = 0.85
            evidence.append(f"Found {len(official_sources_found)} authoritative government citations.")
            recommendations.extend([
                "Verify that your browser address bar points to the official domain before logging in.",
                "Official portal logins use your own mobile number and Aadhaar authentication.",
                "Keep required documentation ready (Income Certificate, Marksheets, Bonafide)."
            ])
        else:
            verdict = "Unable to verify"
            confidence = 0.50
            evidence.append("Missing independent official confirmation; no direct government listing was identified.")
            recommendations.extend([
                "Check with your college scholarship nodal officer before submitting personal documents.",
                "Search the National Scholarship Portal (scholarships.gov.in) directly.",
                "Exercise caution and never transfer funds or provide banking credentials."
            ])

        return ScamCheckResult(
            input_text=input_text[:500],
            verdict=verdict,
            confidence=round(confidence, 2),
            evidence=evidence,
            red_flags=all_warnings,
            legitimate_indicators=legit_indicators,
            official_sources_found=official_sources_found,
            recommendations=recommendations,
        )

    def _extract_searchable_entity(self, text: str, url: Optional[str]) -> str:
        """Extract key scholarship entity phrase from user input."""
        if url:
            parsed = urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if len(p) > 2]
            if path_parts:
                return f"{parsed.netloc} {path_parts[-1]}"
            return parsed.netloc

        lines = [line.strip() for line in text.split("\n") if len(line.strip()) > 5]
        if lines:
            return " ".join(lines[0].split()[:8])
        return "Government Scholarship"
