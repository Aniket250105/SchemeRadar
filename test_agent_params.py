import os
import requests

api_key = os.getenv("TINYFISH_API_KEY", "").strip()
if not api_key and os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TINYFISH_API_KEY"):
                api_key = line.split("=", 1)[1].strip()

headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

# Test 1: with browser_profile lite
r1 = requests.post("https://agent.tinyfish.ai/v1/automation/run-sse", json={"url": "https://scholarships.gov.in", "goal": "Extract info", "browser_profile": "lite"}, headers=headers, stream=True)
print("Test 1 (browser_profile lite):", r1.status_code)

# Test 2: with agent_config
r2 = requests.post("https://agent.tinyfish.ai/v1/automation/run-sse", json={"url": "https://scholarships.gov.in", "goal": "Extract info", "agent_config": {"max_steps": 10}}, headers=headers, stream=True)
print("Test 2 (agent_config max_steps):", r2.status_code)
if r2.status_code != 200:
    print("Test 2 text:", r2.text)

# Test 3: with agent_config max_duration_seconds
r3 = requests.post("https://agent.tinyfish.ai/v1/automation/run-sse", json={"url": "https://scholarships.gov.in", "goal": "Extract info", "agent_config": {"max_duration_seconds": 35}}, headers=headers, stream=True)
print("Test 3 (agent_config max_duration_seconds):", r3.status_code)
if r3.status_code != 200:
    print("Test 3 text:", r3.text)

