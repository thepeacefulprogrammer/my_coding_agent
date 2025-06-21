"""
Agent orchestrator for managing and routing requests to agents.
"""

from typing import Optional

from .agents import ChatbotAgent
from .types import AgentRequest, AgentResponse


class AgentOrchestrator:
    """Orchestrator for managing and routing requests to agents."""

    def __init__(self):
        """Initialize the orchestrator with the chatbot agent."""
        self.chatbot_agent = ChatbotAgent()

    async def process_request(self, message: str, context: Optional[dict] = None) -> AgentResponse:
        """
        Process a request by routing it to the chatbot agent.

        Args:
            message: The user's message
            context: Optional context information

        Returns:
            AgentResponse: The response from the chatbot agent
        """
        request = AgentRequest(message=message, context=context)

        # Always route to the chatbot agent since it can handle any task
        return await self.chatbot_agent.process_task(request)
