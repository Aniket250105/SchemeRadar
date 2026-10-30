import os
import json
import requests

api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}

url = "https://agent.tinyfish.ai/v1/automation/run-sse"
payload = {
    "url": "https://ssp.karnataka.gov.in",
    "goal": "Extract scholarship notification titles and deadlines into JSON format."
}

print(f"Calling Agent API SSE endpoint: {url}...")
try:
    with requests.post(url, json=payload, headers=headers, stream=True, timeout=60) as resp:
        print(f"SSE Status Code: {resp.status_code}")
        for idx, line in enumerate(resp.iter_lines()):
            if line:
                decoded = line.decode('utf-8', errors='ignore')
                print(f"Line {idx+1}: {decoded[:120]}")
                if idx > 15:
                    print("... Truncated for test ...")
                    break
except Exception as e:
    print(f"Agent SSE exception: {e}")

