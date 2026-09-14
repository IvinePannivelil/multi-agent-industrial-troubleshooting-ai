import asyncio
from services.agents.troubleshooting_agent import TroubleshootingAgent
from services.agents.base_agent import AgentContext

agent = TroubleshootingAgent()
context = AgentContext(
    query="no",
    intent="TROUBLESHOOTING",
    history=[
        {"role": "user", "content": "The pump is not starting"},
        {"role": "assistant", "content": "{\"response_text\": \"Is power available?\", \"state\": \"CLARIFYING\"}"}
    ]
)

response = agent.execute("no", context)
print("--- RESOLVED RESPONSE ---")
print("TEXT:", response.response_text)
print("STATE:", response.state)
print("STEPS:", response.steps)
print("MEDIA:", response.media)
print("ESCALATION:", response.ecosystem_escalation)
