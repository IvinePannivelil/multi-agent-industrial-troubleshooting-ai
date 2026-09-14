"""
Product Recommendation Agent
==============================
Recommends industrial hardware from the Goose Mart catalog.

Capabilities:
  - Search product catalog via tools.product_search()
  - Cross-reference specs with retrieved manual context
  - Compare vendors and suggest alternatives

Tools used:
  - tools.product_search()
  - hybrid_retrieval.retrieve() (for spec context)
"""

import logging
from core.config import AGENT_LLM_TEMPERATURE
from services.agents.base_agent import BaseAgent, AgentContext, AgentResponse, ToolCall
from services.agents.tools import product_search
from services.hybrid_retrieval import retrieve as hybrid_retrieve
from services.llm.llm_client import llm_client

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are Goose Sense Product Recommendation Agent — a senior industrial procurement specialist.

Using the product catalog results and technical context below, provide:
1. Top recommended product(s) with justification
2. A comparison table (Name | Vendor | Price | In Stock | Key Spec)
3. Alternative options if the primary is unavailable
4. Any relevant spec notes from the technical documentation

Product Catalog Results:
{products}

Technical Context from Knowledge Base:
{context}

Format as clear Markdown with comparison table. Be concise, factual, and procurement-ready.
CRITICAL INSTRUCTION: You MUST conclude every recommendation with a direct markdown link to Goose Mart. Format it exactly as: '**Ready to proceed? Visit [Goose Mart](https://goosefly.in/goosemart)**'. Do not link to Elevate or any other vertical.
"""


class ProductRecommendationAgent(BaseAgent):
    name = "ProductRecommendationAgent"



    def get_required_tools(self):
        return ["product_search", "hybrid_retrieval"]

    def execute(self, query: str, context: AgentContext) -> AgentResponse:
        logger.info("[ProductRecommendationAgent] Executing for query: '%s'", query)
        tool_calls: list = []

        # Step 1 — Product catalog search
        try:
            products = product_search(query)
            tool_calls.append(ToolCall(
                tool_name="product_search",
                query_used=query,
                result_count=len(products),
                success=True,
            ))
            logger.info("[ProductRecommendationAgent] Found %d products.", len(products))
        except Exception as e:
            logger.error("[ProductRecommendationAgent] product_search failed: %s", e)
            products = []
            tool_calls.append(ToolCall("product_search", query, 0, False))

        # Step 2 — Optional RAG context for spec grounding
        try:
            chunks = hybrid_retrieve(query)
            tool_calls.append(ToolCall("hybrid_retrieval", query, len(chunks), True))
        except Exception as e:
            logger.warning("[ProductRecommendationAgent] Retrieval failed: %s", e)
            chunks = []

        # Step 3 — Format and generate
        products_str = "\n".join(
            f"- **{p.name}** (SKU: {p.sku}) | {p.vendor} | {p.price_range} | "
            f"{'In Stock' if p.in_stock else 'Out of Stock'}\n"
            f"  {p.description}\n"
            f"  Alternatives: {', '.join(p.alternatives) if p.alternatives else 'None'}"
            for p in products
        ) or "No products found in catalog."

        history_str = "\n".join(f"{msg['role'].capitalize()}: {msg['content']}" for msg in context.history) if context.history else "None"
        context_str = self._format_context(chunks)
        prompt = _SYSTEM_PROMPT.format(products=products_str, context=context_str)
        full_prompt = f"{prompt}\n\nPrevious Conversation Context:\n{history_str}\n\nUser Query: {query}"

        try:
            response_text = llm_client.generate(full_prompt, intent=context.intent)
        except Exception as e:
            logger.error("[ProductRecommendationAgent] LLM failed: %s", e)
            response_text = "Unable to generate product recommendations at this time."

        return AgentResponse(
            response_text=response_text,
            intent=context.intent,
            agent_used=self.name,
            sources=self._build_sources(chunks),
            tool_calls_made=tool_calls,
            state="RESOLVED",
        )
