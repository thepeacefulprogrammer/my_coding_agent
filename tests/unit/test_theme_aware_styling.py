"""Unit tests for theme-aware styling that adapts to application theme (Task 3.5)."""

import pytest
from PyQt6.QtWidgets import QApplication
from src.my_coding_agent.core.theme_manager import ThemeManager
from src.my_coding_agent.gui.chat_message_model import ChatMessage
from src.my_coding_agent.gui.chat_widget_v2 import SimplifiedChatWidget
from src.my_coding_agent.gui.components.message_display import (
    MessageDisplay,
    MessageDisplayTheme,
)


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    return QApplication.instance() or QApplication([])


@pytest.fixture
def theme_manager(app):
    """Create ThemeManager instance for testing."""
    return ThemeManager(app)


@pytest.fixture
def sample_user_message():
    """Create a sample user message."""
    return ChatMessage.create_user_message("Test user message")


@pytest.fixture
def sample_assistant_message():
    """Create a sample assistant message."""
    return ChatMessage.create_assistant_message("Test assistant message")


class TestThemeAwareStylingSuite:
    """Test suite for automatic theme adaptation functionality."""

    def test_theme_manager_signals_theme_changes(self, app, theme_manager):
        """Test that ThemeManager emits signals when theme changes."""
        # ThemeManager should emit a signal when theme changes
        assert hasattr(theme_manager, "theme_changed")

        # Set up signal listener
        signal_received = []
        theme_manager.theme_changed.connect(lambda theme: signal_received.append(theme))

        # Change theme
        initial_theme = theme_manager.get_current_theme()
        new_theme = "light" if initial_theme == "dark" else "dark"

        theme_manager.set_theme(new_theme)

        # Signal should have been emitted
        assert len(signal_received) == 1
        assert signal_received[0] == new_theme

    def test_message_display_auto_theme_adaptation(
        self, app, theme_manager, sample_user_message
    ):
        """Test that MessageDisplay automatically adapts when application theme changes."""
        # Create MessageDisplay that should adapt to app theme
        display = MessageDisplay(
            sample_user_message, auto_adapt_theme=True, theme_manager=theme_manager
        )

        # Get initial styling
        initial_theme = theme_manager.get_current_theme()
        initial_style = display.styleSheet()

        # Change application theme
        new_theme = "light" if initial_theme == "dark" else "dark"
        theme_manager.set_theme(new_theme)

        # MessageDisplay should automatically update its styling
        updated_style = display.styleSheet()
        assert updated_style != initial_style

        # Should reflect the new theme colors
        if new_theme == "dark":
            assert "#1E88E5" in updated_style or "#2a2a2a" in updated_style
        else:
            assert "#4285F4" in updated_style or "#f8f9fa" in updated_style

    def test_chat_widget_auto_theme_adaptation(self, app, theme_manager):
        """Test that SimplifiedChatWidget automatically adapts when application theme changes."""
        # Create chat widget that should adapt to app theme
        chat_widget = SimplifiedChatWidget(
            auto_adapt_theme=True, theme_manager=theme_manager
        )

        # Add some messages
        chat_widget.add_user_message("Test user message")
        chat_widget.add_assistant_message("Test assistant message")

        # Get initial theme and styling
        initial_theme = theme_manager.get_current_theme()
        initial_input_style = chat_widget.input_text.styleSheet()

        # Change application theme
        new_theme = "light" if initial_theme == "dark" else "dark"
        theme_manager.set_theme(new_theme)

        # Chat widget should automatically update its styling
        updated_input_style = chat_widget.input_text.styleSheet()
        assert updated_input_style != initial_input_style

        # Verify input area reflects new theme
        if new_theme == "dark":
            assert (
                "#3a3a3a" in updated_input_style
                or "dark" in updated_input_style.lower()
            )
        else:
            assert "white" in updated_input_style or "#fff" in updated_input_style

    def test_theme_aware_widget_base_class(self, app, theme_manager):
        """Test that ThemeAwareWidget base class provides automatic theme adaptation."""
        from src.my_coding_agent.gui.components.theme_aware_widget import (
            ThemeAwareWidget,
        )

        # Create theme-aware widget
        widget = ThemeAwareWidget(theme_manager=theme_manager)

        # Should have theme manager reference
        assert widget.theme_manager is theme_manager

        # Should have automatic theme update method
        assert hasattr(widget, "_on_theme_changed")
        assert callable(widget._on_theme_changed)

        # Should be connected to theme manager (we can't easily test signal connections in PyQt6)
        # Just verify the widget was registered
        assert widget in theme_manager._connected_widgets

    def test_application_wide_theme_synchronization(self, app, theme_manager):
        """Test that all theme-aware components update simultaneously when app theme changes."""
        # Create multiple theme-aware components
        message_display = MessageDisplay(
            ChatMessage.create_user_message("Test"),
            auto_adapt_theme=True,
            theme_manager=theme_manager,
        )
        chat_widget = SimplifiedChatWidget(
            auto_adapt_theme=True, theme_manager=theme_manager
        )

        # Get initial styles
        initial_message_style = message_display.styleSheet()
        initial_chat_style = chat_widget.input_text.styleSheet()

        # Change theme once
        initial_theme = theme_manager.get_current_theme()
        new_theme = "light" if initial_theme == "dark" else "dark"
        theme_manager.set_theme(new_theme)

        # All components should update
        assert message_display.styleSheet() != initial_message_style
        assert chat_widget.input_text.styleSheet() != initial_chat_style

        # All should reflect the same theme
        current_theme = theme_manager.get_current_theme()
        assert current_theme == new_theme

    def test_theme_adaptation_with_existing_components(self, app, theme_manager):
        """Test that existing components without auto-adaptation still work."""
        # Create component without auto-adaptation (existing behavior)
        message_display = MessageDisplay(ChatMessage.create_user_message("Test"))

        # Should still work with manual theme setting
        message_display.set_theme(MessageDisplayTheme.DARK)
        dark_style = message_display.styleSheet()

        message_display.set_theme(MessageDisplayTheme.LIGHT)
        light_style = message_display.styleSheet()

        assert dark_style != light_style

        # Should not automatically update when app theme changes
        initial_style = message_display.styleSheet()
        theme_manager.toggle_theme()
        assert message_display.styleSheet() == initial_style

    def test_theme_manager_enhanced_with_signals(self, app, theme_manager):
        """Test that enhanced ThemeManager properly emits signals and tracks listeners."""
        # Should have signal emission capabilities
        assert hasattr(theme_manager, "theme_changed")

        # Should track connected widgets
        assert hasattr(theme_manager, "_connected_widgets")
        assert isinstance(theme_manager._connected_widgets, list)

        # Should have widget registration methods
        assert hasattr(theme_manager, "register_widget")
        assert hasattr(theme_manager, "unregister_widget")

    def test_theme_aware_component_cleanup(self, app, theme_manager):
        """Test that theme-aware components clean up properly when destroyed."""
        # Create theme-aware component
        message_display = MessageDisplay(
            ChatMessage.create_user_message("Test"),
            auto_adapt_theme=True,
            theme_manager=theme_manager,
        )

        # Should be registered with theme manager
        initial_widget_count = len(theme_manager._connected_widgets)

        # Delete component
        message_display.deleteLater()
        # Process Qt events to ensure cleanup
        QApplication.processEvents()

        # Should be unregistered from theme manager
        final_widget_count = len(theme_manager._connected_widgets)
        assert final_widget_count < initial_widget_count

    def test_multiple_theme_toggles_consistency(self, app, theme_manager):
        """Test that rapid theme changes maintain consistency."""
        # Create theme-aware component
        message_display = MessageDisplay(
            ChatMessage.create_user_message("Test"),
            auto_adapt_theme=True,
            theme_manager=theme_manager,
        )

        # Record initial state
        initial_theme = theme_manager.get_current_theme()
        initial_style = message_display.styleSheet()

        # Toggle theme multiple times
        for _ in range(3):
            theme_manager.toggle_theme()
            QApplication.processEvents()  # Allow signal processing

        # After odd number of toggles, should be different from initial
        final_theme = theme_manager.get_current_theme()
        final_style = message_display.styleSheet()

        assert final_theme != initial_theme
        assert final_style != initial_style

    def test_theme_adaptation_with_custom_styling(
        self, app, theme_manager, sample_user_message
    ):
        """Test that theme adaptation works with custom styled components."""
        # Create component with both auto-adaptation and custom styling
        message_display = MessageDisplay(
            sample_user_message, auto_adapt_theme=True, theme_manager=theme_manager
        )

        # Apply additional custom styling
        custom_style = "QLabel { font-weight: bold; }"
        message_display.setStyleSheet(message_display.styleSheet() + custom_style)

        # Change theme
        theme_manager.toggle_theme()

        # Should maintain custom styling while updating theme colors
        updated_style = message_display.styleSheet()
        assert "font-weight: bold" in updated_style

        # But should also have updated theme colors
        current_theme = theme_manager.get_current_theme()
        if current_theme == "dark":
            assert any(
                color in updated_style for color in ["#1E88E5", "#2a2a2a", "#ffffff"]
            )
        else:
            assert any(
                color in updated_style for color in ["#4285F4", "#f8f9fa", "#333"]
            )

    def test_theme_adaptation_performance(self, app, theme_manager):
        """Test that theme adaptation doesn't cause performance issues with many components."""
        # Create many theme-aware components
        components = []
        for i in range(50):
            message = ChatMessage.create_user_message(f"Message {i}")
            component = MessageDisplay(
                message, auto_adapt_theme=True, theme_manager=theme_manager
            )
            components.append(component)

        # Measure theme change time
        import time

        start_time = time.time()

        theme_manager.toggle_theme()
        QApplication.processEvents()

        end_time = time.time()

        # Should complete quickly (under 1 second for 50 components)
        assert (end_time - start_time) < 1.0

        # All components should have updated
        current_theme = theme_manager.get_current_theme()
        for component in components:
            style = component.styleSheet()
            if current_theme == "dark":
                assert any(
                    color in style for color in ["#1E88E5", "#2a2a2a", "#ffffff"]
                )
            else:
                assert any(color in style for color in ["#4285F4", "#f8f9fa", "#333"])

    def test_theme_adaptation_error_handling(self, app, theme_manager):
        """Test that theme adaptation handles errors gracefully."""
        # Create component with auto-adaptation
        message_display = MessageDisplay(
            ChatMessage.create_user_message("Test"),
            auto_adapt_theme=True,
            theme_manager=theme_manager,
        )

        # Mock theme adaptation to raise exception

        def failing_adaptation(*args):
            raise Exception("Theme adaptation failed")

        message_display._on_theme_changed = failing_adaptation

        # Theme change should not crash the application
        try:
            theme_manager.toggle_theme()
            QApplication.processEvents()
        except Exception:
            pytest.fail("Theme adaptation error should be handled gracefully")

        # Application should still be functional
        assert theme_manager.get_current_theme() in ["light", "dark"]

    def test_backward_compatibility_with_manual_themes(self, app, theme_manager):
        """Test that automatic theme adaptation doesn't break existing manual theme setting."""
        # Create component without auto-adaptation (existing behavior)
        message_display = MessageDisplay(ChatMessage.create_user_message("Test"))

        # Manual theme setting should still work
        message_display.set_theme(MessageDisplayTheme.DARK)
        dark_style = message_display.styleSheet()

        # Change app theme - should not affect manually themed component
        theme_manager.toggle_theme()
        assert message_display.styleSheet() == dark_style

        # Manual theme change should still work
        message_display.set_theme(MessageDisplayTheme.LIGHT)
        light_style = message_display.styleSheet()
        assert light_style != dark_style
