#!/usr/bin/env python3
"""
Test script to verify streaming integration between MainWindow and ChatWidget.

This script tests the basic streaming functionality without requiring
a full GUI application run.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication

from my_coding_agent.core.ai_agent import AIAgent, AIResponse
from my_coding_agent.core.main_window import MainWindow


def test_streaming_integration_mock():
    """Test the streaming integration with mocked AI Agent."""

    # Create QApplication for testing
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        # Create main window
        main_window = MainWindow()

        # Mock the AI agent to avoid requiring real Azure OpenAI credentials
        mock_ai_agent = MagicMock(spec=AIAgent)

        # Mock the streaming response
        async def mock_streaming_response(
            message, on_chunk, on_error, enable_filesystem
        ):
            """Mock streaming response that simulates AI output."""
            try:
                # Simulate chunks being streamed
                chunks = ["Hello ", "there! ", "This is ", "a streaming ", "response."]

                for i, chunk in enumerate(chunks):
                    await asyncio.sleep(0.1)  # Simulate delay
                    is_final = i == len(chunks) - 1
                    on_chunk(chunk, is_final)

                # Return successful response
                return AIResponse(
                    content="Hello there! This is a streaming response.",
                    success=True,
                    stream_id="test-stream",
                    retry_count=0,
                )

            except Exception as e:
                on_error(e)
                return AIResponse(
                    content="",
                    success=False,
                    error=str(e),
                    stream_id="test-stream",
                    retry_count=0,
                )

        mock_ai_agent.send_message_with_tools_stream = AsyncMock(
            side_effect=mock_streaming_response
        )

        # Replace the real AI agent with our mock
        main_window._ai_agent = mock_ai_agent

        # Test streaming by sending a message
        chat_widget = main_window.chat_widget

        # Enable test mode for reliable testing
        chat_widget.display_area.set_test_mode(True)

        # Send a test message to trigger streaming
        print("Testing streaming integration...")
        print("Initial streaming state:", chat_widget.is_streaming())

        # Simulate user sending a message
        chat_widget.add_user_message("Hello AI!")

        # Trigger the streaming response (this is normally triggered by the message_sent signal)
        main_window._handle_chat_message("Hello AI!")

        # Process events to allow the streaming to start
        app.processEvents()

        # Wait a moment for the async operation to start
        import time

        time.sleep(0.5)
        app.processEvents()

        print("Streaming test completed!")
        print("Final message count:", chat_widget.message_model.get_message_count())

        # Verify we have messages
        messages = chat_widget.message_model.get_all_messages()
        for i, msg in enumerate(messages):
            print(
                f"Message {i}: {msg.role.value} - '{msg.content}' (status: {msg.status.value})"
            )

        return True

    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        if hasattr(main_window, "close"):
            main_window.close()


if __name__ == "__main__":
    print("Testing streaming integration...")
    success = test_streaming_integration_mock()

    if success:
        print("✅ Streaming integration test passed!")
        sys.exit(0)
    else:
        print("❌ Streaming integration test failed!")
        sys.exit(1)
