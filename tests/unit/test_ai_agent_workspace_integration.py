"""
Tests for AIAgent WorkspaceService integration.

This module tests the integration between AIAgent and WorkspaceService,
ensuring that ai_agent.py delegates file operations instead of duplicating code.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from src.my_coding_agent.core.ai_agent import AIAgent
from src.my_coding_agent.core.ai_services.configuration_service import (
    ConfigurationService,
)
from src.my_coding_agent.core.ai_services.error_handling_service import (
    ErrorHandlingService,
)
from src.my_coding_agent.core.ai_services.workspace_service import WorkspaceService


class TestAIAgentWorkspaceServiceIntegration:
    """Test AIAgent integration with WorkspaceService."""

    @pytest.fixture
    def mock_workspace_service(self):
        """Create a mock WorkspaceService."""
        return Mock(spec=WorkspaceService)

    @pytest.fixture
    def mock_config_service(self):
        """Create a mock ConfigurationService."""
        config_service = Mock(spec=ConfigurationService)
        config_service.azure_endpoint = "https://test.openai.azure.com/"
        config_service.api_version = "2024-02-15-preview"
        config_service.azure_api_key = "test-key"
        config_service.deployment_name = "test-deployment"
        config_service.max_retries = 3
        config_service.request_timeout = 30
        config_service.max_tokens = 4000
        config_service.temperature = 0.7
        return config_service

    @pytest.fixture
    def mock_error_service(self):
        """Create a mock ErrorHandlingService."""
        return Mock(spec=ErrorHandlingService)

    @pytest.fixture
    def agent_with_workspace_service(
        self, mock_config_service, mock_error_service, mock_workspace_service
    ):
        """Create an AIAgent with WorkspaceService dependency injection."""
        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            agent = AIAgent(
                config_service=mock_config_service,
                error_service=mock_error_service,
                workspace_service=mock_workspace_service,
            )

        return agent, mock_workspace_service

    def test_read_workspace_file_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that read_workspace_file delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock response
        mock_workspace_service.read_workspace_file.return_value = "file content"

        # Call method
        result = agent.read_workspace_file("test.py")

        # Verify delegation
        mock_workspace_service.read_workspace_file.assert_called_once_with("test.py")
        assert result == "file content"

    def test_write_workspace_file_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that write_workspace_file delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        agent.write_workspace_file("test.py", "new content")

        # Verify delegation
        mock_workspace_service.write_workspace_file.assert_called_once_with(
            "test.py", "new content"
        )

    def test_list_workspace_directory_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that list_workspace_directory delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock response
        mock_workspace_service.list_workspace_directory.return_value = [
            "file1.py",
            "file2.py",
        ]

        # Call method
        result = agent.list_workspace_directory("src/")

        # Verify delegation
        mock_workspace_service.list_workspace_directory.assert_called_once_with("src/")
        assert result == ["file1.py", "file2.py"]

    def test_create_workspace_directory_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that create_workspace_directory delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        agent.create_workspace_directory("new_dir")

        # Verify delegation
        mock_workspace_service.create_workspace_directory.assert_called_once_with(
            "new_dir"
        )

    def test_delete_workspace_file_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that delete_workspace_file delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        agent.delete_workspace_file("test.py")

        # Verify delegation
        mock_workspace_service.delete_workspace_file.assert_called_once_with("test.py")

    def test_workspace_file_exists_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that workspace_file_exists delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock response
        mock_workspace_service.workspace_file_exists.return_value = True

        # Call method
        result = agent.workspace_file_exists("test.py")

        # Verify delegation
        mock_workspace_service.workspace_file_exists.assert_called_once_with("test.py")
        assert result is True

    def test_set_workspace_root_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that set_workspace_root delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        test_path = Path("/test/workspace")
        agent.set_workspace_root(test_path)

        # Verify delegation
        mock_workspace_service.set_workspace_root.assert_called_once_with(test_path)

    def test_resolve_workspace_path_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that resolve_workspace_path delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock response
        expected_path = Path("/workspace/test.py")
        mock_workspace_service.resolve_workspace_path.return_value = expected_path

        # Call method
        result = agent.resolve_workspace_path("test.py")

        # Verify delegation
        mock_workspace_service.resolve_workspace_path.assert_called_once_with("test.py")
        assert result == expected_path

    def test_validate_file_path_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that validate_file_path delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        agent.validate_file_path("test.py")

        # Verify delegation
        mock_workspace_service.validate_file_path.assert_called_once_with("test.py")

    def test_validate_file_content_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that validate_file_content delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        agent.validate_file_content("test content")

        # Verify delegation
        mock_workspace_service.validate_file_content.assert_called_once_with(
            "test content"
        )

    def test_validate_directory_path_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that validate_directory_path delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Call method
        agent.validate_directory_path("test_dir")

        # Verify delegation
        mock_workspace_service.validate_directory_path.assert_called_once_with(
            "test_dir"
        )

    def test_read_workspace_file_validated_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that read_workspace_file_validated delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock response
        mock_workspace_service.read_workspace_file_validated.return_value = (
            "validated content"
        )

        # Call method
        result = agent.read_workspace_file_validated("test.py")

        # Verify delegation
        mock_workspace_service.read_workspace_file_validated.assert_called_once_with(
            "test.py"
        )
        assert result == "validated content"

    def test_read_multiple_files_delegates_to_service(
        self, agent_with_workspace_service
    ):
        """Test that read_multiple_files delegates to WorkspaceService."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock response
        expected_result = {"file1.py": "content1", "file2.py": "content2"}
        mock_workspace_service.read_multiple_workspace_files.return_value = (
            expected_result
        )

        # Call method
        result = agent.read_multiple_files(["file1.py", "file2.py"])

        # Verify delegation (with default fail_fast=False parameter)
        mock_workspace_service.read_multiple_workspace_files.assert_called_once_with(
            ["file1.py", "file2.py"], False
        )
        assert result == expected_result

    def test_backward_compatibility_without_workspace_service(
        self, mock_config_service, mock_error_service
    ):
        """Test that AIAgent works without WorkspaceService (backwards compatibility)."""
        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            # Create agent without workspace service (legacy mode)
            agent = AIAgent(
                config_service=mock_config_service, error_service=mock_error_service
            )

        # Agent should have workspace_service as None
        assert agent.workspace_service is None

        # Legacy file operations should still work (using internal implementations)
        # This tests backwards compatibility
        assert hasattr(agent, "read_workspace_file")
        assert hasattr(agent, "write_workspace_file")

    def test_service_vs_legacy_mode_detection(
        self, agent_with_workspace_service, mock_config_service, mock_error_service
    ):
        """Test that agent correctly detects service vs legacy mode."""
        # Service mode agent
        agent_service, mock_workspace_service = agent_with_workspace_service
        assert agent_service.workspace_service is not None

        # Legacy mode agent
        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            agent_legacy = AIAgent(
                config_service=mock_config_service, error_service=mock_error_service
            )

        assert agent_legacy.workspace_service is None

    def test_workspace_service_error_handling(self, agent_with_workspace_service):
        """Test that workspace service errors are properly handled."""
        agent, mock_workspace_service = agent_with_workspace_service

        # Configure mock to raise an exception
        mock_workspace_service.read_workspace_file.side_effect = FileNotFoundError(
            "File not found"
        )

        # The error should propagate (agent doesn't handle it, service does)
        with pytest.raises(FileNotFoundError, match="File not found"):
            agent.read_workspace_file("nonexistent.py")

    def test_workspace_service_initialization_in_constructor(
        self, mock_config_service, mock_error_service
    ):
        """Test that workspace service is properly initialized in constructor."""
        mock_workspace_service = Mock(spec=WorkspaceService)

        with (
            patch("src.my_coding_agent.core.ai_agent.OpenAIModel"),
            patch("src.my_coding_agent.core.ai_agent.Agent"),
        ):
            agent = AIAgent(
                config_service=mock_config_service,
                error_service=mock_error_service,
                workspace_service=mock_workspace_service,
            )

        # Verify service is stored
        assert agent.workspace_service is mock_workspace_service

        # Verify service is ready to use
        agent.workspace_service.read_workspace_file("test.py")
        mock_workspace_service.read_workspace_file.assert_called_once_with("test.py")


class TestWorkspaceServiceDuplicationElimination:
    """Test that duplicate workspace functionality has been eliminated."""

    def test_ai_agent_file_methods_are_delegation_only(self):
        """Test that AIAgent file methods are thin delegation wrappers."""
        import inspect

        from src.my_coding_agent.core.ai_agent import AIAgent

        # List of methods that should delegate to WorkspaceService
        delegation_methods = [
            "read_workspace_file",
            "write_workspace_file",
            "list_workspace_directory",
            "create_workspace_directory",
            "delete_workspace_file",
            "workspace_file_exists",
            "set_workspace_root",
            "resolve_workspace_path",
            "validate_file_path",
            "validate_file_content",
            "validate_directory_path",
            "read_workspace_file_validated",
        ]

        for method_name in delegation_methods:
            if hasattr(AIAgent, method_name):
                method = getattr(AIAgent, method_name)

                # Method should exist and be callable
                assert callable(method), f"{method_name} should be callable"

                # For delegation methods, we expect them to be small
                # (just service calls, not large implementations)
                if inspect.ismethod(method) or inspect.isfunction(method):
                    try:
                        source_lines = inspect.getsourcelines(method)[0]
                        # Delegation methods should be small (< 10 lines typically)
                        assert len(source_lines) < 20, (
                            f"{method_name} should be a small delegation method, got {len(source_lines)} lines"
                        )
                    except OSError:
                        # Can't get source (built-in or C extension), that's fine
                        pass

    def test_no_duplicate_file_validation_logic(self):
        """Test that AIAgent doesn't contain duplicate file validation logic."""
        import inspect

        from src.my_coding_agent.core.ai_agent import AIAgent

        # Get AIAgent source code
        try:
            source = inspect.getsource(AIAgent)

            # Check for duplicate validation patterns that should be in WorkspaceService
            duplicate_patterns = [
                "# Validate file path",
                "if not file_path",
                "if '..' in file_path",
                "DANGEROUS_EXTENSIONS",
                "MAX_FILE_SIZE",
                "file size exceeds",
            ]

            # These patterns should not appear in AIAgent if properly delegated
            for pattern in duplicate_patterns:
                # Count occurrences (some might be in comments or docstrings)
                occurrences = source.count(pattern)
                # Allow minimal occurrences (comments, docstrings) but not implementation
                assert occurrences < 3, (
                    f"Found {occurrences} occurrences of duplicate pattern '{pattern}' in AIAgent"
                )

        except OSError:
            # Can't get source code, skip this test
            pytest.skip("Cannot inspect AIAgent source code")

    def test_workspace_service_integration_coverage(self):
        """Test that all major WorkspaceService methods have AIAgent integration."""
        from src.my_coding_agent.core.ai_agent import AIAgent
        from src.my_coding_agent.core.ai_services.workspace_service import (
            WorkspaceService,
        )

        # Core WorkspaceService methods that should have AIAgent delegation
        core_methods = [
            "read_workspace_file",
            "write_workspace_file",
            "list_workspace_directory",
            "create_workspace_directory",
            "delete_workspace_file",
            "workspace_file_exists",
        ]

        for method_name in core_methods:
            # WorkspaceService should have the method
            assert hasattr(WorkspaceService, method_name), (
                f"WorkspaceService missing {method_name}"
            )

            # AIAgent should have corresponding delegation method
            assert hasattr(AIAgent, method_name), (
                f"AIAgent missing delegation for {method_name}"
            )
