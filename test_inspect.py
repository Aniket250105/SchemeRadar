import os
import json
import requests

api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

headers = {"X-API-Key": api_key, "Accept": "application/json"}

# Test Search and print results safely
query = "Karnataka SSP scholarship B.Tech eligibility portal"
resp = requests.get("https://api.search.tinyfish.ai", params={"query": query}, headers=headers, timeout=30)
print(f"Search status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    results = data.get("results", [])
    print(f"Total results: {len(results)}")
    for i, r in enumerate(results[:5]):
        print(f"\nResult {i+1}:")
        print(f"  Title: {r.get('title', '').encode('ascii', 'ignore').decode('ascii')}")
        print(f"  URL: {r.get('url')}")
        print(f"  Snippet: {r.get('snippet', '')[:100].encode('ascii', 'ignore').decode('ascii')}...")

# Test Fetch and print results safely
f_payload = {
    "urls": ["https://scholarships.gov.in"],
    "format": "markdown",
    "purpose": "Extract scholarship eligibility criteria"
}
f_resp = requests.post("https://api.fetch.tinyfish.ai", json=f_payload, headers={**headers, "Content-Type": "application/json"}, timeout=30)
print(f"\nFetch status: {f_resp.status_code}")
if f_resp.status_code == 200:
    f_data = f_resp.json()
    res = f_data.get("results", [])
    if res:
        print(f"Fetched title: {res[0].get('title', '').encode('ascii', 'ignore').decode('ascii')}")
        print(f"Fetched text length: {len(res[0].get('text', ''))}")

