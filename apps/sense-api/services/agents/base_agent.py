"""
Base Agent Interface
=====================
Defines the abstract contract all Goose Sense agents must implement,
plus the shared data types passed through the agent pipeline.

Data flow:
  AgentContext  ->  BaseAgent.execute()  ->  AgentResponse

Adding a new agent:
  1. Subclass BaseAgent
  2. Implement execute(query, context) -> AgentResponse
  3. Optionally override get_required_tools()
  4. Register in agent_router.py AGENT_REGISTRY
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Shared data types
# ---------------------------------------------------------------------------

@dataclass
class ToolCall:
    """Records a single tool invocation made by an agent."""
    tool_name:  str
    query_used: str
    result_count: int
    success:    bool


@dataclass
class AgentContext:
    """
    Everything an agent knows when it starts executing.

    Populated by AgentRouter before calling agent.execute().
    """
    query:             str
    intent:            str
    history:           List[Dict[str, Any]] = field(default_factory=list)
    retrieved_chunks:  List[Dict[str, Any]] = field(default_factory=list)  # pre-fetched if any


@dataclass
class AgentResponse:
    """
    Standardised response returned by every agent.
    Maps directly to the /chat API response body.
    """
    response_text:    str
    intent:           str
    agent_used:       str
    sources:          List[Dict[str, Any]] = field(default_factory=list)
    tool_calls_made:  List[ToolCall]       = field(default_factory=list)
    state:            str                  = "RESOLVED"   # RESOLVED | CLARIFYING
    search_query:     str                  = ""
    media:            Optional[Dict[str, Any]] = None
    steps:            Optional[List[str]]      = None
    ecosystem_escalation: Optional[Dict[str, str]] = None


# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------

class BaseAgent(ABC):
    """
    Abstract base for all Goose Sense agents.

    Subclasses must implement execute().
    get_required_tools() is optional — used for logging and future
    dependency injection.
    """

    # Human-readable name — override in each subclass
    name: str = "BaseAgent"

    @abstractmethod
    def execute(self, query: str, context: AgentContext) -> AgentResponse:
        """
        Run the agent for the given query and context.

        Args:
            query:   Original user query string.
            context: Pre-populated AgentContext from the router.

        Returns:
            AgentResponse with response_text, sources, tool_calls_made.
        """

    def get_required_tools(self) -> List[str]:
        """
        Return a list of tool names this agent uses.
        Override in subclasses that call specific tools.
        Used for logging and capability introspection.
        """
        return []

    def _build_sources(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Helper: extract source metadata from retrieved chunks."""
        return [
            {
                "document_name": c.get("document_name", "Unknown"),
                "section":       c.get("section", ""),
                "page_number":   c.get("page_number", 0),
                "chunk_index":   c.get("chunk_index", 0),
            }
            for c in chunks
        ]

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Helper: format retrieved chunks into an LLM-readable string."""
        if not chunks:
            return "No relevant documents found in knowledge base."
        parts = []
        for c in chunks:
            header = f"[{c.get('document_name', 'Unknown')}"
            if c.get("section"):
                header += f" | {c['section']}"
            if c.get("page_number"):
                header += f" | p.{c['page_number']}"
            header += "]"
            parts.append(f"{header}\n{c.get('text', '')}")
        return "\n\n---\n\n".join(parts)
