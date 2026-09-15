"""
Training Recommendation Agent
===============================
Recommends Goose Elevate training courses matching the user's query.

Capabilities:
  - Search course catalog via tools.training_search()
  - Match topic keywords to available courses
  - Return structured course list with difficulty and duration

Tools used:
  - tools.training_search()
"""

import logging
from core.config import AGENT_LLM_TEMPERATURE
from services.agents.base_agent import BaseAgent, AgentContext, AgentResponse, ToolCall
from services.agents.tools import training_search
from services.llm.llm_client import llm_client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an Industrial Training Recommendation Agent — an industrial learning advisor.

Using the course catalog results below, provide:
1. Top recommended course(s) with clear justification
2. A structured course list (Title | Level | Duration | Key Topics)
3. A suggested learning path if multiple courses are relevant

Course Catalog Results:
{courses}

Format in Markdown. Be encouraging, practical, and skills-focused.
Mention the Goose Elevate platform as the source of all course content.
CRITICAL INSTRUCTION: You MUST conclude every recommendation with a direct markdown link to Goose Elevate. Format it exactly as: '**Ready to proceed? Visit [Goose Elevate](https://www.gooseelevate.com/)**'. Do not link to any other vertical.
"""


class TrainingRecommendationAgent(BaseAgent):
    name = "TrainingRecommendationAgent"



    def get_required_tools(self):
        return ["training_search"]

    def execute(self, query: str, context: AgentContext) -> AgentResponse:
        logger.info("[TrainingRecommendationAgent] Executing for query: '%s'", query)
        tool_calls: list = []

        # Step 1 — Course search
        try:
            courses = training_search(query)
            tool_calls.append(ToolCall(
                tool_name="training_search",
                query_used=query,
                result_count=len(courses),
                success=True,
            ))
            logger.info("[TrainingRecommendationAgent] Found %d courses.", len(courses))
        except Exception as e:
            logger.error("[TrainingRecommendationAgent] training_search failed: %s", e)
            courses = []
            tool_calls.append(ToolCall("training_search", query, 0, False))

        # Step 2 — Format courses
        courses_str = "\n".join(
            f"- **{c.title}** (ID: {c.course_id})\n"
            f"  Level: {c.level} | Duration: {c.duration}\n"
            f"  Topics: {', '.join(c.topics)}\n"
            f"  {c.description}"
            for c in courses
        ) or "No courses found matching this topic."

        prompt = _SYSTEM_PROMPT.format(courses=courses_str)
        history_str = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in context.history) if context.history else "None"
        full_prompt = f"{prompt}\n\nPrevious Conversation Context:\n{history_str}\n\nUser Query: {query}"

        # Step 3 — Generate response
        try:
            response_text = llm_client.generate(full_prompt, intent=context.intent)
        except Exception as e:
            logger.error("[TrainingRecommendationAgent] LLM failed: %s", e)
            response_text = "Unable to generate training recommendations at this time."

        return AgentResponse(
            response_text=response_text,
            intent=context.intent,
            agent_used=self.name,
            sources=[],          # no RAG sources for training recommendations
            tool_calls_made=tool_calls,
            state="RESOLVED",
            search_query=query,
        )
