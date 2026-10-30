import os
import sys
import json
import time
import requests

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Load API key
api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

print("=" * 70)
print("AUDIT: LIVE TINYFISH API VERIFICATION & RESPONSE INSPECTION")
print(f"API Key Configured: {bool(api_key)} (Prefix: {api_key[:12]}...)")
print("=" * 70)

headers = {
    "X-API-Key": api_key,
    "Accept": "application/json",
}

# -------------------------------------------------------------
# 1. AUDIT SEARCH API
# -------------------------------------------------------------
print("\n[1] AUDITING TINYFISH SEARCH API (GET https://api.search.tinyfish.ai)")
search_url = "https://api.search.tinyfish.ai"
search_params = {
    "query": "Karnataka SSP scholarship 2026 eligibility B.Tech deadline portal",
    "location": "IN",
}
t0 = time.time()
search_resp = requests.get(search_url, params=search_params, headers=headers, timeout=30)
search_latency = time.time() - t0

print(f"  HTTP Status: {search_resp.status_code}")
print(f"  Latency: {search_latency:.2f}s")
print(f"  Headers Returned: {dict(list(search_resp.headers.items())[:5])}")

if search_resp.status_code == 200:
    search_data = search_resp.json()
    print(f"  Response Top-Level Keys: {list(search_data.keys()) if isinstance(search_data, dict) else type(search_data)}")
    results = search_data.get("results", [])
    print(f"  Total Results Count: {len(results)}")
    print(f"  First Result Raw JSON:")
    if results:
        print(json.dumps(results[0], indent=2))
else:
    print(f"  Search Error: {search_resp.text}")

# -------------------------------------------------------------
# 2. AUDIT FETCH API
# -------------------------------------------------------------
print("\n[2] AUDITING TINYFISH FETCH API (POST https://api.fetch.tinyfish.ai)")
fetch_url = "https://api.fetch.tinyfish.ai"

# Pick the first real URL from search results or fallback
target_url = "https://ssp.karnataka.gov.in"
if search_resp.status_code == 200 and search_resp.json().get("results"):
    for r in search_resp.json()["results"]:
        u = r.get("url", "")
        if "ssp.karnataka" in u or "scholarships.gov.in" in u:
            target_url = u
            break

print(f"  Target URL: {target_url}")
fetch_payload = {
    "urls": [target_url],
    "format": "markdown",
    "purpose": "Extract scholarship eligibility criteria, income limit, courses, and application portal link",
    "links": True,
    "per_url_timeout_ms": 30000,
}
fetch_headers = {**headers, "Content-Type": "application/json"}

t0 = time.time()
fetch_resp = requests.post(fetch_url, json=fetch_payload, headers=fetch_headers, timeout=40)
fetch_latency = time.time() - t0

print(f"  HTTP Status: {fetch_resp.status_code}")
print(f"  Latency: {fetch_latency:.2f}s")

if fetch_resp.status_code == 200:
    fetch_data = fetch_resp.json()
    print(f"  Response Top-Level Keys: {list(fetch_data.keys()) if isinstance(fetch_data, dict) else type(fetch_data)}")
    f_results = fetch_data.get("results", [])
    print(f"  Results Count: {len(f_results)}")
    if f_results:
        first_res = f_results[0]
        print(f"  Keys in first result: {list(first_res.keys())}")
        print(f"  Title: {first_res.get('title')}")
        print(f"  URL: {first_res.get('url')}")
        text_content = first_res.get("text", "")
        print(f"  Markdown Text Length: {len(text_content)} chars")
        print(f"  Markdown Text Sample:\n{text_content[:300]}...")
        links = first_res.get("links", [])
        print(f"  Extracted Hyperlinks Count: {len(links)}")
        if links:
            print(f"  Sample Links: {links[:3]}")
else:
    print(f"  Fetch Error: {fetch_resp.text}")

# -------------------------------------------------------------
# 3. AUDIT AGENT API
# -------------------------------------------------------------
print("\n[3] AUDITING TINYFISH AGENT API (POST https://agent.tinyfish.ai/v1/automation/run-sse)")
agent_url = "https://agent.tinyfish.ai/v1/automation/run-sse"

agent_payload = {
    "url": "https://ssp.karnataka.gov.in",
    "goal": "Identify scholarship notices and extract scheme name, eligible courses, income limit, and application deadline into JSON format.",
    "output_schema": {
        "type": "object",
        "properties": {
            "scheme_name": {"type": "string"},
            "provider": {"type": "string"},
            "eligible_courses": {"type": "array", "items": {"type": "string"}},
            "maximum_income": {"type": "number"},
            "scholarship_amount": {"type": "string"},
            "application_deadline": {"type": "string"},
            "application_url": {"type": "string"}
        }
    },
    "browser_profile": "lite",
    "agent_config": {
        "max_steps": 10,
        "max_duration_seconds": 35
    }
}

t0 = time.time()
print(f"  Request Payload:")
print(json.dumps(agent_payload, indent=2))

events_received = []
final_agent_result = None

try:
    with requests.post(agent_url, json=agent_payload, headers=fetch_headers, stream=True, timeout=45) as resp:
        print(f"  HTTP Status: {resp.status_code}")
        for line in resp.iter_lines():
            if time.time() - t0 > 30:  # Cap wait to 30s for audit
                print("  [Audit: stopping stream after 30s window]")
                break
            if not line:
                continue
            decoded = line.decode("utf-8", errors="ignore").strip()
            if decoded.startswith("data:"):
                try:
                    event = json.loads(decoded[5:].strip())
                    evt_type = event.get("type")
                    events_received.append(evt_type)
                    print(f"  -> SSE Event [{evt_type}]: {str(event)[:120]}...")
                    if evt_type in ("COMPLETE", "DONE"):
                        final_agent_result = event.get("result")
                        break
                    elif evt_type == "TF_API_RESULT" and not final_agent_result:
                        final_agent_result = event.get("result")
                except Exception:
                    pass
except Exception as e:
    print(f"  Agent API error: {e}")

print(f"\n  Total SSE Events Captured: {len(events_received)}")
print(f"  Event Types Observed: {list(set(events_received))}")
if final_agent_result:
    print(f"  Agent Extracted Result: {json.dumps(final_agent_result, indent=2)[:300]}...")

print("\n" + "=" * 70)
print("AUDIT COMPLETE")
print("=" * 70)

