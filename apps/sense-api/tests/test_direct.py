import sys
import os
from pathlib import Path
import json
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from services.agents import AgentRouter
    router = AgentRouter()
    result = router.run("How do I troubleshoot a Tetra Pak pasteurizer?")
    print("SUCCESS:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print("FAILED WITH EXCEPTION:")
    traceback.print_exc()
