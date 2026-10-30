import os
from pathlib import Path

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=ENV_PATH)
except ImportError:
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

# TinyFish Configuration
TINYFISH_API_KEY = os.getenv("TINYFISH_API_KEY", "").strip()

# Endpoints
TINYFISH_SEARCH_URL = "https://api.search.tinyfish.ai"
TINYFISH_FETCH_URL = "https://api.fetch.tinyfish.ai"
TINYFISH_AGENT_URL = "https://agent.tinyfish.ai/v1/automation/run"

# Request Config
REQUEST_TIMEOUT = 45  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential multiplier

# Discovery Limits
DEFAULT_SEARCH_RESULT_LIMIT = 5
MAX_PROCESS_URLS = 4  # Focused processing to remain within rate limits and optimize demo response time

# Supported Lists for Profiles
COURSES = [
    "B.Tech",
    "B.E.",
    "BCA",
    "B.Sc",
    "M.Tech",
    "MCA",
    "M.Sc",
    "Diploma",
    "MBBS",
    "B.Com",
    "BA",
    "Other"
]

ACADEMIC_YEARS = [
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
    "Final Year",
    "Postgraduate"
]

INDIAN_STATES = [
    "Karnataka",
    "Maharashtra",
    "Tamil Nadu",
    "Telangana",
    "Andhra Pradesh",
    "Uttar Pradesh",
    "Delhi",
    "Kerala",
    "Gujarat",
    "West Bengal",
    "Rajasthan",
    "Madhya Pradesh",
    "Bihar",
    "Punjab",
    "Haryana",
    "Odisha",
    "Assam",
    "Jharkhand",
    "Chhattisgarh",
    "Uttarakhand",
    "Himachal Pradesh",
    "Goa",
    "All India / Central"
]

CATEGORIES = [
    "General",
    "OBC",
    "SC",
    "ST",
    "EWS",
    "Minority",
    "PWD / Specially Abled",
    "Other"
]

INCOME_BANDS = [
    "Below ₹1 lakh",
    "₹1–2.5 lakh",
    "₹2.5–5 lakh",
    "₹5–8 lakh",
    "Above ₹8 lakh"
]

INTERESTS = [
    "Engineering",
    "Computer Science",
    "Artificial Intelligence",
    "Research",
    "Technology",
    "Entrepreneurship",
    "Innovation",
    "Women in STEM",
    "Merit-based scholarships",
    "Financial assistance"
]

# Source Authenticity Priorities
GOV_DOMAINS = [
    ".gov.in",
    ".nic.in",
    ".ac.in",
    ".edu.in",
    "scholarships.gov.in",
    "ssp.karnataka.gov.in",
    "karnataka.gov.in",
    "ugc.ac.in",
    "aicte-india.org",
    "dst.gov.in",
    "dbtindia.gov.in",
    "buddy4study.com"  # Independent scholarship portal
]
