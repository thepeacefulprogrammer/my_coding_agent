"""Test suite for ProjectHistoryService."""

import logging
from unittest.mock import MagicMock

import pytest
from src.my_coding_agent.core.ai_services.project_history_service import (
    ProjectHistoryService,
)


class TestProjectHistoryServiceInitialization:
    """Test ProjectHistoryService initialization."""

    def test_init_with_memory_system_enabled(self):
        """Test initialization with memory system and project history enabled."""
        mock_memory_system = MagicMock()
        service = ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        )

        assert service.memory_system == mock_memory_system
        assert service.enabled is True
        assert service.is_enabled is True
        assert service._project_history_cache == {}
        assert service._project_understanding_cache == {}

    def test_init_with_memory_system_disabled(self):
        """Test initialization with memory system but project history disabled."""
        mock_memory_system = MagicMock()
        service = ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=False
        )

        assert service.memory_system == mock_memory_system
        assert service.enabled is False
        assert service.is_enabled is False

    def test_init_without_memory_system_enabled(self, caplog):
        """Test initialization without memory system but project history enabled."""
        service = ProjectHistoryService(memory_system=None, enable_project_history=True)

        assert service.memory_system is None
        assert service.enabled is False
        assert service.is_enabled is False
        assert "Project history enabled but no memory system provided" in caplog.text

    def test_init_without_memory_system_disabled(self):
        """Test initialization without memory system and project history disabled."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        assert service.memory_system is None
        assert service.enabled is False
        assert service.is_enabled is False


class TestProjectHistoryServiceToolManagement:
    """Test ProjectHistoryService tool management."""

    def test_get_tool_names_enabled(self):
        """Test get_tool_names when service is enabled."""
        mock_memory_system = MagicMock()
        service = ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        )

        tool_names = service.get_tool_names()
        expected_tools = [
            "get_file_project_history",
            "search_project_history",
            "get_recent_project_changes",
            "get_project_timeline",
        ]
        assert tool_names == expected_tools

    def test_get_tool_names_disabled(self):
        """Test get_tool_names when service is disabled."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        tool_names = service.get_tool_names()
        assert tool_names == []

    def test_get_tool_descriptions_enabled(self):
        """Test get_tool_descriptions when service is enabled."""
        mock_memory_system = MagicMock()
        service = ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        )

        descriptions = service.get_tool_descriptions()
        expected_descriptions = {
            "get_file_project_history": "Get project history and evolution for a specific file",
            "search_project_history": "Search project history using semantic and text search",
            "get_recent_project_changes": "Get recent project changes within specified time period",
            "get_project_timeline": "Get project timeline showing chronological development",
        }
        assert descriptions == expected_descriptions

    def test_get_tool_descriptions_disabled(self):
        """Test get_tool_descriptions when service is disabled."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        descriptions = service.get_tool_descriptions()
        assert descriptions == {}


class TestProjectHistoryServiceToolRegistration:
    """Test ProjectHistoryService tool registration."""

    def test_register_tools_enabled(self, caplog):
        """Test tool registration when service is enabled."""
        mock_memory_system = MagicMock()
        mock_agent = MagicMock()

        # Set log level to capture info messages
        with caplog.at_level(
            logging.INFO,
            logger="src.my_coding_agent.core.ai_services.project_history_service",
        ):
            service = ProjectHistoryService(
                memory_system=mock_memory_system, enable_project_history=True
            )

            service.register_tools(mock_agent)

            # Verify that tool_plain was called for each tool
            assert mock_agent.tool_plain.call_count == 4
            assert "Project history tools registered successfully" in caplog.text

    def test_register_tools_disabled(self, caplog):
        """Test tool registration when service is disabled."""
        mock_agent = MagicMock()

        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        service.register_tools(mock_agent)

        # Verify that no tools were registered
        mock_agent.tool_plain.assert_not_called()
        assert "Project history tools require memory system" in caplog.text

    def test_register_tools_error_handling(self, caplog):
        """Test tool registration error handling."""
        mock_memory_system = MagicMock()
        mock_agent = MagicMock()
        mock_agent.tool_plain.side_effect = Exception("Registration failed")

        service = ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        )

        service.register_tools(mock_agent)

        assert service.enabled is False
        assert "Failed to register project history tools" in caplog.text


class TestProjectHistoryServiceToolImplementations:
    """Test ProjectHistoryService tool implementations."""

    @pytest.fixture
    def service_with_memory(self):
        """Create service with mock memory system."""
        mock_memory_system = MagicMock()
        return ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        ), mock_memory_system

    @pytest.mark.asyncio
    async def test_tool_get_file_project_history_success(self, service_with_memory):
        """Test _tool_get_file_project_history with successful response."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.get_project_history_for_file.return_value = [
            {
                "timestamp": 1640995200,  # 2022-01-01 00:00:00
                "event_type": "modification",
                "summary": "Updated function",
                "content": "Added new feature",
            }
        ]

        result = await service._tool_get_file_project_history("test.py", 10)

        assert "Project History for test.py:" in result
        assert "MODIFICATION" in result
        assert "Updated function" in result
        assert "2022-01-01" in result

        # Verify memory system was called correctly
        mock_memory.get_project_history_for_file.assert_called_once_with("test.py", 10)

    @pytest.mark.asyncio
    async def test_tool_get_file_project_history_no_results(self, service_with_memory):
        """Test _tool_get_file_project_history with no results."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.get_project_history_for_file.return_value = []

        result = await service._tool_get_file_project_history("test.py", 10)

        assert "No project history found for file: test.py" in result

    @pytest.mark.asyncio
    async def test_tool_get_file_project_history_caching(self, service_with_memory):
        """Test _tool_get_file_project_history caching behavior."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.get_project_history_for_file.return_value = [
            {"timestamp": 1640995200, "event_type": "modification", "summary": "Test"}
        ]

        # First call
        result1 = await service._tool_get_file_project_history("test.py", 10)

        # Second call should use cache
        result2 = await service._tool_get_file_project_history("test.py", 10)

        assert result1 == result2
        # Memory system should only be called once due to caching
        mock_memory.get_project_history_for_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_tool_get_file_project_history_no_memory_system(self):
        """Test _tool_get_file_project_history without memory system."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        result = await service._tool_get_file_project_history("test.py", 10)

        assert "Error: Memory system not available for project history" in result

    @pytest.mark.asyncio
    async def test_tool_search_project_history_success(self, service_with_memory):
        """Test _tool_search_project_history with successful response."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.search_project_history.return_value = [
            {
                "timestamp": 1640995200,
                "file_path": "test.py",
                "event_type": "modification",
                "summary": "Updated authentication",
            }
        ]

        result = await service._tool_search_project_history("authentication", 25)

        assert "Project History Search Results for 'authentication':" in result
        assert "test.py" in result
        assert "modification" in result
        assert "Updated authentication" in result

        # Verify memory system was called correctly
        mock_memory.search_project_history.assert_called_once_with("authentication", 25)

    @pytest.mark.asyncio
    async def test_tool_search_project_history_no_results(self, service_with_memory):
        """Test _tool_search_project_history with no results."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.search_project_history.return_value = []

        result = await service._tool_search_project_history("nonexistent", 25)

        assert "No project history found matching query: nonexistent" in result

    @pytest.mark.asyncio
    async def test_tool_get_recent_project_changes_success(self, service_with_memory):
        """Test _tool_get_recent_project_changes with successful response."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.get_project_context_for_ai.return_value = "Recent changes context"

        result = await service._tool_get_recent_project_changes(24, 15)

        assert "Recent Project Changes (Last 24 hours):" in result
        assert "Recent changes context" in result

        # Verify memory system was called correctly
        mock_memory.get_project_context_for_ai.assert_called_once_with(
            recent_hours=24, max_events=15
        )

    @pytest.mark.asyncio
    async def test_tool_get_recent_project_changes_no_changes(
        self, service_with_memory
    ):
        """Test _tool_get_recent_project_changes with no changes."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.get_project_context_for_ai.return_value = ""

        result = await service._tool_get_recent_project_changes(24, 15)

        assert "No project changes found in the last 24 hours" in result

    @pytest.mark.asyncio
    async def test_tool_get_project_timeline_file_specific(self, service_with_memory):
        """Test _tool_get_project_timeline for specific file."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.generate_file_timeline.return_value = ["timeline_data"]
        mock_memory.format_timeline_for_ai.return_value = "Formatted timeline"

        result = await service._tool_get_project_timeline("test.py", 7)

        assert "Timeline for test.py (Last 7 days):" in result
        assert "Formatted timeline" in result

        # Verify memory system was called correctly
        mock_memory.generate_file_timeline.assert_called_once_with("test.py", limit=30)
        mock_memory.format_timeline_for_ai.assert_called_once_with(["timeline_data"])

    @pytest.mark.asyncio
    async def test_tool_get_project_timeline_general(self, service_with_memory):
        """Test _tool_get_project_timeline for general project."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.generate_project_timeline.return_value = ["timeline_data"]
        mock_memory.format_timeline_for_ai.return_value = "Formatted timeline"

        result = await service._tool_get_project_timeline("", 7)

        assert "Project Timeline (Last 7 days):" in result
        assert "Formatted timeline" in result

        # Verify memory system was called correctly
        assert mock_memory.generate_project_timeline.called

    @pytest.mark.asyncio
    async def test_tool_get_project_timeline_no_data(self, service_with_memory):
        """Test _tool_get_project_timeline with no timeline data."""
        service, mock_memory = service_with_memory

        # Mock memory system response
        mock_memory.generate_file_timeline.return_value = []

        result = await service._tool_get_project_timeline("test.py", 7)

        assert "No timeline data found for the specified period" in result


class TestProjectHistoryServiceHelperMethods:
    """Test ProjectHistoryService helper methods."""

    @pytest.fixture
    def service_with_memory(self):
        """Create service with mock memory system."""
        mock_memory_system = MagicMock()
        return ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        ), mock_memory_system

    def test_should_lookup_project_history_enabled_with_keywords(
        self, service_with_memory
    ):
        """Test should_lookup_project_history with relevant keywords."""
        service, _ = service_with_memory

        test_messages = [
            "Show me the history of test.py",
            "What changes were made recently?",
            "How was this file modified?",
            "Show the evolution of the code",
            "When was this development done?",
            "What happened to main.js?",
        ]

        for message in test_messages:
            assert service.should_lookup_project_history(message) is True

    def test_should_lookup_project_history_enabled_without_keywords(
        self, service_with_memory
    ):
        """Test should_lookup_project_history without relevant keywords."""
        service, _ = service_with_memory

        test_messages = [
            "Hello there",
            "How are you?",
            "Write a function",
            "Explain this concept",
        ]

        for message in test_messages:
            assert service.should_lookup_project_history(message) is False

    def test_should_lookup_project_history_disabled(self):
        """Test should_lookup_project_history when service is disabled."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        assert service.should_lookup_project_history("Show me the history") is False

    def test_get_recent_project_history_success(self, service_with_memory):
        """Test get_recent_project_history with successful response."""
        service, mock_memory = service_with_memory

        mock_history = [{"event": "test"}]
        mock_memory.get_project_history.return_value = mock_history

        result = service.get_recent_project_history(50)

        assert result == mock_history
        mock_memory.get_project_history.assert_called_once_with(limit=50)

    def test_get_recent_project_history_caching(self, service_with_memory):
        """Test get_recent_project_history caching behavior."""
        service, mock_memory = service_with_memory

        mock_history = [{"event": "test"}]
        mock_memory.get_project_history.return_value = mock_history

        # First call
        result1 = service.get_recent_project_history(50)

        # Second call should use cache
        result2 = service.get_recent_project_history(50)

        assert result1 == result2 == mock_history
        # Memory system should only be called once due to caching
        mock_memory.get_project_history.assert_called_once()

    def test_get_recent_project_history_no_memory_system(self):
        """Test get_recent_project_history without memory system."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        result = service.get_recent_project_history(50)
        assert result == []

    def test_generate_project_evolution_context_file_specific(
        self, service_with_memory
    ):
        """Test generate_project_evolution_context for specific file."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_context_for_ai.return_value = "File context"

        result = service.generate_project_evolution_context("test.py")

        assert result == "File context"
        mock_memory.get_project_context_for_ai.assert_called_once_with(
            file_path="test.py"
        )

    def test_generate_project_evolution_context_general(self, service_with_memory):
        """Test generate_project_evolution_context for general project."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_context_for_ai.return_value = "General context"

        result = service.generate_project_evolution_context("")

        assert result == "General context"
        mock_memory.get_project_context_for_ai.assert_called_once_with(recent_hours=72)

    def test_build_project_understanding_success(self, service_with_memory):
        """Test build_project_understanding with successful response."""
        service, mock_memory = service_with_memory

        mock_history = [
            {
                "event_type": "modification",
                "summary": "improved authentication system",
                "metadata": {"impact_score": 0.8},
            },
            {
                "event_type": "feature_addition",
                "summary": "added user management",
                "metadata": {"impact_score": 0.6},
            },
        ]
        mock_memory.get_project_history.return_value = mock_history

        result = service.build_project_understanding("")

        assert "patterns" in result
        assert "key_changes" in result
        assert "development_focus" in result
        assert "recent_activities" in result

        # Check patterns extraction
        assert "modification" in result["patterns"]
        assert "feature_addition" in result["patterns"]

        # Check key changes (high impact score)
        assert len(result["key_changes"]) == 1  # Only the 0.8 impact score event
        assert result["key_changes"][0]["metadata"]["impact_score"] == 0.8

    def test_build_project_understanding_caching(self, service_with_memory):
        """Test build_project_understanding caching behavior."""
        service, mock_memory = service_with_memory

        mock_history = [{"event_type": "test"}]
        mock_memory.get_project_history.return_value = mock_history

        # First call
        result1 = service.build_project_understanding("")

        # Second call should use cache
        result2 = service.build_project_understanding("")

        assert result1 == result2
        # Memory system should only be called once due to caching
        mock_memory.get_project_history.assert_called_once()

    def test_enhance_message_with_project_context_with_files(self, service_with_memory):
        """Test enhance_message_with_project_context with file paths."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_context_for_ai.return_value = "Context for test.py"

        message = "Show me test.py file history"
        result = service.enhance_message_with_project_context(message)

        assert "Project Context for test.py:" in result
        assert "Context for test.py" in result
        assert message in result

    def test_enhance_message_with_project_context_general(self, service_with_memory):
        """Test enhance_message_with_project_context without specific files."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_context_for_ai.return_value = "General context"

        message = "What recent changes were made?"
        result = service.enhance_message_with_project_context(message)

        assert "Recent Project Context:" in result
        assert "General context" in result
        assert message in result

    def test_enhance_message_with_project_context_disabled(self):
        """Test enhance_message_with_project_context when disabled."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        message = "Show me history"
        result = service.enhance_message_with_project_context(message)

        assert result == message  # Should return original message unchanged

    def test_generate_file_evolution_timeline_success(self, service_with_memory):
        """Test generate_file_evolution_timeline with successful response."""
        service, mock_memory = service_with_memory

        mock_timeline = [{"timestamp": 1640995200}, {"timestamp": 1640908800}]
        mock_memory.generate_file_timeline.return_value = mock_timeline

        result = service.generate_file_evolution_timeline("test.py")

        assert len(result) == 2
        # Should be sorted by timestamp (most recent first)
        assert result[0]["timestamp"] > result[1]["timestamp"]
        mock_memory.generate_file_timeline.assert_called_once_with("test.py", limit=20)

    def test_generate_file_evolution_timeline_no_memory_system(self):
        """Test generate_file_evolution_timeline without memory system."""
        service = ProjectHistoryService(
            memory_system=None, enable_project_history=False
        )

        result = service.generate_file_evolution_timeline("test.py")
        assert result == []

    def test_clear_cache(self, service_with_memory):
        """Test clear_cache functionality."""
        service, _ = service_with_memory

        # Add some cache data
        service._project_history_cache["test"] = "data"
        service._project_understanding_cache["test"] = "data"

        service.clear_cache()

        assert service._project_history_cache == {}
        assert service._project_understanding_cache == {}


class TestProjectHistoryServiceErrorHandling:
    """Test ProjectHistoryService error handling."""

    @pytest.fixture
    def service_with_memory(self):
        """Create service with mock memory system."""
        mock_memory_system = MagicMock()
        return ProjectHistoryService(
            memory_system=mock_memory_system, enable_project_history=True
        ), mock_memory_system

    @pytest.mark.asyncio
    async def test_tool_get_file_project_history_error(
        self, service_with_memory, caplog
    ):
        """Test _tool_get_file_project_history error handling."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_history_for_file.side_effect = Exception("Memory error")

        result = await service._tool_get_file_project_history("test.py", 10)

        assert "Error retrieving project history for test.py" in result
        assert "Memory error" in result
        assert "Error getting file project history" in caplog.text

    @pytest.mark.asyncio
    async def test_tool_search_project_history_error(self, service_with_memory, caplog):
        """Test _tool_search_project_history error handling."""
        service, mock_memory = service_with_memory

        mock_memory.search_project_history.side_effect = Exception("Search error")

        result = await service._tool_search_project_history("query", 25)

        assert "Error searching project history for 'query'" in result
        assert "Search error" in result
        assert "Error searching project history" in caplog.text

    @pytest.mark.asyncio
    async def test_tool_get_recent_project_changes_error(
        self, service_with_memory, caplog
    ):
        """Test _tool_get_recent_project_changes error handling."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_context_for_ai.side_effect = Exception("Context error")

        result = await service._tool_get_recent_project_changes(24, 15)

        assert "Error retrieving recent changes" in result
        assert "Context error" in result
        assert "Error getting recent project changes" in caplog.text

    @pytest.mark.asyncio
    async def test_tool_get_project_timeline_error(self, service_with_memory, caplog):
        """Test _tool_get_project_timeline error handling."""
        service, mock_memory = service_with_memory

        mock_memory.generate_file_timeline.side_effect = Exception("Timeline error")

        result = await service._tool_get_project_timeline("test.py", 7)

        assert "Error generating project timeline" in result
        assert "Timeline error" in result
        assert "Error getting project timeline" in caplog.text

    def test_get_recent_project_history_error(self, service_with_memory, caplog):
        """Test get_recent_project_history error handling."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_history.side_effect = Exception("History error")

        result = service.get_recent_project_history(50)

        assert result == []
        assert "Error getting recent project history" in caplog.text

    def test_generate_project_evolution_context_error(
        self, service_with_memory, caplog
    ):
        """Test generate_project_evolution_context error handling."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_context_for_ai.side_effect = Exception("Context error")

        result = service.generate_project_evolution_context("test.py")

        assert result == ""
        assert "Error generating project evolution context" in caplog.text

    def test_build_project_understanding_error(self, service_with_memory, caplog):
        """Test build_project_understanding error handling."""
        service, mock_memory = service_with_memory

        mock_memory.get_project_history.side_effect = Exception("Understanding error")

        result = service.build_project_understanding("")

        assert result == {}
        assert "Error building project understanding" in caplog.text

    def test_enhance_message_with_project_context_error(
        self, service_with_memory, caplog
    ):
        """Test enhance_message_with_project_context error handling."""
        service, mock_memory = service_with_memory

        # Mock to throw error when generating context
        service.generate_project_evolution_context = MagicMock(
            side_effect=Exception("Context error")
        )

        message = "Show me test.py history"
        result = service.enhance_message_with_project_context(message)

        assert result == message  # Should return original message on error
        assert "Error enhancing message with project context" in caplog.text

    def test_generate_file_evolution_timeline_error(self, service_with_memory, caplog):
        """Test generate_file_evolution_timeline error handling."""
        service, mock_memory = service_with_memory

        mock_memory.generate_file_timeline.side_effect = Exception("Timeline error")

        result = service.generate_file_evolution_timeline("test.py")

        assert result == []
        assert "Error generating file evolution timeline" in caplog.text
