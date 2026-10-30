import os
import json
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
api_key = os.getenv("TINYFISH_API_KEY", "").strip()

print(f"API Key present: {bool(api_key)}, Length: {len(api_key)}")

headers = {
    "X-API-Key": api_key,
    "Accept": "application/json",
    "User-Agent": "SchemeRadar-Test/1.0"
}

# 1. Test Search API
print("\n--- TEST 1: TinyFish Search API ---")
search_url = "https://api.search.tinyfish.ai"
query = "Karnataka SSP scholarship for B.Tech engineering students eligibility official portal"
try:
    resp = requests.get(search_url, params={"query": query}, headers=headers, timeout=30)
    print(f"Search API Status Code: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Search response type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            results = data.get("results") or data.get("organic_results") or data.get("data") or []
            print(f"Result count: {len(results)}")
            for idx, r in enumerate(results[:3]):
                print(f"  [{idx+1}] {r.get('title')} -> {r.get('url')}")
        elif isinstance(data, list):
            print(f"List items: {len(data)}")
            for idx, r in enumerate(data[:3]):
                print(f"  [{idx+1}] {r.get('title')} -> {r.get('url')}")
    else:
        print(f"Search error response: {resp.text[:300]}")
except Exception as e:
    print(f"Search API exception: {e}")

# 2. Test Fetch API
print("\n--- TEST 2: TinyFish Fetch API ---")
fetch_url = "https://api.fetch.tinyfish.ai"
test_target = "https://scholarships.gov.in"
fetch_payload = {
    "urls": [test_target],
    "format": "markdown",
    "purpose": "Extract scholarship eligibility criteria and schemes"
}
fetch_headers = {**headers, "Content-Type": "application/json"}
try:
    f_resp = requests.post(fetch_url, json=fetch_payload, headers=fetch_headers, timeout=30)
    print(f"Fetch API Status Code: {f_resp.status_code}")
    if f_resp.status_code == 200:
        f_data = f_resp.json()
        print(f"Fetch response keys: {list(f_data.keys()) if isinstance(f_data, dict) else type(f_data)}")
        results = f_data.get("results", [])
        if results and isinstance(results, list):
            text = results[0].get("text") or results[0].get("content") or ""
            print(f"Fetched text snippet ({len(text)} chars):\n{text[:250]}...")
    else:
        print(f"Fetch error response: {f_resp.text[:300]}")
except Exception as e:
    print(f"Fetch API exception: {e}")

# 3. Test Agent API
print("\n--- TEST 3: TinyFish Agent API ---")
agent_url = "https://agent.tinyfish.ai/v1/automation/run"
agent_payload = {
    "url": "https://scholarships.gov.in",
    "goal": "Extract national scholarship portal banner text and primary schemes. Return structured JSON.",
    "browser_profile": "lite"
}
try:
    a_resp = requests.post(agent_url, json=agent_payload, headers=fetch_headers, timeout=45)
    print(f"Agent API Status Code: {a_resp.status_code}")
    if a_resp.status_code == 200:
        a_data = a_resp.json()
        print(f"Agent response keys: {list(a_data.keys()) if isinstance(a_data, dict) else type(a_data)}")
        result = a_data.get("result") or a_data.get("output") or a_data
        print(f"Agent result preview: {str(result)[:250]}...")
    else:
        print(f"Agent error response: {a_resp.text[:300]}")
except Exception as e:
    print(f"Agent API exception: {e}")
