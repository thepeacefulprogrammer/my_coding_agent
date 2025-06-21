"""
Type definitions for the agent architecture library.
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AgentType(Enum):
    """Types of agents available in the system."""
    CHATBOT = "chatbot"


class AgentRequest(BaseModel):
    """Request sent to an agent."""
    message: str
    context: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Response from an agent."""
    response: str
    agent_type: AgentType
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
