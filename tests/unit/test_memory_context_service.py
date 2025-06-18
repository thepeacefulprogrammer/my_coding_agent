"""Tests for the Memory Context Service."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.my_coding_agent.core.ai_services.memory_context_service import (
    MemoryContextService,
)


class TestMemoryContextService:
    """Test cases for MemoryContextService."""

    @pytest.fixture
    def mock_memory_system(self):
        """Mock memory system for testing."""
        memory = MagicMock()
        memory.store_user_message = MagicMock(return_value="user_msg_123")
        memory.store_assistant_message = MagicMock(return_value="assistant_msg_123")
        memory.store_long_term_memory = MagicMock(return_value="memory_123")
        memory.get_conversation_context = MagicMock(return_value=[])
        memory.get_long_term_memories = MagicMock(return_value=[])
        memory.get_memory_stats = MagicMock(return_value={"total_messages": 10})
        memory.clear_all_memory_data = AsyncMock(return_value=True)
        memory.start_new_session = MagicMock(return_value="session_123")
        memory.current_session_id = "current_session_123"
        memory.load_conversation_history = MagicMock()
        memory.get_project_context_for_ai = MagicMock(return_value="Project context")
        memory.close = AsyncMock()
        return memory

    @pytest.fixture
    def memory_disabled_service(self):
        """Create a MemoryContextService with memory disabled."""
        return MemoryContextService(enable_memory_awareness=False)

    @pytest.fixture
    def memory_enabled_service(self, mock_memory_system):
        """Create a MemoryContextService with memory enabled."""
        with patch(
            "src.my_coding_agent.core.memory_integration.ConversationMemoryHandler"
        ) as mock_handler_class:
            mock_handler_class.return_value = mock_memory_system
            service = MemoryContextService(enable_memory_awareness=True)
            service._memory_system = mock_memory_system  # Ensure it's set for tests
            return service

    def test_initialization_memory_disabled(self, memory_disabled_service):
        """Test service initialization with memory disabled."""
        assert not memory_disabled_service.memory_aware_enabled
        assert memory_disabled_service.memory_system is None

    @patch("src.my_coding_agent.core.memory_integration.ConversationMemoryHandler")
    def test_initialization_memory_enabled_success(
        self, mock_handler_class, mock_memory_system
    ):
        """Test successful service initialization with memory enabled."""
        mock_handler_class.return_value = mock_memory_system

        service = MemoryContextService(enable_memory_awareness=True)

        assert service.memory_aware_enabled
        assert service.memory_system == mock_memory_system
        mock_handler_class.assert_called_once_with(None)

    @patch("src.my_coding_agent.core.memory_integration.ConversationMemoryHandler")
    def test_initialization_memory_enabled_with_path(
        self, mock_handler_class, mock_memory_system
    ):
        """Test service initialization with custom memory path."""
        mock_handler_class.return_value = mock_memory_system
        custom_path = Path("/custom/memory/path")

        service = MemoryContextService(
            enable_memory_awareness=True, memory_db_path=custom_path
        )

        assert service.memory_aware_enabled
        mock_handler_class.assert_called_once_with(custom_path)

    @patch("src.my_coding_agent.core.memory_integration.ConversationMemoryHandler")
    def test_initialization_memory_enabled_failure(self, mock_handler_class):
        """Test service initialization when memory system fails to initialize."""
        mock_handler_class.side_effect = Exception("Memory init failed")

        service = MemoryContextService(enable_memory_awareness=True)

        assert not service.memory_aware_enabled
        assert service.memory_system is None

    def test_store_user_message_memory_disabled(self, memory_disabled_service):
        """Test storing user message when memory is disabled."""
        result = memory_disabled_service.store_user_message("test message")
        assert result is None

    def test_store_user_message_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test storing user message when memory is enabled."""
        result = memory_enabled_service.store_user_message(
            "test message", {"key": "value"}
        )

        assert result == "user_msg_123"
        mock_memory_system.store_user_message.assert_called_once_with(
            "test message", {"key": "value"}
        )

    def test_store_user_message_error_handling(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test error handling when storing user message fails."""
        mock_memory_system.store_user_message.side_effect = Exception("Store failed")

        result = memory_enabled_service.store_user_message("test message")
        assert result is None

    def test_store_assistant_message_memory_disabled(self, memory_disabled_service):
        """Test storing assistant message when memory is disabled."""
        result = memory_disabled_service.store_assistant_message("test response")
        assert result is None

    def test_store_assistant_message_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test storing assistant message when memory is enabled."""
        result = memory_enabled_service.store_assistant_message("test response")

        assert result == "assistant_msg_123"
        mock_memory_system.store_assistant_message.assert_called_once_with(
            "test response", None
        )

    def test_store_long_term_memory_memory_disabled(self, memory_disabled_service):
        """Test storing long-term memory when memory is disabled."""
        result = memory_disabled_service.store_long_term_memory("important fact")
        assert result is None

    def test_store_long_term_memory_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test storing long-term memory when memory is enabled."""
        result = memory_enabled_service.store_long_term_memory(
            "important fact", "user_info", 0.9
        )

        assert result == "memory_123"
        mock_memory_system.store_long_term_memory.assert_called_once_with(
            "important fact", "user_info", 0.9
        )

    def test_get_conversation_context_memory_disabled(self, memory_disabled_service):
        """Test getting conversation context when memory is disabled."""
        result = memory_disabled_service.get_conversation_context()
        assert result == []

    def test_get_conversation_context_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test getting conversation context when memory is enabled."""
        expected_context = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        mock_memory_system.get_conversation_context.return_value = expected_context

        result = memory_enabled_service.get_conversation_context(limit=25)

        assert result == expected_context
        mock_memory_system.get_conversation_context.assert_called_once_with(25)

    def test_get_long_term_memories_memory_disabled(self, memory_disabled_service):
        """Test getting long-term memories when memory is disabled."""
        result = memory_disabled_service.get_long_term_memories("query")
        assert result == []

    def test_get_long_term_memories_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test getting long-term memories when memory is enabled."""
        expected_memories = [
            {
                "content": "User likes Python",
                "memory_type": "preference",
                "importance_score": 0.8,
            }
        ]
        mock_memory_system.get_long_term_memories.return_value = expected_memories

        result = memory_enabled_service.get_long_term_memories("preferences", 5)

        assert result == expected_memories
        mock_memory_system.get_long_term_memories.assert_called_once_with(
            "preferences", 5
        )

    def test_enhance_message_with_memory_context_memory_disabled(
        self, memory_disabled_service
    ):
        """Test message enhancement when memory is disabled."""
        original_message = "What is Python?"
        result = memory_disabled_service.enhance_message_with_memory_context(
            original_message
        )
        assert result == original_message

    def test_enhance_message_with_memory_context_no_context(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test message enhancement when no memory context is available."""
        mock_memory_system.get_conversation_context.return_value = []
        mock_memory_system.get_long_term_memories.return_value = []

        original_message = "What is Python?"
        result = memory_enabled_service.enhance_message_with_memory_context(
            original_message
        )
        assert result == original_message

    def test_enhance_message_with_memory_context_with_context(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test message enhancement with available memory context."""
        mock_memory_system.get_conversation_context.return_value = [
            {"role": "user", "content": "I'm learning Python"},
            {"role": "assistant", "content": "Great choice!"},
        ]
        mock_memory_system.get_long_term_memories.return_value = [
            {
                "content": "User is a beginner",
                "memory_type": "user_info",
                "importance_score": 0.8,
            }
        ]

        original_message = "What should I learn next?"
        result = memory_enabled_service.enhance_message_with_memory_context(
            original_message
        )

        assert "MEMORY CONTEXT" in result
        assert "LONG-TERM MEMORY" in result
        assert "CONVERSATION HISTORY" in result
        assert "CURRENT USER MESSAGE" in result
        assert original_message in result

    def test_enhance_message_with_long_term_memory_trigger(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test that certain phrases trigger long-term memory storage."""
        message = "My name is John, remember that"
        memory_enabled_service.enhance_message_with_memory_context(message)

        mock_memory_system.store_long_term_memory.assert_called_once_with(
            message, "user_info", 0.9
        )

    def test_get_memory_statistics_memory_disabled(self, memory_disabled_service):
        """Test getting memory statistics when memory is disabled."""
        result = memory_disabled_service.get_memory_statistics()

        expected = {"memory_enabled": False, "error": "Memory system not enabled"}
        assert result == expected

    def test_get_memory_statistics_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test getting memory statistics when memory is enabled."""
        expected_stats = {"total_messages": 10, "memory_enabled": True}

        result = memory_enabled_service.get_memory_statistics()
        assert result == expected_stats

    def test_get_memory_statistics_error_handling(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test error handling when getting memory statistics fails."""
        mock_memory_system.get_memory_stats.side_effect = Exception("Stats failed")

        result = memory_enabled_service.get_memory_statistics()
        assert result["memory_enabled"] is True
        assert "error" in result

    @pytest.mark.asyncio
    async def test_clear_all_memory_memory_disabled(self, memory_disabled_service):
        """Test clearing memory when memory is disabled."""
        result = await memory_disabled_service.clear_all_memory()
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_all_memory_memory_enabled_success(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test successful memory clearing when memory is enabled."""
        result = await memory_enabled_service.clear_all_memory()

        assert result is True
        mock_memory_system.clear_all_memory_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_clear_all_memory_memory_enabled_failure(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test memory clearing failure when memory is enabled."""
        mock_memory_system.clear_all_memory_data.return_value = False

        result = await memory_enabled_service.clear_all_memory()
        assert result is False

    def test_start_new_session_memory_disabled(self, memory_disabled_service):
        """Test starting new session when memory is disabled."""
        result = memory_disabled_service.start_new_session()
        assert result is None

    def test_start_new_session_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test starting new session when memory is enabled."""
        result = memory_enabled_service.start_new_session()

        assert result == "session_123"
        mock_memory_system.start_new_session.assert_called_once()

    def test_get_current_session_id_memory_disabled(self, memory_disabled_service):
        """Test getting current session ID when memory is disabled."""
        result = memory_disabled_service.get_current_session_id()
        assert result is None

    def test_get_current_session_id_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test getting current session ID when memory is enabled."""
        result = memory_enabled_service.get_current_session_id()
        assert result == "current_session_123"

    def test_load_conversation_history_memory_disabled(self, memory_disabled_service):
        """Test loading conversation history when memory is disabled."""
        mock_chat_widget = MagicMock()
        result = memory_disabled_service.load_conversation_history(mock_chat_widget)
        assert result is False

    def test_load_conversation_history_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test loading conversation history when memory is enabled."""
        mock_chat_widget = MagicMock()
        result = memory_enabled_service.load_conversation_history(mock_chat_widget)

        assert result is True
        mock_memory_system.load_conversation_history.assert_called_once_with(
            mock_chat_widget
        )

    def test_get_project_context_for_ai_memory_disabled(self, memory_disabled_service):
        """Test getting project context when memory is disabled."""
        result = memory_disabled_service.get_project_context_for_ai()
        assert result == ""

    def test_get_project_context_for_ai_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test getting project context when memory is enabled."""
        result = memory_enabled_service.get_project_context_for_ai("test.py", 48, 20)

        assert result == "Project context"
        mock_memory_system.get_project_context_for_ai.assert_called_once_with(
            "test.py", 48, 20
        )

    @pytest.mark.asyncio
    async def test_close_memory_disabled(self, memory_disabled_service):
        """Test closing service when memory is disabled."""
        # Should not raise any exceptions
        await memory_disabled_service.close()

    @pytest.mark.asyncio
    async def test_close_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test closing service when memory is enabled."""
        await memory_enabled_service.close()
        mock_memory_system.close.assert_called_once()

    def test_get_health_status_memory_disabled(self, memory_disabled_service):
        """Test health status when memory is disabled."""
        status = memory_disabled_service.get_health_status()

        expected_keys = {
            "service_name",
            "memory_enabled",
            "memory_system_initialized",
            "current_session_id",
            "is_healthy",
        }
        assert set(status.keys()) == expected_keys
        assert status["service_name"] == "MemoryContextService"
        assert not status["memory_enabled"]
        assert not status["memory_system_initialized"]
        assert status["current_session_id"] is None
        assert status["is_healthy"]

    def test_get_health_status_memory_enabled(
        self, memory_enabled_service, mock_memory_system
    ):
        """Test health status when memory is enabled."""
        status = memory_enabled_service.get_health_status()

        assert status["service_name"] == "MemoryContextService"
        assert status["memory_enabled"]
        assert status["memory_system_initialized"]
        assert status["current_session_id"] == "current_session_123"
        assert status["is_healthy"]
