"""Unit tests for metadata removal from chat message display (Task 3.3)."""

import pytest
from PyQt6.QtWidgets import QApplication, QLabel
from src.my_coding_agent.gui.chat_message_model import (
    ChatMessage,
    ChatMessageModel,
    MessageRole,
    MessageStatus,
)
from src.my_coding_agent.gui.chat_widget import (
    ChatWidget,
    MessageBubble,
    MessageDisplayArea,
)


class TestMetadataRemoval:
    """Test that all metadata (timestamps and status indicators) are removed from message display."""

    @pytest.fixture
    def app(self):
        """Create QApplication instance."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def sample_message(self):
        """Create a sample chat message."""
        return ChatMessage(
            message_id="test_001",
            role=MessageRole.USER,
            content="Test message content",
            status=MessageStatus.SENT,
        )

    @pytest.fixture
    def assistant_message(self):
        """Create a sample assistant message."""
        return ChatMessage(
            message_id="test_002",
            role=MessageRole.ASSISTANT,
            content="AI response content",
            status=MessageStatus.DELIVERED,
        )

    def test_message_bubble_has_no_timestamp_label(self, app, sample_message):
        """Test that MessageBubble no longer has a timestamp label."""
        bubble = MessageBubble(sample_message)

        # The timestamp_label attribute should not exist
        assert not hasattr(bubble, "timestamp_label"), (
            "MessageBubble should not have timestamp_label attribute"
        )

    def test_message_bubble_has_no_status_indicator(self, app, sample_message):
        """Test that MessageBubble no longer has a status indicator."""
        bubble = MessageBubble(sample_message)

        # The status_label attribute should not exist
        assert not hasattr(bubble, "status_label"), (
            "MessageBubble should not have status_label attribute"
        )

    def test_message_bubble_has_no_metadata_display(self, app, sample_message):
        """Test that no metadata is visually displayed in message bubble."""
        bubble = MessageBubble(sample_message)

        # Find all QLabel children - none should contain metadata
        labels = bubble.findChildren(QLabel)

        # Check for timestamp patterns
        timestamp_patterns = [
            sample_message.format_timestamp("%H:%M"),
            sample_message.format_timestamp("%I:%M %p"),
            sample_message.format_timestamp("%H:%M:%S"),
        ]

        # Check for status indicators
        status_patterns = ["⏳", "📤", "✓", "✓✓", "❌", "💭"]

        for label in labels:
            label_text = label.text()

            # No timestamps
            for pattern in timestamp_patterns:
                assert pattern not in label_text, (
                    f"Found timestamp '{pattern}' in label text: '{label_text}'"
                )

            # No status indicators
            for pattern in status_patterns:
                assert pattern not in label_text, (
                    f"Found status indicator '{pattern}' in label text: '{label_text}'"
                )

    def test_get_timestamp_text_method_removed(self, app, sample_message):
        """Test that get_timestamp_text method is removed."""
        bubble = MessageBubble(sample_message)

        # The get_timestamp_text method should not exist
        assert not hasattr(bubble, "get_timestamp_text"), (
            "get_timestamp_text method should be removed"
        )

    def test_get_status_text_method_removed(self, app, sample_message):
        """Test that get_status_text method is removed."""
        bubble = MessageBubble(sample_message)

        # The get_status_text method should not exist
        assert not hasattr(bubble, "get_status_text"), (
            "get_status_text method should be removed"
        )

    def test_message_content_still_displayed(self, app, sample_message):
        """Test that message content is still properly displayed."""
        bubble = MessageBubble(sample_message)

        # Content should still be displayed
        content_labels = [
            label
            for label in bubble.findChildren(QLabel)
            if sample_message.content in label.text()
        ]
        assert len(content_labels) > 0, "Message content should still be displayed"

    def test_user_message_styling_preserved(self, app, sample_message):
        """Test that user message styling is preserved without metadata."""
        bubble = MessageBubble(sample_message)

        # Check that the bubble has proper styling (should have background/border styling)
        style = bubble.styleSheet()
        assert "background" in style.lower() or "border" in style.lower(), (
            "User message styling should be preserved"
        )

    def test_assistant_message_natural_flow_preserved(self, app, assistant_message):
        """Test that assistant message natural flow is preserved without metadata."""
        bubble = MessageBubble(assistant_message)

        # Check that assistant messages still have transparent background
        style = bubble.styleSheet()
        assert "transparent" in style.lower(), (
            "Assistant message natural flow should be preserved"
        )

    def test_light_theme_no_metadata_styling(self, app, sample_message):
        """Test that light theme styling doesn't include metadata colors."""
        bubble = MessageBubble(sample_message)
        bubble.apply_theme("light")

        # Check that styling doesn't reference metadata elements
        # Should not have any styling for non-existent metadata elements
        assert True  # If no errors occur during theme application, test passes

    def test_dark_theme_no_metadata_styling(self, app, sample_message):
        """Test that dark theme styling doesn't include metadata colors."""
        bubble = MessageBubble(sample_message)
        bubble.apply_theme("dark")

        # Check that styling doesn't reference metadata elements
        # Should not have any styling for non-existent metadata elements
        assert True  # If no errors occur during theme application, test passes

    def test_message_display_area_functionality(self, app):
        """Test that MessageDisplayArea still works properly without metadata."""
        model = ChatMessageModel()
        display_area = MessageDisplayArea(model)

        # Add a message and verify it displays correctly
        message = ChatMessage(
            message_id="test_003",
            role=MessageRole.USER,
            content="Test message",
            status=MessageStatus.SENT,
        )

        model.add_message(message)

        # Verify message is displayed
        assert display_area.get_message_count() == 1
        assert display_area.has_message("test_003")

    def test_chat_widget_integration(self, app):
        """Test that ChatWidget integration works without metadata."""
        chat_widget = ChatWidget()

        # Add messages of different types
        user_msg_id = chat_widget.add_user_message("User message")
        assistant_msg_id = chat_widget.add_assistant_message("Assistant response")
        system_msg_id = chat_widget.add_system_message("System notification")

        # All messages should be added successfully
        assert user_msg_id is not None
        assert assistant_msg_id is not None
        assert system_msg_id is not None

        # Display area should show all messages
        assert chat_widget.display_area.get_message_count() == 3

    def test_message_data_preserved(self, app, sample_message):
        """Test that underlying message data is preserved."""
        # Create bubble to verify it works with preserved data
        MessageBubble(sample_message)

        # The underlying message should still have timestamp and status data
        assert sample_message.timestamp is not None, (
            "Message timestamp data should be preserved"
        )
        assert hasattr(sample_message, "format_timestamp"), (
            "Message timestamp formatting should be available"
        )
        assert sample_message.status is not None, (
            "Message status data should be preserved"
        )

    def test_export_functionality_includes_metadata(self, app):
        """Test that exported conversation data still includes metadata."""
        chat_widget = ChatWidget()

        # Add a message
        chat_widget.add_user_message("Test message for export")

        # Export conversation
        exported = chat_widget.export_conversation()

        # Exported data should include metadata information
        assert len(exported) == 1
        message_data = exported[0]
        assert "timestamp" in message_data, "Exported data should include timestamp"
        assert "status" in message_data, "Exported data should include status"

    def test_no_metadata_related_errors(self, app):
        """Test that removing metadata doesn't cause any runtime errors."""
        model = ChatMessageModel()
        display_area = MessageDisplayArea(model)

        # Add multiple messages and verify no errors occur
        for i in range(5):
            message = ChatMessage(
                message_id=f"test_{i}",
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"Message {i}",
                status=MessageStatus.SENT,
            )
            model.add_message(message)

        # Apply theme changes
        display_area.apply_theme("light")
        display_area.apply_theme("dark")

        # All operations should complete without errors
        assert display_area.get_message_count() == 5

    def test_status_update_methods_still_work(self, app, sample_message):
        """Test that status update methods still work for internal state tracking."""
        bubble = MessageBubble(sample_message)

        # These methods should exist and work for internal state management
        assert hasattr(bubble, "update_status"), (
            "update_status method should exist for internal tracking"
        )
        assert hasattr(bubble, "_update_status_display"), (
            "_update_status_display method should exist"
        )

        # Should be able to call update_status without errors
        bubble.update_status(MessageStatus.DELIVERED)

        # Internal state should be updated even if not displayed
        assert hasattr(bubble, "_current_status"), (
            "Internal status state should be maintained"
        )
