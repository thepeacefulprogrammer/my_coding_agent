"""Unit tests for automated memory classification system."""

import pytest
from src.my_coding_agent.core.memory.memory_classifier import MemoryClassifier
from src.my_coding_agent.core.memory.memory_types import (
    ConversationMessage,
    LongTermMemory,
)


class TestMemoryClassifier:
    """Test cases for MemoryClassifier."""

    @pytest.fixture
    def classifier(self):
        """Create a MemoryClassifier instance for testing."""
        return MemoryClassifier()

    def test_classifier_initialization(self, classifier):
        """Test that classifier initializes with correct defaults."""
        assert classifier.importance_threshold == 0.3
        assert classifier.min_content_length == 20
        assert len(classifier.classification_rules) > 0

    def test_analyze_conversation_message(self, classifier):
        """Test basic message analysis functionality."""
        message = ConversationMessage(
            content="I prefer dark mode for all applications", role="user", tokens=8
        )

        analysis = classifier.analyze_message(message)

        assert "importance_score" in analysis
        assert "memory_type" in analysis
        assert "should_save" in analysis
        assert "reasoning" in analysis
        assert isinstance(analysis["importance_score"], float)
        assert 0.0 <= analysis["importance_score"] <= 1.0

    def test_preference_classification(self, classifier):
        """Test classification of user preferences."""
        preference_messages = [
            "I prefer Python over JavaScript for backend development",
            "Please always use tabs instead of spaces for indentation",
            "I like to see detailed error messages when debugging",
        ]

        for content in preference_messages:
            message = ConversationMessage(
                content=content, role="user", tokens=len(content.split())
            )
            analysis = classifier.analyze_message(message)

            assert analysis["memory_type"] == "preference"
            assert analysis["importance_score"] > classifier.importance_threshold
            assert analysis["should_save"] is True

    def test_fact_classification(self, classifier):
        """Test classification of factual information."""
        fact_messages = [
            "The project database is hosted on PostgreSQL version 14.2",
            "Our API endpoint is https://api.example.com/v1/",
            "The main configuration file is located at /etc/app/config.yaml",
        ]

        for content in fact_messages:
            message = ConversationMessage(content=content, role="assistant")
            analysis = classifier.analyze_message(message)

            assert analysis["memory_type"] == "fact"
            assert analysis["importance_score"] > classifier.importance_threshold
            assert analysis["should_save"] is True

    def test_lesson_classification(self, classifier):
        """Test classification of learning experiences."""
        lesson_messages = [
            "I learned that async/await is better than callbacks for this use case",
            "The bug was caused by a race condition in the threading code",
            "Remember to always validate input before processing in the future",
        ]

        for content in lesson_messages:
            message = ConversationMessage(content=content, role="user")
            analysis = classifier.analyze_message(message)

            assert analysis["memory_type"] == "lesson"
            assert analysis["importance_score"] > classifier.importance_threshold
            assert analysis["should_save"] is True

    def test_instruction_classification(self, classifier):
        """Test classification of explicit instructions."""
        instruction_messages = [
            "Always run tests before committing code changes",
            "Use the company coding style guide for all new code",
            "Create documentation for any new API endpoints",
        ]

        for content in instruction_messages:
            message = ConversationMessage(content=content, role="user")
            analysis = classifier.analyze_message(message)

            assert analysis["memory_type"] == "instruction"
            assert analysis["importance_score"] > classifier.importance_threshold
            assert analysis["should_save"] is True

    def test_project_info_classification(self, classifier):
        """Test classification of project-related information."""
        project_messages = [
            "This project uses React 18 with TypeScript for the frontend",
            "The build system is configured with Webpack 5 and Babel",
            "We're following the MVC architecture pattern for this application",
        ]

        for content in project_messages:
            message = ConversationMessage(content=content, role="assistant")
            analysis = classifier.analyze_message(message)

            assert analysis["memory_type"] == "project_info"
            assert analysis["importance_score"] > classifier.importance_threshold
            assert analysis["should_save"] is True

    def test_user_info_classification(self, classifier):
        """Test classification of user information."""
        user_messages = [
            "I'm working on a web application for e-commerce",
            "My main programming languages are Python and JavaScript",
            "I usually work in the Pacific timezone",
        ]

        for content in user_messages:
            message = ConversationMessage(content=content, role="user")
            analysis = classifier.analyze_message(message)

            assert analysis["memory_type"] == "user_info"
            assert analysis["importance_score"] > classifier.importance_threshold
            assert analysis["should_save"] is True

    def test_low_importance_messages(self, classifier):
        """Test that low-importance messages are not saved."""
        low_importance_messages = ["Hi there", "Thanks", "Ok", "Got it", "Sure thing"]

        for content in low_importance_messages:
            message = ConversationMessage(content=content, role="user")
            analysis = classifier.analyze_message(message)

            assert analysis["importance_score"] < classifier.importance_threshold
            assert analysis["should_save"] is False

    def test_short_message_filtering(self, classifier):
        """Test that very short messages are filtered out."""
        short_message = ConversationMessage(content="Yes.", role="user")
        analysis = classifier.analyze_message(short_message)

        assert analysis["should_save"] is False
        assert "too short" in analysis["reasoning"].lower()

    def test_conversation_context_analysis(self, classifier):
        """Test analysis of conversation context for better classification."""
        messages = [
            ConversationMessage(
                content="What's the best way to handle errors?", role="user"
            ),
            ConversationMessage(
                content="Use try-catch blocks with specific exception types. "
                "Always log errors with context for debugging.",
                role="assistant",
            ),
            ConversationMessage(
                content="I'll remember that for my project", role="user"
            ),
        ]

        analysis = classifier.analyze_conversation_context(messages)

        assert len(analysis) == len(messages)
        # The assistant's detailed response should be classified as high importance
        assert analysis[1]["importance_score"] > classifier.importance_threshold
        assert analysis[1]["memory_type"] in ["lesson", "instruction"]

    def test_batch_classification(self, classifier):
        """Test batch processing of multiple messages."""
        messages = [
            ConversationMessage(
                content="I prefer using pytest for testing", role="user"
            ),
            ConversationMessage(
                content="The server runs on port 8080", role="assistant"
            ),
            ConversationMessage(content="Thanks!", role="user"),
        ]

        analyses = classifier.classify_batch(messages)

        assert len(analyses) == len(messages)
        assert analyses[0]["should_save"] is True  # Preference
        assert analyses[1]["should_save"] is True  # Fact
        assert analyses[2]["should_save"] is False  # Low importance

    def test_create_long_term_memory_from_analysis(self, classifier):
        """Test conversion of analysis to LongTermMemory object."""
        message = ConversationMessage(
            content="I always use virtual environments for Python projects", role="user"
        )
        analysis = classifier.analyze_message(message)

        memory = classifier.create_long_term_memory(message, analysis)

        assert isinstance(memory, LongTermMemory)
        assert memory.content == message.content
        assert memory.memory_type == analysis["memory_type"]
        assert memory.importance_score == analysis["importance_score"]
        assert "auto_classified" in memory.tags

    def test_custom_classification_rules(self, classifier):
        """Test adding custom classification rules."""
        custom_rule = {
            "name": "database_rule",
            "patterns": [r"\bdatabase\b", r"\bSQL\b", r"\bMySQL\b"],
            "memory_type": "project_info",
            "importance_boost": 0.2,
        }

        classifier.add_classification_rule(custom_rule)

        message = ConversationMessage(
            content="The database connection uses MySQL with connection pooling",
            role="assistant",
        )
        analysis = classifier.analyze_message(message)

        assert analysis["memory_type"] == "project_info"
        assert analysis["importance_score"] > 0.5  # Should be boosted

    def test_importance_threshold_adjustment(self, classifier):
        """Test adjusting importance threshold."""
        original_threshold = classifier.importance_threshold

        # Lower threshold should save more messages
        classifier.set_importance_threshold(0.1)
        assert classifier.importance_threshold == 0.1

        # Reset to original
        classifier.set_importance_threshold(original_threshold)
        assert classifier.importance_threshold == original_threshold

    def test_classification_statistics(self, classifier):
        """Test getting classification statistics."""
        messages = [
            ConversationMessage(content="I prefer vim over emacs", role="user"),
            ConversationMessage(
                content="The API key is stored in environment variables",
                role="assistant",
            ),
            ConversationMessage(content="Cool", role="user"),
        ]

        analyses = classifier.classify_batch(messages)
        stats = classifier.get_classification_stats(analyses)

        assert "total_messages" in stats
        assert "saved_messages" in stats
        assert "memory_types" in stats
        assert stats["total_messages"] == 3
        assert stats["saved_messages"] == 2

    def test_tag_generation(self, classifier):
        """Test automatic tag generation for classified memories."""
        message = ConversationMessage(
            content="Use pytest fixtures for test setup and dependency injection",
            role="assistant",
        )
        analysis = classifier.analyze_message(message)
        memory = classifier.create_long_term_memory(message, analysis)

        assert "auto_classified" in memory.tags
        assert "pytest" in memory.tags or "testing" in memory.tags
        assert len(memory.tags) >= 2

    def test_error_handling(self, classifier):
        """Test error handling for invalid inputs."""
        # Test with empty message
        empty_message = ConversationMessage(content="", role="user")
        analysis = classifier.analyze_message(empty_message)
        assert analysis["should_save"] is False

        # Test with None content
        with pytest.raises(ValueError):
            classifier.analyze_message(ConversationMessage(content=None, role="user"))
