import sys
import json
import logging
# Suppress general logs for cleaner output
logging.getLogger().setLevel(logging.WARNING)

from services.agents.agent_router import agent_router

history = []
results = []
queries = [
    "My motor is broken.",
    "It's a Siemens.",
    "No fault codes, just smoke.",
    "I don't know anything else."
]

for q in queries:
    res = agent_router.run(q, history=history)
    history.append({"role": "user", "content": q})
    history.append({"role": "assistant", "content": res['response_text']})
    results.append(res)
    
with open("test_results.json", "w") as f:
    json.dump(results, f, indent=2)
