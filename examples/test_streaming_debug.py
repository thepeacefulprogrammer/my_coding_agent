#!/usr/bin/env python3
"""Test script to verify streaming chunk accumulation is working correctly."""

import os
import sys

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

# Add the libs to the path
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "libs", "code_viewer", "src")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "libs", "agent_arch", "src")
)

from code_viewer.core.main_window import MainWindow


def test_streaming_accumulation():
    """Test that streaming chunks accumulate properly."""
    print("🧪 Testing streaming chunk accumulation...")

    app = QApplication(sys.argv)

    # Use current directory as the directory path
    current_dir = os.getcwd()
    main_window = MainWindow(directory_path=current_dir)
    main_window.show()

    # Wait for initialization
    QTimer.singleShot(500, lambda: test_accumulation_logic(main_window, app))

    return app.exec()


def test_accumulation_logic(main_window, app):
    """Test the accumulation logic."""
    try:
        chat_widget = main_window._chat_widget

        print("✅ Chat widget found")

        # Start a streaming response
        stream_id = "test_stream_123"
        message_id = chat_widget.start_streaming_response(stream_id)
        print(f"✅ Started streaming response: {message_id}")

        # Send chunks one by one and verify accumulation
        chunks = ["Hello ", "world! ", "This ", "is ", "a ", "streaming ", "test."]
        expected_content = ""

        for i, chunk in enumerate(chunks):
            # Add chunk
            chat_widget.append_streaming_chunk(chunk)
            expected_content += chunk

            # Get the message and check content
            message = chat_widget.message_model.get_message_by_id(message_id)
            if message:
                actual_content = message.content
                print(f"📝 Chunk {i + 1}: '{chunk}' -> Content: '{actual_content}'")

                if actual_content == expected_content:
                    print(f"✅ Chunk {i + 1} accumulated correctly")
                else:
                    print(
                        f"❌ Chunk {i + 1} failed! Expected: '{expected_content}', Got: '{actual_content}'"
                    )
                    break
            else:
                print(f"❌ Could not find message {message_id}")
                break
        else:
            print("🎉 All chunks accumulated successfully!")
            print(f"📄 Final content: '{expected_content}'")

        # Complete the streaming
        chat_widget.complete_streaming_response()
        print("✅ Streaming completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()

    # Close after a short delay
    QTimer.singleShot(2000, app.quit)


if __name__ == "__main__":
    exit_code = test_streaming_accumulation()
    sys.exit(exit_code)
