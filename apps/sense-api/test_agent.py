import requests
import json

payload = {
    "query": "no",
    "history": [
        {"role": "user", "content": "The pump is not starting"},
        {"role": "assistant", "content": "{\"response_text\": \"Is power available?\", \"state\": \"CLARIFYING\"}"}
    ]
}

r = requests.post("http://localhost:8001/chat", json=payload)
output = r.json()

with open("out2.json", "w") as f:
    json.dump(output, f, indent=2)
print("done")
