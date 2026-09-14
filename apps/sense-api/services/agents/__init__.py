"""
Goose Sense Agent Framework
============================
Exports the main AgentRouter for use in main.py.

Usage:
    from services.agents import AgentRouter
    router = AgentRouter()
    response = router.run(query, history)
"""

from services.agents.agent_router import AgentRouter

__all__ = ["AgentRouter"]
