"""
Simple chatbot agent using PydanticAI with Azure OpenAI.
"""

import os

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.azure import AzureProvider

from ..types import AgentRequest, AgentResponse, AgentType
from .base_agent import BaseAgent


class ChatbotAgent(BaseAgent):
    """Simple chatbot agent using PydanticAI with Azure OpenAI."""

    def __init__(self):
        """Initialize the chatbot agent."""
        super().__init__()
        self.agent_type = AgentType.CHATBOT

        # Get Azure OpenAI configuration from environment
        api_version = os.getenv('API_VERSION')
        endpoint = os.getenv('ENDPOINT')
        api_key = os.getenv('API_KEY')
        model = os.getenv('MODEL')

        if not all([api_version, endpoint, api_key, model]):
            raise ValueError(
                "Missing Azure OpenAI configuration. Please set API_VERSION, "
                "ENDPOINT, API_KEY, and MODEL environment variables."
            )

        # Create Azure OpenAI model using AzureProvider
        self.model = OpenAIModel(
            model,  # type: ignore
            provider=AzureProvider(
                azure_endpoint=endpoint,
                api_version=api_version,
                api_key=api_key,
            ),
        )

        # Create PydanticAI agent
        self.ai_agent = Agent(
            model=self.model,
            system_prompt="You are a helpful AI assistant. Provide clear, concise, and helpful responses to user questions."
        )

    def can_handle_task(self, request: AgentRequest) -> bool:
        """This chatbot can handle any task."""
        return True

    async def process_task(self, request: AgentRequest) -> AgentResponse:
        """Process a chat request using PydanticAI."""
        try:
            # Run the AI agent
            result = await self.ai_agent.run(request.message)

            return AgentResponse(
                response=result.output,
                agent_type=self.agent_type,
                success=True,
                metadata={
                    "model": self.model.model_name,
                    "usage": result.usage().__dict__ if result.usage() else None
                }
            )

        except Exception as e:
            return AgentResponse(
                response="I'm sorry, I encountered an error while processing your request.",
                agent_type=self.agent_type,
                success=False,
                error_message=str(e)
            )
