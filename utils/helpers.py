import re
import ipaddress
import textwrap
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, Dict, Any
from urllib.parse import urlparse

# Indian Standard Time (IST = UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def render_html(html_str: str):
    """Safely render HTML without Markdown converting indented lines into code blocks."""
    import streamlit as st
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
        clean_html = " ".join(clean_lines)
        st.markdown(clean_html, unsafe_allow_html=True)

def get_current_ist_time() -> datetime:
    """Return the current datetime in Asia/Kolkata timezone."""
    return datetime.now(IST)

def format_currency(val: Optional[Any]) -> str:
    """Format numeric or string amount into readable Indian Rupee format."""
    if not val:
        return "Amount not specified"
    if isinstance(val, (int, float)):
        return f"₹{val:,.0f}"
    s = str(val).strip()
    if not s.startswith("₹") and not s.lower().startswith("rs"):
        return f"₹{s}"
    return s

def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various Indian government date formats and attach IST timezone."""
    if not date_str:
        return None
    s = date_str.strip()
    
    # Clean common suffixes like 31st, 1st, 2nd, 3rd
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)
    
    patterns = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    
    for fmt in patterns:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.replace(tzinfo=IST)
        except ValueError:
            continue
            
    # Regex fallback for embedded dates e.g. "31-03-2026" or "2026-03-31"
    match = re.search(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", s)
    if match:
        try:
            return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)), tzinfo=IST)
        except ValueError:
            pass

    match = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
    if match:
        try:
            return datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)), tzinfo=IST)
        except ValueError:
            pass

    return None

def calculate_deadline_urgency(
    deadline_str: Optional[str],
    start_date_str: Optional[str] = None
) -> Tuple[str, Optional[int]]:
    """Determine urgency status and days remaining relative to Asia/Kolkata current date.
    
    Returns:
        (status: str, days_left: Optional[int])
        Statuses: "Closed", "Urgent", "Closing soon", "Deadline approaching", "Time available", "Upcoming", "Needs verification"
    """
    if not deadline_str:
        return "Needs verification", None

    now_ist = get_current_ist_time()
    today_ist = now_ist.date()

    # Check start date first for Upcoming
    if start_date_str:
        start_dt = parse_date_string(start_date_str)
        if start_dt and start_dt.date() > today_ist:
            days_until_open = (start_dt.date() - today_ist).days
            return "Upcoming", days_until_open

    dt = parse_date_string(deadline_str)
    if not dt:
        lower = deadline_str.lower()
        if "close" in lower or "expired" in lower:
            return "Closed", -1
        if "always open" in lower or "round the year" in lower:
            return "Time available", 999
        return "Needs verification", None

    days_left = (dt.date() - today_ist).days

    if days_left < 0:
        return "Closed", days_left
    elif days_left <= 7:
        return "Urgent", days_left
    elif days_left <= 14:
        return "Closing soon", days_left
    elif days_left <= 21:
        return "Deadline approaching", days_left
    else:
        return "Time available", days_left

def classify_domain_trust(url_or_domain: str) -> Dict[str, Any]:
    """Classify the authority level, official status, and trust tier of a web domain."""
    if not url_or_domain:
        return {
            "tier": "Unknown",
            "authority_level": "Third-Party Information Portal",
            "is_official": False,
            "badge_color": "gray",
            "trust_score": 30,
            "domain": "",
        }

    domain = url_or_domain.lower().strip()
    if domain.startswith("http://") or domain.startswith("https://"):
        parsed = urlparse(domain)
        domain = parsed.netloc.lower()

    # Strip port if present
    if ":" in domain:
        domain = domain.split(":")[0]

    # Central government portals
    if any(d in domain for d in ["scholarships.gov.in", "aicte-india.org", "ugc.ac.in", "dst.gov.in", "dbtindia.gov.in"]):
        return {
            "tier": "Official Central Government Portal",
            "authority_level": "Official Central Government",
            "is_official": True,
            "badge_color": "green",
            "trust_score": 98,
            "domain": domain,
        }

    # State government scholarship portals
    if "ssp.karnataka.gov.in" in domain or "karnataka.gov.in" in domain:
        return {
            "tier": "Official Karnataka State Portal",
            "authority_level": "Official State Government",
            "is_official": True,
            "badge_color": "green",
            "trust_score": 96,
            "domain": domain,
        }

    if domain.endswith(".gov.in") or domain.endswith(".nic.in"):
        return {
            "tier": "Official Government Portal",
            "authority_level": "Official Central Government" if "gov.in" in domain and not any(st in domain for st in ["karnataka", "maharashtra", "tn", "up"]) else "Official State Government",
            "is_official": True,
            "badge_color": "green",
            "trust_score": 95,
            "domain": domain,
        }

    # Universities and Accredited Institutions
    if domain.endswith(".ac.in") or domain.endswith(".edu.in") or ".ac." in domain or ".edu" in domain:
        return {
            "tier": "Official University / Educational Portal",
            "authority_level": "Official University / Educational",
            "is_official": True,
            "badge_color": "blue",
            "trust_score": 88,
            "domain": domain,
        }

    # Third-party aggregators (Never label as official!)
    if any(d in domain for d in ["buddy4study.com", "vidyasaarathi.co.in", "shiksha.com", "collegedunia.com"]):
        return {
            "tier": "Recognized Third-Party Scholarship Platform",
            "authority_level": "Third-Party Information Portal",
            "is_official": False,
            "badge_color": "teal",
            "trust_score": 65,
            "domain": domain,
        }

    return {
        "tier": "Third-Party Information Portal (Unverified)",
        "authority_level": "Third-Party Information Portal",
        "is_official": False,
        "badge_color": "orange",
        "trust_score": 40,
        "domain": domain,
    }

def classify_page_type(url: str, title: str = "", text: str = "") -> str:
    """Determine whether a web page is a Directory, Portal Homepage, or Scheme Announcement."""
    u_lower = url.lower()
    t_lower = (title + " " + text[:500]).lower()

    if any(d in u_lower for d in ["/all-scholarships", "/scholarship-schemes", "/schemes", "/directory", "/list-of-schemes"]):
        return "Scholarship Directory"

    if any(h in u_lower for h in ["/homepage", "/home", "/login", "/default.aspx"]) or u_lower.rstrip("/").count("/") <= 2:
        return "Portal Homepage"

    if any(kw in t_lower for kw in ["all schemes", "schemes on nsp", "directory of scholarships", "list of schemes"]):
        return "Scholarship Directory"

    return "Scheme Announcement"

def is_safe_url(url: str) -> bool:
    """Validate that a URL is well-formed, uses http/https, and does not target localhost or private RFC1918 IPs."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block localhost and loopback names
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
            return False

        # Block private IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_reserved or ip.is_link_local:
                return False
        except ValueError:
            # It is a domain name, not a raw IP
            pass

        return True
    except Exception:
        return False

def extract_income_ceiling(text: str) -> Optional[float]:
    """Parse text like 'up to Rs. 2.5 Lakhs' or 'income not exceeding 8,00,000' into a float."""
    if not text:
        return None
        
    t = text.lower()
    
    # Check for lakh patterns
    lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs|lac|lacs)", t)
    if lakh_match:
        try:
            return float(lakh_match.group(1)) * 100000.0
        except ValueError:
            pass

    # Check for raw numbers e.g. 2,50,000 or 800000
    num_match = re.search(r"(?:rs\.?|inr|₹)?\s*(\d{1,2}(?:,\d{2})*(?:,\d{3})|\d{5,8})", t)
    if num_match:
        try:
            num_str = num_match.group(1).replace(",", "")
            val = float(num_str)
            if 30000 <= val <= 2500000:
                return val
        except ValueError:
            pass

    return None
