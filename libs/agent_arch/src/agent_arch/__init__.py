"""
Agent Architecture Library

A simple chatbot agent architecture using PydanticAI and Azure OpenAI.
"""

from .agents import BaseAgent, ChatbotAgent
from .orchestrator import AgentOrchestrator
from .types import AgentRequest, AgentResponse, AgentType

__version__ = "0.1.0"
__all__ = [
    "AgentOrchestrator",
    "BaseAgent",
    "ChatbotAgent",
    "AgentRequest",
    "AgentResponse",
    "AgentType",
]
