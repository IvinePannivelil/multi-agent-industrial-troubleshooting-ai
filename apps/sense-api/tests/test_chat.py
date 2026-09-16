import urllib.request
import json
import sys

url = "http://localhost:8001/chat"
data = {"query": "How do I troubleshoot a Tetra Pak pasteurizer?"}
req = urllib.request.Request(url, json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code}")
    print(e.read().decode("utf-8", errors="ignore"))
except Exception as e:
    print(f"Error: {e}")
