import sys
import os
from pathlib import Path

# Ensure apps/sense-api root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.agents.troubleshooting_agent import TroubleshootingAgent
from services.agents.base_agent import AgentContext

agent = TroubleshootingAgent()

print("=== SCENARIO 1: Centrifugal Pump ===")
context1 = AgentContext(
    query="no",
    intent="TROUBLESHOOTING",
    history=[
        {"role": "user", "content": "The pump is not starting"},
        {"role": "assistant", "content": "{\"response_text\": \"Is power available?\", \"state\": \"CLARIFYING\"}"}
    ]
)
response1 = agent.execute("no", context1)
print("TEXT:", response1.response_text)
print("STATE:", response1.state)
print("STEPS:", response1.steps)
print("MEDIA:", response1.media)
print("ESCALATION:", response1.ecosystem_escalation)

print("\n=== SCENARIO 2: Pasteurizer Heating ===")
context2 = AgentContext(
    query="no, there is no steam",
    intent="TROUBLESHOOTING",
    history=[
        {"role": "user", "content": "The pasteurizer is not heating up"},
        {"role": "assistant", "content": "{\"response_text\": \"Is steam pressure available?\", \"state\": \"CLARIFYING\"}"}
    ]
)
response2 = agent.execute("no", context2)
print("TEXT:", response2.response_text)
print("STATE:", response2.state)
print("STEPS:", response2.steps)
print("MEDIA:", response2.media)
print("ESCALATION:", response2.ecosystem_escalation)
