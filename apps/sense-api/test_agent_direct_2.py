import asyncio
from services.agents.troubleshooting_agent import TroubleshootingAgent
from services.agents.base_agent import AgentContext

agent = TroubleshootingAgent()
context = AgentContext(
    query="no, there is no steam",
    intent="TROUBLESHOOTING",
    history=[
        {"role": "user", "content": "The pasteurizer is not heating up"},
        {"role": "assistant", "content": "{\"response_text\": \"Is steam pressure available?\", \"state\": \"CLARIFYING\"}"}
    ]
)

response = agent.execute("no", context)
print("--- RESOLVED RESPONSE ---")
print("TEXT:", response.response_text)
print("STATE:", response.state)
print("STEPS:", response.steps)
print("MEDIA:", response.media)
print("ESCALATION:", response.ecosystem_escalation)
