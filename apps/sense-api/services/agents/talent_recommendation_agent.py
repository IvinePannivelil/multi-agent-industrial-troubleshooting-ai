"""
Talent Recommendation Agent
=============================
Recommends engineers from the HireMyEngineer platform.

Capabilities:
  - Search talent database via tools.engineer_search()
  - Match engineer specialisms to the user's requirement
  - Return structured expert profiles with availability

Tools used:
  - tools.engineer_search()
"""

import logging
from core.config import AGENT_LLM_TEMPERATURE
from services.agents.base_agent import BaseAgent, AgentContext, AgentResponse, ToolCall
from services.agents.tools import engineer_search
from services.llm.llm_client import llm_client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an Industrial Talent Recommendation Agent — a senior technical recruiter for industrial engineers.

Using the talent search results below, provide:
1. Top recommended engineer(s) with clear justification
2. A structured profile table (Name | Specialisms | Experience | Availability | Location)
3. A brief note on how each engineer's skills match the requirement
4. A call-to-action directing the user to the HireMyEngineer platform

Talent Search Results:
{talent}

Format in Markdown. Be professional, concise, and focused on skills-fit.
CRITICAL INSTRUCTION: You MUST conclude every recommendation with a direct markdown link to HireMyEngineer. Format it exactly as: '**Ready to proceed? Visit [HireMyEngineer](https://www.hiremyengineer.com/)**'. Do not link to any other vertical.
"""


class TalentRecommendationAgent(BaseAgent):
    name = "TalentRecommendationAgent"



    def get_required_tools(self):
        return ["engineer_search"]

    def execute(self, query: str, context: AgentContext) -> AgentResponse:
        logger.info("[TalentRecommendationAgent] Executing for query: '%s'", query)
        tool_calls: list = []

        # Step 1 — Engineer search
        try:
            engineers = engineer_search(query)
            tool_calls.append(ToolCall(
                tool_name="engineer_search",
                query_used=query,
                result_count=len(engineers),
                success=True,
            ))
            logger.info("[TalentRecommendationAgent] Found %d engineers.", len(engineers))
        except Exception as e:
            logger.error("[TalentRecommendationAgent] engineer_search failed: %s", e)
            engineers = []
            tool_calls.append(ToolCall("engineer_search", query, 0, False))

        # Step 2 — Format talent
        talent_str = "\n".join(
            f"- **{e.name}** (ID: {e.engineer_id})\n"
            f"  Specialisms: {', '.join(e.specialisms)}\n"
            f"  Experience: {e.experience_years} years | {e.availability} | {e.location}"
            for e in engineers
        ) or "No engineers found matching this requirement."

        prompt = _SYSTEM_PROMPT.format(talent=talent_str)
        history_str = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in context.history) if context.history else "None"
        full_prompt = f"{prompt}\n\nPrevious Conversation Context:\n{history_str}\n\nUser Requirement: {query}"

        # Step 3 — Generate response
        try:
            response_text = llm_client.generate(full_prompt, intent=context.intent)
        except Exception as e:
            logger.error("[TalentRecommendationAgent] LLM failed: %s", e)
            response_text = "Unable to generate talent recommendations at this time."

        return AgentResponse(
            response_text=response_text,
            intent=context.intent,
            agent_used=self.name,
            sources=[],
            tool_calls_made=tool_calls,
            state="RESOLVED",
            search_query=query,
        )
