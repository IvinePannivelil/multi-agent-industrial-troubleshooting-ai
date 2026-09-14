"""
Agent Router
=============
Classifies intent, selects the appropriate agent, executes it,
and returns a standardised AgentResponse.

This is the single entry point for the /chat endpoint.

Pipeline:
  query
    -> IntentClassifier.classify()     [rules + LLM]
    -> AGENT_REGISTRY[intent]          [agent selection]
    -> agent.execute(query, context)   [tool calls + LLM]
    -> AgentResponse                   [structured output]

Adding a new agent:
  1. Implement BaseAgent in its own file
  2. Add entry to AGENT_REGISTRY below (intent -> agent class)
"""

import logging
from typing import Dict, Type

from services.intent_classifier import (
    intent_classifier,
    INTENT_TROUBLESHOOTING,
    INTENT_PRODUCT_SEARCH,
    INTENT_TRAINING_REQUEST,
    INTENT_ENGINEERING_TALENT,
    INTENT_GENERAL_QA,
)
from services.agents.base_agent import BaseAgent, AgentContext, AgentResponse
from services.agents.troubleshooting_agent        import TroubleshootingAgent
from services.agents.product_recommendation_agent import ProductRecommendationAgent
from services.agents.training_recommendation_agent import TrainingRecommendationAgent
from services.agents.talent_recommendation_agent  import TalentRecommendationAgent

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GeneralQAAgent — wraps the existing hybrid RAG pipeline as fallback
# ---------------------------------------------------------------------------

class GeneralQAAgent(BaseAgent):
    """
    Fallback agent — uses the hybrid RAG pipeline for general industrial Q&A.
    """
    name = "GeneralQAAgent"

    def execute(self, query: str, context: AgentContext) -> AgentResponse:
        logger.info("[GeneralQAAgent] Executing hybrid RAG pipeline.")
        from services.hybrid_retrieval import retrieve as hybrid_retrieve
        from services.llm.llm_client import llm_client
        import json

        # Step 1 — Hybrid retrieval
        retrieved = hybrid_retrieve(query)
        context_parts = []
        sources = []
        for chunk in retrieved:
            text = chunk.get("text", "")
            doc_name = chunk.get("document_name", "Unknown")
            sources.append({"document_name": doc_name, "section": chunk.get("section", ""), "page_number": chunk.get("page_number", 0)})
            context_parts.append(f"[Source: {doc_name}] {text}")
        
        context_str = "\n\n".join(context_parts) if context_parts else "No relevant context found."
        
        # Step 2 — LLM call
        prompt = f"You are an industrial assistant. Use the following context to answer: {context_str}\n\nQuery: {query}\n\nRespond in JSON: {{\"chatResponse\": \"...\"}}"
        try:
            raw_res = llm_client.generate(prompt, format="json")
            if raw_res.startswith("```"):
                raw_res = raw_res.split("```")[1].split("```")[0].strip()
                if raw_res.startswith("json"): raw_res = raw_res[4:].strip()
            
            result = json.loads(raw_res)
        except Exception:
            result = {"chatResponse": "I'm sorry, I couldn't process that general question."}

        return AgentResponse(
            response_text=result.get("chatResponse", ""),
            intent=context.intent,
            agent_used=self.name,
            sources=sources,
            state="RESOLVED"
        )


# ---------------------------------------------------------------------------
# Agent registry — maps intent -> agent class
# ---------------------------------------------------------------------------

AGENT_REGISTRY: Dict[str, Type[BaseAgent]] = {
    INTENT_TROUBLESHOOTING:    TroubleshootingAgent,
    INTENT_PRODUCT_SEARCH:     ProductRecommendationAgent,
    INTENT_TRAINING_REQUEST:   TrainingRecommendationAgent,
    INTENT_ENGINEERING_TALENT: TalentRecommendationAgent,
    INTENT_GENERAL_QA:         GeneralQAAgent,
}


# ---------------------------------------------------------------------------
# Agent Router
# ---------------------------------------------------------------------------

class AgentRouter:
    """
    Routes a user query to the appropriate specialist agent.

    Instantiates agents lazily on first use and caches them.
    """

    def __init__(self):
        self._agent_cache: Dict[str, BaseAgent] = {}

    def _get_agent(self, intent: str) -> BaseAgent:
        """Return a cached agent instance for the given intent."""
        if intent not in self._agent_cache:
            agent_cls = AGENT_REGISTRY.get(intent, GeneralQAAgent)
            self._agent_cache[intent] = agent_cls()
            logger.info("[AgentRouter] Instantiated agent: %s", agent_cls.__name__)
        return self._agent_cache[intent]

    def run(self, query: str, history: list = None) -> dict:
        """
        Full agent pipeline entry point.

        Args:
            query:   User's raw query string.
            history: Conversation history (forwarded to context).

        Returns:
            Dict with keys: response_text, intent, agent_used, sources,
                            state, search_query, tool_calls_made
        """
        history = history or []

        # Step 1 — Intent classification
        intent = intent_classifier.classify(query, history=history)
        logger.info("[AgentRouter] Intent detected: %s", intent)

        # Step 2 — Agent selection
        agent = self._get_agent(intent)
        logger.info(
            "[AgentRouter] Selected agent: %s | Tools: %s",
            agent.name, agent.get_required_tools(),
        )

        # Step 3 — Build context
        context = AgentContext(
            query=query,
            intent=intent,
            history=history,
        )

        # Step 4 — Execute agent
        try:
            response: AgentResponse = agent.execute(query, context)
        except Exception as e:
            logger.error("[AgentRouter] Agent '%s' raised an exception: %s", agent.name, e)
            response = AgentResponse(
                response_text=(
                    "I encountered an unexpected error processing your request. "
                    "Please try again."
                ),
                intent=intent,
                agent_used=agent.name,
                state="RESOLVED",
            )

        # Step 5 — Log tool calls
        for tc in response.tool_calls_made:
            logger.info(
                "[AgentRouter] Tool used: %s | query='%s' | results=%d | success=%s",
                tc.tool_name, tc.query_used, tc.result_count, tc.success,
            )

        # Step 6 — Serialise and return
        return {
            "response_text":   response.response_text,
            "intent":          response.intent,
            "agent_used":      response.agent_used,
            "sources":         response.sources,
            "state":           response.state,
            "search_query":    response.search_query,
            "media":           response.media,
            "steps":           response.steps,
            "ecosystem_escalation": response.ecosystem_escalation,
            "tool_calls_made": [
                {
                    "tool":    tc.tool_name,
                    "results": tc.result_count,
                    "success": tc.success,
                }
                for tc in response.tool_calls_made
            ],
        }


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

agent_router = AgentRouter()
