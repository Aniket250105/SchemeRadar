import os
import requests
import json

api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

# 1. Inspect Fetch errors for https://ssp.karnataka.gov.in/
print("--- FETCH INSPECT ---")
f_resp = requests.post(
    "https://api.fetch.tinyfish.ai",
    json={"urls": ["https://ssp.karnataka.gov.in/"], "format": "markdown", "purpose": "Scholarship eligibility"},
    headers=headers,
    timeout=30
)
print("Fetch status:", f_resp.status_code)
print("Fetch body:", f_resp.text)

# Also test another URL on Fetch, e.g. buddy4study or scholarships.gov.in
f_resp2 = requests.post(
    "https://api.fetch.tinyfish.ai",
    json={"urls": ["https://scholarships.gov.in"], "format": "markdown"},
    headers=headers,
    timeout=30
)
print("Fetch scholarships.gov.in status:", f_resp2.status_code)
print("Fetch scholarships.gov.in results count:", len(f_resp2.json().get("results", [])))
if f_resp2.json().get("errors"):
    print("Fetch scholarships.gov.in errors:", f_resp2.json().get("errors"))

# 2. Inspect Agent 403
print("\n--- AGENT INSPECT ---")
# Test simple payload that worked earlier:
a_resp_simple = requests.post(
    "https://agent.tinyfish.ai/v1/automation/run-sse",
    json={"url": "https://ssp.karnataka.gov.in", "goal": "Extract scholarship info"},
    headers=headers,
    stream=True,
    timeout=20
)
print("Agent simple payload status:", a_resp_simple.status_code)
if a_resp_simple.status_code != 200:
    print("Agent simple error:", a_resp_simple.text)

# Test payload with output_schema:
a_resp_schema = requests.post(
    "https://agent.tinyfish.ai/v1/automation/run-sse",
    json={
        "url": "https://ssp.karnataka.gov.in",
        "goal": "Extract scholarship info",
        "output_schema": {"type": "object", "properties": {"name": {"type": "string"}}}
    },
    headers=headers,
    stream=True,
    timeout=20
)
print("Agent with schema status:", a_resp_schema.status_code)
if a_resp_schema.status_code != 200:
    print("Agent schema error:", a_resp_schema.text)

