import os
import requests
import json
import sys

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

resp = requests.post(
    "https://api.fetch.tinyfish.ai",
    json={
        "urls": ["https://scholarships.gov.in/All-Scholarships"],
        "format": "markdown",
        "purpose": "Extract all active scholarship schemes, eligibility, and closing dates",
        "links": True
    },
    headers=headers,
    timeout=40
)

print(f"Fetch status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    results = data.get("results", [])
    if results:
        res = results[0]
        text = res.get("text", "")
        print(f"Text length: {len(text)}")
        print(f"Sample text:\n{text[:1500]}")
        links = res.get("links", [])
        print(f"\nLinks count: {len(links)}")
        for l in links[:10]:
            print(f"  {l.get('text')} -> {l.get('href')}")

