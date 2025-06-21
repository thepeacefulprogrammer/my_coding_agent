"""
Base agent class for the multi-agent architecture.
"""

from abc import ABC, abstractmethod

from ..types import AgentRequest, AgentResponse, AgentType


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(self):
        """Initialize the base agent."""
        self.agent_type: AgentType = AgentType.CHATBOT

    @abstractmethod
    def can_handle_task(self, request: AgentRequest) -> bool:
        """Check if this agent can handle the given request.

        Args:
            request: The request to evaluate

        Returns:
            True if the agent can handle the request
        """
        pass

    @abstractmethod
    async def process_task(self, request: AgentRequest) -> AgentResponse:
        """Process a request and return a response.

        Args:
            request: The request to process

        Returns:
            Agent response with results
        """
        pass
