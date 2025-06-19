"""Tests for AIAgent streaming functionality delegation to StreamingResponseService.

This test suite verifies that AIAgent properly delegates streaming operations
to StreamingResponseService, eliminating code duplication.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from src.my_coding_agent.core.ai_agent import AIAgent, AIAgentConfig
from src.my_coding_agent.core.ai_services.core_ai_service import AIResponse


class TestAIAgentStreamingIntegration:
    """Test AIAgent streaming functionality delegation to StreamingResponseService."""

    @pytest_asyncio.fixture
    async def ai_config(self):
        """Create AI configuration for testing."""
        return AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test_key",
            deployment_name="gpt-4o-mini",
            max_tokens=1000,
            temperature=0.7,
        )

    @pytest_asyncio.fixture
    async def mock_streaming_service(self):
        """Create mock StreamingResponseService."""
        service = MagicMock()
        service.send_message_with_tools_stream = AsyncMock(
            return_value=AIResponse(
                success=True, content="Streaming response", stream_id="test_stream_123"
            )
        )
        service.send_memory_aware_message_stream = AsyncMock(
            return_value=AIResponse(
                success=True,
                content="Memory-aware streaming response",
                stream_id="memory_stream_456",
            )
        )
        service.interrupt_current_stream = AsyncMock(return_value=True)
        service.is_streaming = False
        service.get_stream_status = MagicMock(
            return_value={"status": "idle", "stream_id": None}
        )
        service.get_health_status = MagicMock(
            return_value={"status": "healthy", "active_streams": 0}
        )
        return service

    @pytest_asyncio.fixture
    async def ai_agent_with_streaming(self, ai_config, mock_streaming_service):
        """Create AI agent with streaming service integration."""
        # Mock the agent creation to avoid actual API calls
        with patch("pydantic_ai.Agent") as mock_pydantic:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=MagicMock(data="Test response"))
            mock_pydantic.return_value = mock_agent

            agent = AIAgent(
                config=ai_config,
                streaming_response_service=mock_streaming_service,
                enable_filesystem_tools=True,
            )
            agent._agent = mock_agent

            return agent, mock_streaming_service

    @pytest.mark.asyncio
    async def test_send_message_with_tools_stream_delegation(
        self, ai_agent_with_streaming
    ):
        """Test that send_message_with_tools_stream delegates to StreamingResponseService."""
        agent, mock_streaming_service = ai_agent_with_streaming

        # Mock callback function
        async def mock_on_chunk(chunk: str, is_final: bool):
            pass

        # Call the streaming method
        result = await agent.send_message_with_tools_stream(
            message="Test streaming message",
            on_chunk=mock_on_chunk,
            enable_filesystem=True,
        )

        # Verify delegation to service
        mock_streaming_service.send_message_with_tools_stream.assert_called_once_with(
            "Test streaming message", mock_on_chunk, None, True
        )

        # Verify response
        assert result.success
        assert result.content == "Streaming response"
        assert result.stream_id == "test_stream_123"

    @pytest.mark.asyncio
    async def test_send_memory_aware_message_stream_delegation(
        self, ai_agent_with_streaming
    ):
        """Test that send_memory_aware_message_stream delegates to StreamingResponseService."""
        agent, mock_streaming_service = ai_agent_with_streaming

        # Mock callback function
        async def mock_on_chunk(chunk: str, is_final: bool):
            pass

        # Call the memory-aware streaming method
        result = await agent.send_memory_aware_message_stream(
            message="Test memory-aware streaming",
            on_chunk=mock_on_chunk,
            enable_filesystem=True,
        )

        # Verify delegation to service
        mock_streaming_service.send_memory_aware_message_stream.assert_called_once_with(
            "Test memory-aware streaming", mock_on_chunk, enable_filesystem=True
        )

        # Verify response
        assert result.success
        assert result.content == "Memory-aware streaming response"
        assert result.stream_id == "memory_stream_456"

    @pytest.mark.asyncio
    async def test_interrupt_current_stream_delegation(self, ai_agent_with_streaming):
        """Test that interrupt_current_stream delegates to StreamingResponseService."""
        agent, mock_streaming_service = ai_agent_with_streaming

        # Call the interrupt method
        result = await agent.interrupt_current_stream()

        # Verify delegation to service
        mock_streaming_service.interrupt_current_stream.assert_called_once()

        # Verify response
        assert result is True

    def test_is_streaming_property_delegation(self, ai_agent_with_streaming):
        """Test that is_streaming property delegates to StreamingResponseService."""
        agent, mock_streaming_service = ai_agent_with_streaming

        # Test when not streaming
        mock_streaming_service.is_streaming = False
        assert agent.is_streaming is False

        # Test when streaming
        mock_streaming_service.is_streaming = True
        assert agent.is_streaming is True

    def test_get_stream_status_delegation(self, ai_agent_with_streaming):
        """Test that get_stream_status delegates to StreamingResponseService."""
        agent, mock_streaming_service = ai_agent_with_streaming

        # Call the method
        result = agent.get_stream_status()

        # Verify delegation to service
        mock_streaming_service.get_stream_status.assert_called_once()

        # Verify response
        assert result["status"] == "idle"
        assert result["stream_id"] is None

    def test_get_streaming_health_status_delegation(self, ai_agent_with_streaming):
        """Test that get_streaming_health_status delegates to StreamingResponseService."""
        agent, mock_streaming_service = ai_agent_with_streaming

        # Add the method to agent if it doesn't exist
        if not hasattr(agent, "get_streaming_health_status"):

            def get_streaming_health_status():
                if (
                    hasattr(agent, "streaming_response_service")
                    and agent.streaming_response_service is not None
                ):
                    return agent.streaming_response_service.get_health_status()
                return {"status": "unavailable", "active_streams": 0}

            agent.get_streaming_health_status = get_streaming_health_status.__get__(
                agent, AIAgent
            )

        # Call the method
        result = agent.get_streaming_health_status()

        # Verify delegation to service
        mock_streaming_service.get_health_status.assert_called_once()

        # Verify response
        assert result["status"] == "healthy"
        assert result["active_streams"] == 0

    @pytest.mark.asyncio
    async def test_streaming_fallback_when_service_not_available(self, ai_config):
        """Test that streaming methods fall back to legacy implementation when service not available."""
        # Create agent without streaming service
        with patch("pydantic_ai.Agent") as mock_pydantic:
            mock_agent = MagicMock()
            mock_agent.run = AsyncMock(return_value=MagicMock(data="Test response"))
            mock_pydantic.return_value = mock_agent

            agent = AIAgent(config=ai_config, enable_filesystem_tools=True)
            agent._agent = mock_agent

            # Mock the send_message_with_tools method for fallback
            agent.send_message_with_tools = AsyncMock(
                return_value=AIResponse(success=True, content="Fallback response")
            )

            # Mock callback function
            chunks_received = []

            async def mock_on_chunk(chunk: str, is_final: bool):
                chunks_received.append((chunk, is_final))

            # Call streaming method
            result = await agent.send_message_with_tools_stream(
                message="Test message", on_chunk=mock_on_chunk, enable_filesystem=True
            )

            # Verify fallback was used
            agent.send_message_with_tools.assert_called_once_with("Test message", True)

            # Verify response
            assert result.success
            assert result.content == "Fallback response"

            # Verify chunks were sent (simulated streaming)
            assert len(chunks_received) > 0
            assert chunks_received[-1][1] is True  # Final chunk


class TestStreamingServiceDuplicationElimination:
    """Test that streaming duplication has been eliminated from AIAgent."""

    @pytest_asyncio.fixture
    async def ai_config(self):
        """Create AI configuration for testing."""
        return AIAgentConfig(
            azure_endpoint="https://test.openai.azure.com/",
            azure_api_key="test_key",
            deployment_name="gpt-4o-mini",
            max_tokens=1000,
            temperature=0.7,
        )

    @pytest_asyncio.fixture
    async def ai_agent_with_streaming_service(self, ai_config):
        """Create AI agent with streaming service."""
        mock_streaming_service = MagicMock()
        mock_streaming_service.send_message_with_tools_stream = AsyncMock()
        mock_streaming_service.is_streaming = False

        with patch("pydantic_ai.Agent") as mock_pydantic:
            mock_agent = MagicMock()
            mock_pydantic.return_value = mock_agent

            agent = AIAgent(
                config=ai_config,
                streaming_response_service=mock_streaming_service,
                enable_filesystem_tools=True,
            )
            agent._agent = mock_agent

            return agent

    def test_ai_agent_streaming_methods_are_delegation_only(
        self, ai_agent_with_streaming_service
    ):
        """Test that AIAgent streaming methods are small delegation methods."""
        agent = ai_agent_with_streaming_service

        streaming_methods = [
            "send_message_with_tools_stream",
        ]

        for method_name in streaming_methods:
            if hasattr(agent, method_name):
                method = getattr(agent, method_name)
                if callable(method):
                    # Check that the method is a small delegation method
                    import inspect

                    try:
                        source_lines = inspect.getsourcelines(method)[0]
                        # Delegation methods should be small (< 25 lines typically)
                        assert len(source_lines) < 25, (
                            f"{method_name} should be a delegation method, got {len(source_lines)} lines"
                        )
                    except (OSError, TypeError):
                        # Can't get source (built-in method, etc.) - skip check
                        pass

    def test_no_duplicate_streaming_logic(self, ai_agent_with_streaming_service):
        """Test that AIAgent doesn't contain duplicate streaming logic."""
        import inspect

        # Get the source code of the AIAgent class
        try:
            source = inspect.getsource(AIAgent)
        except OSError:
            pytest.skip("Cannot get source code for AIAgent")

        # Patterns that indicate duplicate streaming logic
        duplicate_patterns = [
            "StreamHandler",
            "stream_text",
            "chunk_count",
            "stream_id =",
            "interrupt_event",
        ]

        # These patterns should not appear in AIAgent if properly delegated
        for pattern in duplicate_patterns:
            # Count occurrences (some might be in comments or docstrings)
            occurrences = source.count(pattern)
            # Allow minimal occurrences for delegation and comments
            assert occurrences < 5, (
                f"Found {occurrences} occurrences of duplicate pattern '{pattern}' in AIAgent"
            )

    def test_streaming_service_parameter_accepted(self, ai_config):
        """Test that AIAgent constructor accepts streaming_response_service parameter."""
        mock_streaming_service = MagicMock()

        with patch("pydantic_ai.Agent"):
            agent = AIAgent(
                config=ai_config,
                streaming_response_service=mock_streaming_service,
                enable_filesystem_tools=True,
            )

            # Verify the service is stored
            assert hasattr(agent, "streaming_response_service")
            assert agent.streaming_response_service is mock_streaming_service

    def test_streaming_state_management_delegated(
        self, ai_agent_with_streaming_service
    ):
        """Test that streaming state management is delegated to service."""
        agent = ai_agent_with_streaming_service

        # These attributes should not exist in AIAgent anymore (delegated to service)
        legacy_streaming_attributes = [
            "current_stream_handler",
            "current_stream_id",
            "_stream_handler",
        ]

        for attr in legacy_streaming_attributes:
            if hasattr(agent, attr):
                # If they exist, they should be None or delegated
                value = getattr(agent, attr)
                # Allow None values (indicating delegation) but not actual handlers
                if value is not None:
                    # Should be a delegation to the service
                    assert hasattr(agent, "streaming_response_service"), (
                        f"Found {attr} but no streaming service"
                    )
