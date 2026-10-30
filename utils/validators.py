import re
from typing import List, Tuple, Dict, Any
from urllib.parse import urlparse

def validate_profile(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate student profile input fields."""
    errors = []
    
    if not data.get("course"):
        errors.append("Please select your Course / Degree.")
    if not data.get("academic_year"):
        errors.append("Please select your current Academic Year.")
    if not data.get("state_of_domicile"):
        errors.append("Please specify your State of Domicile.")
    if not data.get("category"):
        errors.append("Please select your Category (e.g., General, OBC, SC, ST, EWS).")
    if not data.get("family_income_band"):
        errors.append("Please select your Annual Family Income band.")

    return len(errors) == 0, errors

def validate_url(url: str) -> bool:
    """Validate if a URL is well-formed and safe (http or https only)."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def sanitize_query(query: str) -> str:
    """Sanitize user search queries to prevent malformed API calls."""
    if not query:
        return ""
    # Strip dangerous characters and excessive whitespace
    cleaned = re.sub(r"[^\w\s\-\.,₹]", " ", query)
    return " ".join(cleaned.split())

def validate_scholarship_fields(data: Dict[str, Any]) -> List[str]:
    """Identify which critical scholarship fields could not be verified."""
    missing = []
    if not data.get("scholarship_amount"):
        missing.append("Scholarship Grant Amount")
    if not data.get("application_deadline"):
        missing.append("Application Deadline")
    if not data.get("application_url"):
        missing.append("Direct Application Portal Link")
    if not data.get("maximum_income"):
        missing.append("Explicit Income Ceiling")
    if not data.get("eligible_courses"):
        missing.append("Specific Course Criteria")
    return missing

