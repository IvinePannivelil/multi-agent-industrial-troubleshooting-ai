import sys
import json
import traceback

try:
    from services.agents import AgentRouter
    router = AgentRouter()
    result = router.run("How do I troubleshoot a Tetra Pak pasteurizer?")
    print("SUCCESS:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("FAILED WITH EXCEPTION:")
    traceback.print_exc()
