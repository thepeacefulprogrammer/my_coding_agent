"""
Automated memory classification system for determining what should be saved as long-term memory.

This module provides intelligent classification of conversation messages to automatically
determine their importance and appropriate memory type for long-term storage.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from .memory_types import ConversationMessage, LongTermMemory

logger = logging.getLogger(__name__)


class MemoryClassifier:
    """Automated classifier for determining memory importance and type."""

    def __init__(self, importance_threshold: float = 0.3, min_content_length: int = 20):
        """Initialize the memory classifier.

        Args:
            importance_threshold: Minimum importance score for saving (0.0-1.0)
            min_content_length: Minimum content length to consider for saving
        """
        self.importance_threshold = importance_threshold
        self.min_content_length = min_content_length
        self.classification_rules = self._initialize_classification_rules()

        logger.info(
            f"MemoryClassifier initialized with threshold {importance_threshold}"
        )

    def _initialize_classification_rules(self) -> list[dict[str, Any]]:
        """Initialize the classification rules for different memory types."""
        return [
            # User Preferences
            {
                "name": "preference",
                "patterns": [
                    r"\b(I prefer|I like|I want|I choose)\b",
                    r"\b(prefer|like|want|choose|favorite|better|best)\b",
                    r"\b(please always|please use|I usually|I typically|I generally)\b",
                    r"\buse\s+.+\s+instead\s+of\b",
                    r"\b(setting|option|configuration)\s+(I|that I)\b",
                ],
                "memory_type": "preference",
                "base_importance": 0.65,  # Higher than instruction
                "role_boost": {"user": 0.2, "assistant": 0.0},
            },
            # Factual Information
            {
                "name": "fact",
                "patterns": [
                    r"\b(database|server|API|endpoint|URL|port|version)\b",
                    r"\b(configuration|config|setting|parameter)\b",
                    r"\b(located|hosted|stored|running|using)\b",
                    r"\b(file|path|directory|folder)\b",
                    r"\bhttps?://\S+",
                    r"\b\w+\.\w+\.\w+\b",  # Version numbers
                ],
                "memory_type": "fact",
                "base_importance": 0.5,
                "role_boost": {"assistant": 0.2, "user": 0.1},
            },
            # Learning Experiences
            {
                "name": "lesson",
                "patterns": [
                    r"\b(learn(ed)?|discovered|found out|realized|understood)\b",
                    r"\b(bug|issue|problem|error|mistake).*(was|caused|due|because)\b",
                    r"\b(better|worse).*(than|for|in)\b",
                    r"\b(remember|note).*(future|next time|always|never)\b",
                    r"\b(experience|lesson|insight)\b",
                ],
                "memory_type": "lesson",
                "base_importance": 0.7,  # Higher importance than preferences
                "role_boost": {"user": 0.2, "assistant": 0.1},
            },
            # Instructions and Guidelines
            {
                "name": "instruction",
                "patterns": [
                    r"\b(always|never)\s+(run|create|add|implement|use|validate|log|check)\b",
                    r"\b(should|must|need to|have to)\s+",
                    r"\b(rule|guideline|standard|practice|convention|style guide)\b",
                    r"\bbefore\s+(commit|deploy|release|push|committing)\b",
                    r"\b(create|add)\s+(documentation|comment|test)",
                    r"\buse\s+.*(guide|standard|practice)\b",
                ],
                "memory_type": "instruction",
                "base_importance": 0.6,  # Higher than fact
                "role_boost": {"user": 0.2, "assistant": 0.1},
            },
            # Project Information
            {
                "name": "project_info",
                "patterns": [
                    r"\b(project|application|app|system|software)\b",
                    r"\b(architecture|pattern|structure|design)\b",
                    r"\b(framework|library|technology|tool)\b",
                    r"\b(build|deployment|CI/CD|pipeline)\b",
                    r"\b(React|Vue|Angular|Python|JavaScript|TypeScript)\b",
                    r"\b(Docker|Kubernetes|AWS|Azure|GCP)\b",
                ],
                "memory_type": "project_info",
                "base_importance": 0.4,
                "role_boost": {"assistant": 0.2, "user": 0.1},
            },
            # User Information
            {
                "name": "user_info",
                "patterns": [
                    r"\b(I'm|I am)\s+(working|developing|building|creating)\b",
                    r"\b(my|My)\s+(main|primary|favorite)\s+(programming\s+)?(languages?|skills?)\b",
                    r"\b(I usually|I typically|I generally|I normally)\s+(work|code|develop)\b",
                    r"\b(timezone|location|availability|schedule)\b",
                    r"\b(my|My)\s+(team|company|organization|background|experience)\b",
                ],
                "memory_type": "user_info",
                "base_importance": 0.6,  # Even higher than project_info
                "role_boost": {"user": 0.2, "assistant": 0.0},
            },
        ]

    def analyze_message(self, message: ConversationMessage) -> dict[str, Any]:
        """Analyze a conversation message and determine if it should be stored.

        Args:
            message: ConversationMessage to analyze

        Returns:
            Dictionary containing analysis results
        """
        if message.content is None:
            raise ValueError("Message content cannot be None")

        if not message.content.strip():
            return {
                "importance_score": 0.0,
                "memory_type": "unknown",
                "should_save": False,
                "reasoning": "Message content is empty",
                "matched_patterns": [],
            }

        # Check minimum length
        if len(message.content) < self.min_content_length:
            return {
                "importance_score": 0.0,
                "memory_type": "unknown",
                "should_save": False,
                "reasoning": "Message too short to be meaningful",
                "matched_patterns": [],
            }

        # Check for low-importance patterns
        if self._is_low_importance(message.content):
            return {
                "importance_score": 0.1,
                "memory_type": "unknown",
                "should_save": False,
                "reasoning": "Low importance greeting/acknowledgment",
                "matched_patterns": [],
            }

        # Find best matching rule
        best_match = self._find_best_classification_rule(message)

        importance_score = self._calculate_importance_score(message, best_match)
        should_save = importance_score >= self.importance_threshold

        return {
            "importance_score": importance_score,
            "memory_type": best_match["memory_type"],
            "should_save": should_save,
            "reasoning": self._generate_reasoning(
                message, best_match, importance_score
            ),
            "matched_patterns": best_match["matched_patterns"],
        }

    def _is_low_importance(self, content: str) -> bool:
        """Check if content is a low-importance message."""
        low_importance_patterns = [
            r"^(hi|hello|hey|thanks?|thank you|ok|okay|sure|yes|no|got it|cool|nice)\.?$",
            r"^(that's|that is)\s+(good|great|fine|ok|okay)\.?$",
            r"^(sounds|looks)\s+(good|great|fine)\.?$",
        ]

        content_lower = content.lower().strip()
        return any(
            re.match(pattern, content_lower, re.IGNORECASE)
            for pattern in low_importance_patterns
        )

    def _find_best_classification_rule(
        self, message: ConversationMessage
    ) -> dict[str, Any]:
        """Find the best matching classification rule for a message."""
        best_match = {
            "memory_type": "fact",  # Default fallback
            "base_importance": 0.2,
            "role_boost": {},
            "matched_patterns": [],
            "pattern_count": 0,
            "rule_score": 0.0,
        }

        for rule in self.classification_rules:
            matched_patterns = []
            pattern_count = 0

            for pattern in rule["patterns"]:
                if re.search(pattern, message.content, re.IGNORECASE):
                    matched_patterns.append(pattern)
                    pattern_count += 1

            if pattern_count > 0:
                # Calculate rule score: base importance + pattern bonus
                rule_score = rule["base_importance"] + (pattern_count * 0.1)

                if rule_score > best_match["rule_score"]:
                    best_match.update(
                        {
                            "memory_type": rule["memory_type"],
                            "base_importance": rule["base_importance"],
                            "role_boost": rule["role_boost"],
                            "matched_patterns": matched_patterns,
                            "pattern_count": pattern_count,
                            "rule_score": rule_score,
                        }
                    )

        return best_match

    def _calculate_importance_score(
        self, message: ConversationMessage, rule_match: dict[str, Any]
    ) -> float:
        """Calculate the importance score for a message."""
        base_score = rule_match["base_importance"]

        # Apply role-based boost
        role_boost = rule_match["role_boost"].get(message.role, 0.0)

        # Length boost for detailed messages
        length_boost = min(0.2, len(message.content) / 1000)

        # Pattern match boost
        pattern_boost = min(0.2, rule_match["pattern_count"] * 0.05)

        # Combine all factors
        importance_score = base_score + role_boost + length_boost + pattern_boost

        return min(1.0, max(0.0, importance_score))

    def _generate_reasoning(
        self,
        message: ConversationMessage,
        rule_match: dict[str, Any],
        importance_score: float,
    ) -> str:
        """Generate human-readable reasoning for the classification."""
        reasoning_parts = [
            f"Classified as {rule_match['memory_type']} based on content patterns",
            f"Importance score: {importance_score:.2f}",
        ]

        if rule_match["matched_patterns"]:
            reasoning_parts.append(
                f"Matched {len(rule_match['matched_patterns'])} classification patterns"
            )

        if message.role == "user":
            reasoning_parts.append("User message adds personal context")
        elif message.role == "assistant":
            reasoning_parts.append("Assistant message provides information")

        return "; ".join(reasoning_parts)

    def analyze_conversation_context(
        self, messages: list[ConversationMessage]
    ) -> list[dict[str, Any]]:
        """Analyze messages with conversation context for better classification."""
        analyses = []

        for i, message in enumerate(messages):
            analysis = self.analyze_message(message)

            # Context boost for messages that are part of important conversations
            if i > 0 and analyses[-1]["importance_score"] > 0.5:
                analysis["importance_score"] = min(
                    1.0, analysis["importance_score"] + 0.1
                )
                analysis["reasoning"] += (
                    "; Context boost from previous important message"
                )

            analyses.append(analysis)

        return analyses

    def classify_batch(
        self, messages: list[ConversationMessage]
    ) -> list[dict[str, Any]]:
        """Classify a batch of messages efficiently."""
        return [self.analyze_message(message) for message in messages]

    def create_long_term_memory(
        self, message: ConversationMessage, analysis: dict[str, Any]
    ) -> LongTermMemory:
        """Create a LongTermMemory object from message and analysis."""
        tags = ["auto_classified", analysis["memory_type"]]

        # Add content-based tags
        content_tags = self._extract_content_tags(message.content)
        tags.extend(content_tags)

        return LongTermMemory(
            content=message.content,
            memory_type=analysis["memory_type"],
            importance_score=analysis["importance_score"],
            tags=tags,
            embedding=None,  # Will be generated when needed
            metadata={
                "original_role": message.role,
                "classification_reasoning": analysis["reasoning"],
                "matched_patterns": analysis["matched_patterns"],
                "auto_classified": True,
            },
        )

    def _extract_content_tags(self, content: str) -> list[str]:
        """Extract relevant tags from content."""
        tags = []

        # Technology tags
        tech_patterns = {
            "python": r"\bpython\b",
            "javascript": r"\bjavascript\b",
            "react": r"\breact\b",
            "docker": r"\bdocker\b",
            "database": r"\b(database|db|sql|mysql|postgresql)\b",
            "api": r"\b(api|endpoint|rest|graphql)\b",
            "testing": r"\b(test|testing|pytest|jest)\b",
            "git": r"\b(git|github|gitlab|commit|branch)\b",
        }

        for tag, pattern in tech_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                tags.append(tag)

        return tags[:5]  # Limit to top 5 tags

    def add_classification_rule(self, rule: dict[str, Any]) -> None:
        """Add a custom classification rule."""
        required_fields = ["name", "patterns", "memory_type", "importance_boost"]
        if not all(field in rule for field in required_fields):
            raise ValueError(f"Rule must contain fields: {required_fields}")

        # Convert importance_boost to proper rule format
        custom_rule = {
            "name": rule["name"],
            "patterns": rule["patterns"],
            "memory_type": rule["memory_type"],
            "base_importance": 0.3 + rule["importance_boost"],
            "role_boost": {"user": 0.1, "assistant": 0.1},
        }

        self.classification_rules.append(custom_rule)
        logger.info(f"Added custom classification rule: {rule['name']}")

    def set_importance_threshold(self, threshold: float) -> None:
        """Set the importance threshold for saving memories."""
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Importance threshold must be between 0.0 and 1.0")

        self.importance_threshold = threshold
        logger.info(f"Updated importance threshold to {threshold}")

    def get_classification_stats(
        self, analyses: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Get statistics about classification results."""
        total_messages = len(analyses)
        saved_messages = sum(1 for analysis in analyses if analysis["should_save"])

        memory_types = {}
        for analysis in analyses:
            if analysis["should_save"]:
                memory_type = analysis["memory_type"]
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1

        return {
            "total_messages": total_messages,
            "saved_messages": saved_messages,
            "save_rate": saved_messages / total_messages if total_messages > 0 else 0.0,
            "memory_types": memory_types,
            "average_importance": sum(a["importance_score"] for a in analyses)
            / total_messages
            if total_messages > 0
            else 0.0,
        }
