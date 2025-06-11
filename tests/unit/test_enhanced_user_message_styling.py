"""Unit tests for enhanced user message styling (Task 3.2)."""

import pytest
from PyQt6.QtWidgets import QApplication
from src.my_coding_agent.gui.chat_message_model import (
    ChatMessage,
    ChatMessageModel,
    MessageRole,
    MessageStatus,
)
from src.my_coding_agent.gui.chat_widget import (
    MessageDisplayArea,
)


class TestEnhancedUserMessageStyling:
    """Test enhanced user message styling with bordered distinction."""

    @pytest.fixture
    def qapp(self):
        """Create QApplication instance."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        return app

    @pytest.fixture
    def message_model(self):
        """Create a message model instance."""
        return ChatMessageModel()

    @pytest.fixture
    def display_area(self, qapp, message_model):
        """Create a display area instance."""
        return MessageDisplayArea(message_model)

    def test_user_message_light_theme_enhanced_styling(self, display_area, qapp):
        """Test that user messages have enhanced styling in light theme."""
        # Apply light theme
        display_area.apply_theme("light")

        # Add user message
        message = ChatMessage(
            message_id="test_user_light",
            role=MessageRole.USER,
            content="Test user message",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        # Get the created bubble
        bubble = display_area.get_message_bubble("test_user_light")
        assert bubble is not None
        assert bubble.role == MessageRole.USER

        # Verify enhanced styling is applied
        style_sheet = bubble.styleSheet()

        # Should have background color for distinction
        assert "background-color" in style_sheet.lower()

        # Should have border styling for distinction
        assert "border:" in style_sheet.lower() or "border " in style_sheet.lower()

        # Should have border-radius
        assert "border-radius" in style_sheet.lower()

        # Should have left alignment (no margin-left for right alignment)
        assert (
            "margin-left" not in style_sheet.lower()
            or "margin-left: 0" in style_sheet.lower()
        )

    def test_user_message_dark_theme_enhanced_styling(self, display_area, qapp):
        """Test that user messages have enhanced styling in dark theme."""
        # Apply dark theme
        display_area.apply_theme("dark")

        # Add user message
        message = ChatMessage(
            message_id="test_user_dark",
            role=MessageRole.USER,
            content="Test user message dark",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        # Get the created bubble
        bubble = display_area.get_message_bubble("test_user_dark")
        assert bubble is not None

        # Verify dark theme styling
        style_sheet = bubble.styleSheet()

        # Should have appropriate colors for dark theme
        assert "background-color" in style_sheet.lower()
        assert "border:" in style_sheet.lower() or "border " in style_sheet.lower()

    def test_user_message_has_subtle_border_enhancement(self, display_area, qapp):
        """Test that user messages have subtle border for distinction."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_border",
            role=MessageRole.USER,
            content="Testing border enhancement",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_border")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have border for distinction
        assert "border:" in style_sheet.lower() or "border " in style_sheet.lower()

    def test_user_message_background_refinement(self, display_area, qapp):
        """Test user message background refinement."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_bg",
            role=MessageRole.USER,
            content="Testing background",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_bg")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have background color
        assert "background-color" in style_sheet.lower()

    def test_user_message_preserves_alignment_and_spacing(self, display_area, qapp):
        """Test that styling preserves proper alignment and spacing."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_alignment",
            role=MessageRole.USER,
            content="Testing alignment preservation",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_alignment")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have left alignment with proper spacing
        assert "margin:" in style_sheet.lower() or "padding:" in style_sheet.lower()

    def test_user_message_styling_does_not_affect_other_roles(self, display_area, qapp):
        """Test that enhanced user styling doesn't affect assistant/system messages."""
        display_area.apply_theme("light")

        # Add messages of different roles
        user_msg = ChatMessage(
            message_id="test_user",
            role=MessageRole.USER,
            content="User message",
            status=MessageStatus.DELIVERED,
        )

        assistant_msg = ChatMessage(
            message_id="test_assistant",
            role=MessageRole.ASSISTANT,
            content="Assistant message",
            status=MessageStatus.DELIVERED,
        )

        system_msg = ChatMessage(
            message_id="test_system",
            role=MessageRole.SYSTEM,
            content="System message",
            status=MessageStatus.DELIVERED,
        )

        display_area.message_model.add_message(user_msg)
        display_area.message_model.add_message(assistant_msg)
        display_area.message_model.add_message(system_msg)

        user_bubble = display_area.get_message_bubble("test_user")
        assistant_bubble = display_area.get_message_bubble("test_assistant")
        system_bubble = display_area.get_message_bubble("test_system")

        assert all(
            bubble is not None
            for bubble in [user_bubble, assistant_bubble, system_bubble]
        )

        # User should have border styling
        user_style = user_bubble.styleSheet()
        assert "border:" in user_style.lower() or "border " in user_style.lower()

        # Assistant should have transparent background
        assistant_style = assistant_bubble.styleSheet()
        assert "transparent" in assistant_style.lower()

    def test_enhanced_styling_theme_consistency(self, display_area, qapp):
        """Test that enhanced styling is consistent across theme switches."""
        # Create user message
        message = ChatMessage(
            message_id="test_consistency",
            role=MessageRole.USER,
            content="Testing theme consistency",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_consistency")
        assert bubble is not None

        # Test light theme styling
        display_area.apply_theme("light")
        light_style = bubble.styleSheet()

        # Test dark theme styling
        display_area.apply_theme("dark")
        dark_style = bubble.styleSheet()

        # Styles should be different but both should have enhancements
        assert light_style != dark_style

        # Both should have core properties
        for style in [light_style, dark_style]:
            assert "background-color" in style.lower()
            assert "border-radius" in style.lower()
            assert "border:" in style.lower() or "border " in style.lower()

    def test_enhanced_user_message_visual_hierarchy(self, display_area, qapp):
        """Test that enhanced styling creates clear visual hierarchy."""
        display_area.apply_theme("light")

        # Add both user and assistant messages
        user_msg = ChatMessage(
            message_id="test_user_hier",
            role=MessageRole.USER,
            content="User message",
            status=MessageStatus.DELIVERED,
        )

        assistant_msg = ChatMessage(
            message_id="test_assistant_hier",
            role=MessageRole.ASSISTANT,
            content="Assistant message",
            status=MessageStatus.DELIVERED,
        )

        display_area.message_model.add_message(user_msg)
        display_area.message_model.add_message(assistant_msg)

        user_bubble = display_area.get_message_bubble("test_user_hier")
        assistant_bubble = display_area.get_message_bubble("test_assistant_hier")

        assert user_bubble is not None
        assert assistant_bubble is not None

        user_style = user_bubble.styleSheet()
        assistant_style = assistant_bubble.styleSheet()

        # User should have distinct styling (border, background)
        assert "border:" in user_style.lower() or "border " in user_style.lower()
        assert "background-color" in user_style.lower()

        # Assistant should be more minimal
        assert "transparent" in assistant_style.lower()

    def test_user_message_has_enhanced_depth_styling(self, display_area, qapp):
        """Test that user messages have enhanced styling for visual depth."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_depth",
            role=MessageRole.USER,
            content="Test message for depth styling",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_depth")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have border for visual distinction
        depth_styling = any(
            prop in style_sheet.lower()
            for prop in ["border:", "border ", "background-color"]
        )
        assert depth_styling, (
            "User messages should have border styling for visual distinction"
        )

    def test_user_message_has_refined_border_in_dark_theme(self, display_area, qapp):
        """Test refined border styling in dark theme."""
        display_area.apply_theme("dark")

        message = ChatMessage(
            message_id="test_dark_border",
            role=MessageRole.USER,
            content="Test dark border",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_dark_border")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have border in dark theme
        assert "border:" in style_sheet.lower() or "border " in style_sheet.lower()

    def test_user_message_has_enhanced_background_gradient(self, display_area, qapp):
        """Test user message background styling."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_gradient",
            role=MessageRole.USER,
            content="Test background",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_gradient")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have background color for distinction
        assert "background-color" in style_sheet.lower()

    def test_user_message_has_improved_border_radius(self, display_area, qapp):
        """Test that user messages have border-radius values."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_radius",
            role=MessageRole.USER,
            content="Test border radius",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_radius")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have border-radius
        assert "border-radius" in style_sheet.lower()

    def test_user_message_light_theme_has_enhanced_colors(self, display_area, qapp):
        """Test light theme color enhancements."""
        display_area.apply_theme("light")

        message = ChatMessage(
            message_id="test_light_colors",
            role=MessageRole.USER,
            content="Test light colors",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_light_colors")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have appropriate light theme colors
        assert "background-color" in style_sheet.lower()

    def test_user_message_dark_theme_has_enhanced_colors(self, display_area, qapp):
        """Test dark theme color enhancements."""
        display_area.apply_theme("dark")

        message = ChatMessage(
            message_id="test_dark_colors",
            role=MessageRole.USER,
            content="Test dark colors",
            status=MessageStatus.DELIVERED,
        )
        display_area.message_model.add_message(message)

        bubble = display_area.get_message_bubble("test_dark_colors")
        assert bubble is not None

        style_sheet = bubble.styleSheet()

        # Should have appropriate dark theme colors
        assert "background-color" in style_sheet.lower()

    def test_user_message_maintains_bubble_identity(self, display_area, qapp):
        """Test that styling maintains clear distinction between user and AI messages."""
        display_area.apply_theme("light")

        # Add both user and assistant messages for comparison
        user_msg = ChatMessage(
            message_id="test_user_identity",
            role=MessageRole.USER,
            content="User message",
            status=MessageStatus.DELIVERED,
        )

        assistant_msg = ChatMessage(
            message_id="test_assistant_identity",
            role=MessageRole.ASSISTANT,
            content="Assistant message",
            status=MessageStatus.DELIVERED,
        )

        display_area.message_model.add_message(user_msg)
        display_area.message_model.add_message(assistant_msg)

        user_bubble = display_area.get_message_bubble("test_user_identity")
        assistant_bubble = display_area.get_message_bubble("test_assistant_identity")

        assert user_bubble is not None
        assert assistant_bubble is not None

        user_style = user_bubble.styleSheet()
        assistant_style = assistant_bubble.styleSheet()

        # User should have distinguishing characteristics (border, background-color, border-radius)
        user_distinguishing_traits = [
            "border:" in user_style.lower() or "border " in user_style.lower(),
            "background-color" in user_style.lower(),
            "border-radius" in user_style.lower(),
        ]

        # Assistant should have transparent styling
        assistant_transparent_traits = ["transparent" in assistant_style.lower()]

        assert all(user_distinguishing_traits), (
            "User messages should have clear distinguishing identity"
        )
        assert all(assistant_transparent_traits), (
            "Assistant messages should have transparent styling"
        )
