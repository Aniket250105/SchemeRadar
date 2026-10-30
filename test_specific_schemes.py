import os
import requests
import json

api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

headers = {"X-API-Key": api_key, "Accept": "application/json"}

# 1. Search for specific schemes
queries = [
    "AICTE Pragati Saksham scholarship eligibility deadline official portal",
    "Karnataka SSP Post-Matric scholarship for OBC engineering students eligibility deadline",
    "Central Sector Scheme of Scholarships for College and University Students NSP eligibility"
]

for q in queries:
    print(f"\n=== Query: {q} ===")
    resp = requests.get("https://api.search.tinyfish.ai", params={"query": q, "location": "IN"}, headers=headers, timeout=30)
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        print(f"Total results: {len(results)}")
        for r in results[:3]:
            print(f"  Title: {r.get('title')}")
            print(f"  URL: {r.get('url')}")
            print(f"  Snippet: {r.get('snippet')[:120]}...")

