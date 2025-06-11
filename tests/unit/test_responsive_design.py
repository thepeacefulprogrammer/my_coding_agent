"""Comprehensive unit tests for responsive design across different window sizes.

This module tests the chat widget's ability to adapt to different window sizes
and maintain usability and visual quality at various screen resolutions.
"""

import pytest
from PyQt6.QtWidgets import QApplication, QMainWindow

from my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget


class TestResponsiveDesign:
    """Test cases for responsive design functionality."""

    @pytest.fixture
    def chat_widget(self, qapp):
        """Create a chat widget instance for testing."""
        widget = SimplifiedChatWidget()
        widget.add_user_message("Test user message for responsive testing")
        widget.add_assistant_message(
            "Test assistant response with longer content that should wrap properly "
            "across different window sizes and demonstrate responsive behavior."
        )
        widget.add_system_message("System message test")
        return widget

    @pytest.fixture
    def main_window(self, qapp, chat_widget):
        """Create a main window with chat widget for testing."""
        window = QMainWindow()
        window.setCentralWidget(chat_widget)
        window.show()  # Show the window to make widgets visible
        QApplication.processEvents()  # Process events to complete initialization
        return window

    def test_minimum_window_size_constraint(self, main_window, chat_widget):
        """Test that minimum window size maintains usability."""
        # Ensure window is visible first
        main_window.show()
        QApplication.processEvents()

        # Set to very small size
        main_window.resize(300, 200)

        # Process events to trigger layout updates
        QApplication.processEvents()

        # Check that minimum size constraint is applied
        assert chat_widget.minimumSize().width() == 320
        assert chat_widget.minimumSize().height() == 240

        # Check that input area properties are reasonable for small screens
        assert chat_widget.input_text.minimumHeight() <= 40
        assert chat_widget.input_text.maximumHeight() <= 100

        # Check basic widget structure exists
        assert hasattr(chat_widget, "input_text")
        assert hasattr(chat_widget, "send_icon")
        assert hasattr(chat_widget, "display_area")

    def test_mobile_like_window_size(self, main_window, chat_widget):
        """Test responsive behavior at mobile-like dimensions."""
        # Ensure visibility
        main_window.show()
        QApplication.processEvents()

        # Mobile-like aspect ratio: tall and narrow
        main_window.resize(360, 640)
        QApplication.processEvents()

        # Check text wrapping capability
        display_area = chat_widget.display_area

        # Verify messages have word wrapping enabled
        for bubble in display_area._message_bubbles.values():
            assert bubble.content_display.wordWrap() is True

    def test_tablet_window_size(self, main_window, chat_widget):
        """Test responsive behavior at tablet-like dimensions."""
        # Tablet-like dimensions
        main_window.resize(768, 1024)
        QApplication.processEvents()

        # Check that layout utilizes available space efficiently
        display_area = chat_widget.display_area
        input_area_height = chat_widget.input_text.height()

        # Display area should take most of the space
        assert display_area.height() > input_area_height * 8

        # Check message bubble sizing
        for bubble in display_area._message_bubbles.values():
            # Messages should span available width
            bubble_width = bubble.width()
            container_width = display_area.container.width()
            # Account for margins/padding
            assert bubble_width >= container_width * 0.9

    def test_desktop_window_size(self, main_window, chat_widget):
        """Test responsive behavior at desktop dimensions."""
        # Large desktop window
        main_window.resize(1440, 900)
        QApplication.processEvents()

        # Check that content doesn't become unusably wide
        display_area = chat_widget.display_area

        # Messages should utilize full width but remain readable
        for bubble in display_area._message_bubbles.values():
            assert bubble.content_display.wordWrap() is True
            # Content should wrap appropriately
            content_width = bubble.content_display.width()
            assert content_width > 0

    def test_ultrawide_window_size(self, main_window, chat_widget):
        """Test responsive behavior at ultrawide dimensions."""
        # Test with ultrawide resolution
        main_window.resize(3440, 1440)  # Ultrawide 1440p
        QApplication.processEvents()

        # Check that content doesn't become unusably wide
        display_area = chat_widget.display_area

        # Messages should utilize full width but remain readable
        assert display_area.isVisible()
        assert display_area.width() > 0

    def test_window_resize_text_wrapping(self, main_window, chat_widget):
        """Test that text wrapping adapts during window resize."""
        # Add a message with long content
        long_message = "This is a very long message " * 20
        chat_widget.add_assistant_message(long_message)
        QApplication.processEvents()

        # Start with wide window
        main_window.resize(1200, 600)
        QApplication.processEvents()

        # Get initial bubble dimensions
        bubbles = list(chat_widget.display_area._message_bubbles.values())
        long_bubble = bubbles[-1]  # Last added bubble
        initial_height = long_bubble.height()

        # Resize to narrow window
        main_window.resize(400, 600)
        QApplication.processEvents()

        # Height should increase due to text wrapping
        new_height = long_bubble.height()
        assert new_height >= initial_height  # More wrapping = taller bubble

    def test_input_area_responsiveness(self, main_window, chat_widget):
        """Test that input area adapts to different window sizes."""
        # Ensure visibility
        main_window.show()
        QApplication.processEvents()

        sizes_to_test = [
            (320, 240),  # Minimum size
            (600, 400),  # Medium
            (1200, 800),  # Large
        ]

        for width, height in sizes_to_test:
            main_window.resize(width, height)
            QApplication.processEvents()

            # Check that input height adapts to window size
            max_input_height = chat_widget.input_text.maximumHeight()

            # Should be reasonable for the window size
            assert max_input_height >= 32  # Not too small
            assert max_input_height <= height // 4  # Not too large relative to window

    def test_scroll_area_responsiveness(self, main_window, chat_widget):
        """Test that scroll area adapts to different window sizes."""
        # Add many messages to test scrolling
        for i in range(10):
            chat_widget.add_user_message(f"User message {i}")
            chat_widget.add_assistant_message(f"Assistant response {i}")

        QApplication.processEvents()

        sizes_to_test = [
            (400, 300),  # Small
            (800, 600),  # Medium
            (1200, 900),  # Large
        ]

        for width, height in sizes_to_test:
            main_window.resize(width, height)
            QApplication.processEvents()

            display_area = chat_widget.display_area

            # Scroll area should adapt to available space
            assert display_area.width() > 0
            assert display_area.height() > 0

            # Should maintain scrolling capability
            scrollbar = display_area.verticalScrollBar()
            assert scrollbar is not None

            # Container should be properly sized
            container = display_area.container
            assert container.width() > 0

    def test_font_scaling_responsiveness(self, main_window, chat_widget):
        """Test that font scaling works with responsive design."""
        # Test different DPI-like scenarios by changing font sizes
        display_area = chat_widget.display_area

        # Test with different window sizes
        sizes = [(400, 300), (800, 600), (1200, 900)]

        for width, height in sizes:
            main_window.resize(width, height)
            QApplication.processEvents()

            # Check that text remains readable
            for bubble in display_area._message_bubbles.values():
                content_label = bubble.content_display

                # Text should be visible and have reasonable size
                assert content_label.isVisible()
                font = content_label.font()
                assert font.pointSize() > 0 or font.pixelSize() > 0

    def test_layout_stability_during_resize(self, main_window, chat_widget):
        """Test that layout remains stable during window resizing."""
        # Add various message types
        chat_widget.add_user_message("User message")
        chat_widget.add_assistant_message("Assistant message")
        chat_widget.add_system_message("System message")
        QApplication.processEvents()

        # Rapidly change window sizes
        sizes = [
            (300, 200),
            (600, 400),
            (900, 600),
            (450, 300),
            (1200, 800),
            (400, 250),
        ]

        for width, height in sizes:
            main_window.resize(width, height)
            QApplication.processEvents()

            # Check that layout doesn't break
            display_area = chat_widget.display_area
            assert display_area.container.layout() is not None

            # All message bubbles should remain valid
            for bubble in display_area._message_bubbles.values():
                assert bubble.isVisible()
                assert bubble.parent() is not None

            # Input area should remain functional
            assert chat_widget.input_text.isVisible()
            assert chat_widget.send_icon.isVisible()

    def test_aspect_ratio_adaptability(self, main_window, chat_widget):
        """Test adaptability to different aspect ratios."""
        aspect_ratios = [
            (400, 800),  # Portrait (mobile)
            (800, 400),  # Landscape (wide)
            (600, 600),  # Square
            (1600, 600),  # Ultrawide
        ]

        for width, height in aspect_ratios:
            main_window.resize(width, height)
            QApplication.processEvents()

            # Layout should adapt to any aspect ratio
            display_area = chat_widget.display_area
            input_area = chat_widget.input_text

            # Both areas should be visible and functional
            assert display_area.isVisible()
            assert input_area.isVisible()

            # Display area should take majority of space
            display_height = display_area.height()
            input_height = input_area.height()
            total_height = display_height + input_height

            # Display should be at least 60% of available space
            assert display_height >= total_height * 0.6

    def test_message_bubble_size_policies(self, chat_widget):
        """Test that message bubbles have appropriate size policies for responsive design."""
        # Ensure widget is shown
        chat_widget.show()
        QApplication.processEvents()

        # Add messages to test
        chat_widget.add_user_message("Test message")
        chat_widget.add_assistant_message("Another test message")
        QApplication.processEvents()

        display_area = chat_widget.display_area

        for bubble in display_area._message_bubbles.values():
            size_policy = bubble.sizePolicy()

            # Should have appropriate horizontal policy for full width
            h_policy = size_policy.horizontalPolicy()
            assert h_policy in [
                bubble.sizePolicy().Policy.Preferred,
                bubble.sizePolicy().Policy.Expanding,
            ]

            # Should have minimum vertical policy for content-based height
            v_policy = size_policy.verticalPolicy()
            assert v_policy == bubble.sizePolicy().Policy.Minimum

            # Content labels should wrap text
            assert bubble.content_display.wordWrap() is True
