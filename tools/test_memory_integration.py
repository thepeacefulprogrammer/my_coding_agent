#!/usr/bin/env python3
"""Test script for memory integration functionality."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from my_coding_agent.core.memory_integration import ConversationMemoryHandler


def test_memory_integration():
    """Test the memory integration functionality."""
    print("🧪 Testing Memory Integration...")

    # Create memory handler
    handler = ConversationMemoryHandler()
    print(
        f"✅ Created memory handler with session: {handler.current_session_id[:8]}..."
    )

    # Store some test messages
    print("\n📝 Storing test messages...")
    user_msg_id = handler.store_user_message("Hello, can you help me with Python?")
    print(f"   User message stored with ID: {user_msg_id}")

    assistant_msg_id = handler.store_assistant_message(
        "Of course! I'd be happy to help you with Python. What specific topic would you like to learn about?"
    )
    print(f"   Assistant message stored with ID: {assistant_msg_id}")

    user_msg_id2 = handler.store_user_message("I want to learn about decorators.")
    print(f"   User message 2 stored with ID: {user_msg_id2}")

    # Retrieve conversation context
    print("\n📚 Retrieving conversation context...")
    context = handler.get_conversation_context(limit=10)
    print(f"   Retrieved {len(context)} messages:")

    for i, msg in enumerate(context, 1):
        role = msg["role"].upper()
        content = (
            msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        )
        print(f"   {i}. {role}: {content}")

    # Test new session
    print("\n🔄 Testing new session...")
    old_session = handler.current_session_id
    new_session = handler.start_new_session()
    print(f"   Old session: {old_session[:8]}...")
    print(f"   New session: {new_session[:8]}...")

    # Check that new session has no context
    new_context = handler.get_conversation_context(limit=10)
    print(f"   New session context: {len(new_context)} messages")

    # Get memory stats
    print("\n📊 Memory statistics:")
    stats = handler.get_memory_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n✅ Memory integration test completed successfully!")


if __name__ == "__main__":
    test_memory_integration()
