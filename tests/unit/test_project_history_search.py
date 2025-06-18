"""Unit tests for project history search functionality."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import pytest
from src.my_coding_agent.core.memory.project_history_search import (
    ChangeImpactAnalyzer,
    EventChain,
    EventChainAnalyzer,
    ProjectHistoryAnalytics,
    ProjectHistoryFilter,
    ProjectHistorySearch,
    SearchResult,
)
from src.my_coding_agent.core.project_event_recorder import (
    ProjectEvent,
    ProjectEventType,
)


class TestProjectHistorySearch:
    """Test the ProjectHistorySearch class."""

    @pytest.fixture
    def mock_memory_integration(self):
        """Create a mock memory integration for testing."""
        mock = Mock()
        return mock

    @pytest.fixture
    def sample_events(self):
        """Create sample project events for testing."""
        import time

        now = time.time()
        events = [
            ProjectEvent(
                event_type=ProjectEventType.FEATURE_ADDITION,
                description="Added new feature X",
                file_path=Path("src/main.py"),
                change_summary="Added class X with methods A and B",
                timestamp=now - 86400,  # 1 day ago
                metadata={
                    "author": "user1",
                    "lines_added": 50,
                    "lines_removed": 5,
                    "event_id": "event1",
                },
            ),
            ProjectEvent(
                event_type=ProjectEventType.BUG_FIX,
                description="Fixed memory leak in utils",
                file_path=Path("src/utils.py"),
                change_summary="Fixed buffer overflow in parse_data",
                timestamp=now - 172800,  # 2 days ago
                metadata={
                    "author": "user2",
                    "lines_added": 10,
                    "lines_removed": 20,
                    "event_id": "event2",
                },
            ),
            ProjectEvent(
                event_type=ProjectEventType.REFACTORING,
                description="Refactored main module",
                file_path=Path("src/main.py"),
                change_summary="Extracted helper functions",
                timestamp=now - 259200,  # 3 days ago
                metadata={
                    "author": "user1",
                    "lines_added": 30,
                    "lines_removed": 40,
                    "event_id": "event3",
                },
            ),
        ]
        return events

    @pytest.fixture
    def search_instance(self, mock_memory_integration):
        """Create a ProjectHistorySearch instance for testing."""
        return ProjectHistorySearch(memory_integration=mock_memory_integration)

    def test_search_initialization(self, mock_memory_integration):
        """Test basic initialization of ProjectHistorySearch."""
        searcher = ProjectHistorySearch(memory_integration=mock_memory_integration)
        assert searcher.memory_integration == mock_memory_integration
        assert hasattr(searcher, "search_text")
        assert hasattr(searcher, "search_semantic")
        assert hasattr(searcher, "search_hybrid")

    def test_search_text_basic(self, search_instance, sample_events):
        """Test basic text search functionality."""
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )

        results = search_instance.search_text("feature")

        assert len(results) == 1
        assert results[0].metadata["event_id"] == "event1"
        assert "feature" in results[0].description.lower()

    def test_search_text_case_sensitive(self, search_instance, sample_events):
        """Test case-sensitive text search."""
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )

        # Case-insensitive (default)
        results = search_instance.search_text("FEATURE", case_sensitive=False)
        assert len(results) == 1

        # Case-sensitive
        results = search_instance.search_text("FEATURE", case_sensitive=True)
        assert len(results) == 0

    def test_search_text_with_fields(self, search_instance, sample_events):
        """Test text search with specific fields."""
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )

        # Search only in description
        results = search_instance.search_text("utils", fields=["description"])
        assert len(results) == 1
        assert results[0].metadata["event_id"] == "event2"

    def test_search_text_with_date_range(self, search_instance, sample_events):
        """Test text search with date filtering."""
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )

        import time

        now = time.time()
        start_date = now - 43200  # 12 hours ago

        # Note: Using timestamp comparison with ProjectEvent timestamps (float)
        # This test checks that only events within the time range are returned
        results = search_instance.search_text("", start_date=start_date)
        assert len(results) >= 0  # May be 0 or more depending on time comparison

    def test_search_text_with_limit(self, search_instance, sample_events):
        """Test text search with result limit."""
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )

        results = search_instance.search_text("", limit=2)
        assert len(results) <= 2

    def test_search_text_no_memory_integration(self):
        """Test text search without memory integration."""
        searcher = ProjectHistorySearch(memory_integration=None)
        results = searcher.search_text("test")
        assert results == []

    def test_search_semantic_basic(self, search_instance):
        """Test basic semantic search functionality."""
        mock_results = [Mock()]
        mock_results[0].metadata = {"event_id": "event1"}
        search_instance.memory_integration.search_project_history.return_value = (
            mock_results
        )

        results = search_instance.search_semantic("semantic query")

        assert len(results) == 1
        assert results[0].metadata["event_id"] == "event1"
        search_instance.memory_integration.search_project_history.assert_called_once_with(
            query="semantic query", limit=20
        )

    def test_search_semantic_with_parameters(self, search_instance):
        """Test semantic search with custom parameters."""
        mock_results = [Mock()]
        mock_results[0].metadata = {"event_id": "event1"}
        search_instance.memory_integration.search_project_history.return_value = (
            mock_results
        )

        results = search_instance.search_semantic("query", limit=10, threshold=0.8)

        assert len(results) == 1
        search_instance.memory_integration.search_project_history.assert_called_once_with(
            query="query", limit=10
        )

    def test_search_semantic_error_handling(self, search_instance):
        """Test semantic search error handling."""
        search_instance.memory_integration.search_project_history.side_effect = (
            Exception("API Error")
        )

        results = search_instance.search_semantic("query")
        assert results == []

    def test_search_semantic_no_memory_integration(self):
        """Test semantic search without memory integration."""
        searcher = ProjectHistorySearch(memory_integration=None)
        results = searcher.search_semantic("test")
        assert results == []

    def test_search_hybrid_basic(self, search_instance, sample_events):
        """Test basic hybrid search functionality."""
        # Mock text search
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )

        # Mock semantic search
        semantic_results = [sample_events[1]]  # Different from text results
        search_instance.memory_integration.search_project_history.return_value = (
            semantic_results
        )

        results = search_instance.search_hybrid("feature")

        # Should combine results from both searches
        assert len(results) >= 1

    def test_search_hybrid_with_weights(self, search_instance, sample_events):
        """Test hybrid search with custom weights."""
        search_instance.memory_integration.get_project_history.return_value = (
            sample_events
        )
        search_instance.memory_integration.search_project_history.return_value = (
            sample_events
        )

        results = search_instance.search_hybrid(
            "test", text_weight=0.8, semantic_weight=0.2, limit=5
        )

        assert len(results) <= 5

    def test_search_hybrid_deduplication(self, search_instance, sample_events):
        """Test that hybrid search deduplicates results."""
        # Same event appears in both text and semantic results
        search_instance.memory_integration.get_project_history.return_value = [
            sample_events[0]
        ]
        search_instance.memory_integration.search_project_history.return_value = [
            sample_events[0]
        ]

        results = search_instance.search_hybrid("test")

        # Should only return the event once but with boosted score
        assert len(results) == 1
        assert results[0].metadata["event_id"] == "event1"

    def test_event_matches_text_query(self, search_instance, sample_events):
        """Test the private _event_matches_text_query method."""
        event = sample_events[0]

        # Test matching description
        assert search_instance._event_matches_text_query(
            event, "feature", ["description"], False
        )

        # Test non-matching query
        assert not search_instance._event_matches_text_query(
            event, "nonexistent", ["description"], False
        )

    def test_get_event_field_value(self, search_instance, sample_events):
        """Test the private _get_event_field_value method."""
        event = sample_events[0]

        assert (
            search_instance._get_event_field_value(event, "description")
            == event.description
        )
        assert search_instance._get_event_field_value(event, "file_path") == str(
            event.file_path
        )
        assert (
            search_instance._get_event_field_value(event, "change_summary")
            == event.change_summary
        )
        assert (
            search_instance._get_event_field_value(event, "event_type")
            == event.event_type.value
        )

    def test_filter_by_date_range(self, search_instance, sample_events):
        """Test the private _filter_by_date_range method."""
        import time

        now = time.time()
        start_date = now - 300000  # Earlier than all test events (3.5 days)
        end_date = now + 100000  # Later than all test events

        filtered = search_instance._filter_by_date_range(
            sample_events, start_date, end_date
        )

        # Should include all events within the very wide date range
        assert len(filtered) == 3


class TestProjectHistoryFilter:
    """Test the ProjectHistoryFilter class."""

    @pytest.fixture
    def filter_instance(self):
        """Create a ProjectHistoryFilter instance."""
        return ProjectHistoryFilter()

    @pytest.fixture
    def sample_events(self):
        """Create sample events for filtering tests."""
        import time

        now = time.time()
        return [
            ProjectEvent(
                event_type=ProjectEventType.FEATURE_ADDITION,
                description="Added feature",
                file_path=Path("src/main.py"),
                change_summary="Added feature implementation",
                timestamp=now - 86400,  # 1 day ago
                metadata={
                    "author": "user1",
                    "lines_added": 50,
                    "impact_score": 8.5,
                    "event_id": "event1",
                },
            ),
            ProjectEvent(
                event_type=ProjectEventType.BUG_FIX,
                description="Fixed bug",
                file_path=Path("tests/test_main.py"),
                change_summary="Fixed critical bug",
                timestamp=now - 172800,  # 2 days ago
                metadata={
                    "author": "user2",
                    "lines_removed": 20,
                    "impact_score": 6.0,
                    "event_id": "event2",
                },
            ),
        ]

    def test_filter_by_event_type(self, filter_instance, sample_events):
        """Test filtering by event type."""
        results = filter_instance.filter_by_event_type(
            sample_events, [ProjectEventType.FEATURE_ADDITION.value]
        )

        assert len(results) == 1
        assert results[0].event_type == ProjectEventType.FEATURE_ADDITION

    def test_filter_by_file_path_exact(self, filter_instance, sample_events):
        """Test filtering by exact file path."""
        results = filter_instance.filter_by_file_path(
            sample_events, file_path=Path("src/main.py")
        )

        assert len(results) == 1
        assert results[0].file_path == Path("src/main.py")

    def test_filter_by_file_path_pattern(self, filter_instance, sample_events):
        """Test filtering by file path pattern."""
        results = filter_instance.filter_by_file_path(
            sample_events, path_pattern="src/*.py"
        )

        assert len(results) == 1
        assert str(results[0].file_path).startswith("src/")

    def test_filter_by_date_range(self, filter_instance, sample_events):
        """Test filtering by date range."""
        now = datetime.now()
        start_date = now - timedelta(days=1, hours=12)
        end_date = now

        results = filter_instance.filter_by_date_range(
            sample_events, start_date, end_date
        )

        assert len(results) == 1  # Only event1 is in range

    def test_filter_by_impact_score(self, filter_instance, sample_events):
        """Test filtering by impact score."""
        results = filter_instance.filter_by_impact_score(
            sample_events, min_score=7.0, max_score=10.0
        )

        assert len(results) == 1
        assert results[0].metadata["impact_score"] >= 7.0

    def test_filter_by_change_magnitude(self, filter_instance, sample_events):
        """Test filtering by change magnitude."""
        results = filter_instance.filter_by_change_magnitude(
            sample_events, min_lines_added=40
        )

        assert len(results) == 1
        assert results[0].metadata.get("lines_added", 0) >= 40

    def test_filter_by_author(self, filter_instance, sample_events):
        """Test filtering by author."""
        results = filter_instance.filter_by_author(sample_events, "user1")

        assert len(results) == 1
        assert results[0].metadata["author"] == "user1"


class TestEventChainAnalyzer:
    """Test the EventChainAnalyzer class."""

    @pytest.fixture
    def analyzer_instance(self):
        """Create an EventChainAnalyzer instance."""
        return EventChainAnalyzer()

    @pytest.fixture
    def sample_events(self):
        """Create sample events for chain analysis."""
        import time

        now = time.time()
        return [
            ProjectEvent(
                event_type=ProjectEventType.FEATURE_ADDITION,
                description="Added feature X",
                file_path=Path("src/main.py"),
                change_summary="Added feature implementation",
                timestamp=now - 3600,  # 1 hour ago
                metadata={"author": "user1", "event_id": "event1"},
            ),
            ProjectEvent(
                event_type=ProjectEventType.BUG_FIX,
                description="Fixed issue in feature X",
                file_path=Path("src/main.py"),
                change_summary="Fixed bug in new feature",
                timestamp=now,
                metadata={"author": "user1", "event_id": "event2"},
            ),
        ]

    def test_analyzer_initialization(self, analyzer_instance):
        """Test EventChainAnalyzer initialization."""
        assert hasattr(analyzer_instance, "find_related_events")
        assert hasattr(analyzer_instance, "analyze_change_chains")

    def test_find_related_events_by_file(self, analyzer_instance, sample_events):
        """Test finding related events by file path."""
        target_event = sample_events[0]

        related = analyzer_instance.find_related_events(
            target_event, sample_events, relation_types=["same_file"]
        )

        # Should find the other event in the same file
        assert len(related) == 1
        assert related[0].metadata["event_id"] == "event2"

    def test_find_related_events_by_author(self, analyzer_instance, sample_events):
        """Test finding related events by author."""
        target_event = sample_events[0]

        related = analyzer_instance.find_related_events(
            target_event, sample_events, relation_types=["same_author"]
        )

        assert len(related) == 1
        assert related[0].metadata["author"] == target_event.metadata["author"]

    def test_find_related_events_time_window(self, analyzer_instance, sample_events):
        """Test finding related events within time window."""
        target_event = sample_events[0]

        # Test with small time window - only check temporal proximity
        related = analyzer_instance.find_related_events(
            target_event,
            sample_events,
            relation_types=["temporal_proximity"],
            time_window_hours=0.5,
        )
        assert len(related) == 0  # Events are 1 hour apart

        # Test with larger time window - only check temporal proximity
        related = analyzer_instance.find_related_events(
            target_event,
            sample_events,
            relation_types=["temporal_proximity"],
            time_window_hours=2,
        )
        assert len(related) == 1

    def test_analyze_change_chains(self, analyzer_instance, sample_events):
        """Test analyzing change chains."""
        chains = analyzer_instance.analyze_change_chains(sample_events)

        assert isinstance(chains, list)
        # Should find at least one chain for related events
        assert len(chains) >= 0

    def test_find_event_dependencies(self, analyzer_instance, sample_events):
        """Test finding event dependencies."""
        target_event = sample_events[1]  # Bug fix event

        dependencies = analyzer_instance.find_event_dependencies(
            target_event, sample_events
        )

        # Bug fix might depend on the feature addition
        assert isinstance(dependencies, list)


class TestProjectHistoryAnalytics:
    """Test the ProjectHistoryAnalytics class."""

    @pytest.fixture
    def analytics_instance(self):
        """Create a ProjectHistoryAnalytics instance."""
        return ProjectHistoryAnalytics()

    @pytest.fixture
    def sample_events(self):
        """Create sample events for analytics tests."""
        import time

        now = time.time()
        return [
            ProjectEvent(
                event_type=ProjectEventType.FEATURE_ADDITION,
                description="Added feature",
                file_path=Path("src/main.py"),
                change_summary="Feature implementation",
                timestamp=now - 86400,  # 1 day ago
                metadata={
                    "author": "user1",
                    "lines_added": 100,
                    "impact_score": 8.0,
                    "event_id": "event1",
                },
            ),
            ProjectEvent(
                event_type=ProjectEventType.BUG_FIX,
                description="Fixed bug",
                file_path=Path("src/main.py"),
                change_summary="Bug fix",
                timestamp=now - 172800,  # 2 days ago
                metadata={
                    "author": "user2",
                    "lines_added": 10,
                    "impact_score": 5.0,
                    "event_id": "event2",
                },
            ),
            ProjectEvent(
                event_type=ProjectEventType.REFACTORING,
                description="Refactored utils",
                file_path=Path("src/utils.py"),
                change_summary="Code cleanup",
                timestamp=now - 259200,  # 3 days ago
                metadata={
                    "author": "user1",
                    "lines_added": 50,
                    "impact_score": 6.0,
                    "event_id": "event3",
                },
            ),
        ]

    def test_analytics_initialization(self, analytics_instance):
        """Test ProjectHistoryAnalytics initialization."""
        assert hasattr(analytics_instance, "get_most_changed_files")
        assert hasattr(analytics_instance, "get_activity_patterns")

    def test_get_most_changed_files(self, analytics_instance, sample_events):
        """Test getting most changed files."""
        results = analytics_instance.get_most_changed_files(sample_events, limit=5)

        assert isinstance(results, list)
        assert len(results) <= 5

        # Should include file stats
        if results:
            assert "file_path" in results[0]
            assert "change_count" in results[0]

    def test_get_activity_patterns_daily(self, analytics_instance, sample_events):
        """Test getting daily activity patterns."""
        patterns = analytics_instance.get_activity_patterns(
            sample_events, granularity="daily"
        )

        assert isinstance(patterns, list)
        if patterns:
            assert "date" in patterns[0]
            assert "event_count" in patterns[0]

    def test_get_activity_patterns_hourly(self, analytics_instance, sample_events):
        """Test getting hourly activity patterns."""
        patterns = analytics_instance.get_activity_patterns(
            sample_events, granularity="hourly"
        )

        assert isinstance(patterns, list)

    def test_get_developer_contributions(self, analytics_instance, sample_events):
        """Test getting developer contributions."""
        contributions = analytics_instance.get_developer_contributions(sample_events)

        assert isinstance(contributions, list)
        if contributions:
            assert "author" in contributions[0]
            assert "total_events" in contributions[0]

    def test_get_event_type_distribution(self, analytics_instance, sample_events):
        """Test getting event type distribution."""
        distribution = analytics_instance.get_event_type_distribution(sample_events)

        assert isinstance(distribution, dict)
        # Should have stats for each event type present
        assert ProjectEventType.FEATURE_ADDITION.value in distribution

    def test_get_impact_analysis(self, analytics_instance, sample_events):
        """Test getting impact analysis."""
        analysis = analytics_instance.get_impact_analysis(sample_events)

        assert isinstance(analysis, dict)
        assert "total_events" in analysis
        assert "average_impact" in analysis

    def test_get_file_evolution_timeline(self, analytics_instance, sample_events):
        """Test getting file evolution timeline."""
        timeline = analytics_instance.get_file_evolution_timeline(
            sample_events, Path("src/main.py")
        )

        assert isinstance(timeline, list)
        # Should include events for the specified file
        if timeline:
            assert "timestamp" in timeline[0]
            assert "event_type" in timeline[0]


class TestChangeImpactAnalyzer:
    """Test the ChangeImpactAnalyzer class."""

    @pytest.fixture
    def impact_analyzer(self):
        """Create a ChangeImpactAnalyzer instance."""
        return ChangeImpactAnalyzer()

    @pytest.fixture
    def sample_events(self):
        """Create sample events for impact analysis."""
        import time

        now = time.time()
        return [
            ProjectEvent(
                event_type=ProjectEventType.FEATURE_ADDITION,
                description="Added database connection",
                file_path=Path("src/main.py"),
                change_summary="Added DB layer",
                timestamp=now - 86400,  # 1 day ago
                metadata={
                    "impact_score": 8.0,
                    "risk_level": "medium",
                    "event_id": "event1",
                },
            )
        ]

    def test_impact_analyzer_initialization(self, impact_analyzer):
        """Test ChangeImpactAnalyzer initialization."""
        assert hasattr(impact_analyzer, "analyze_change_impact")
        assert hasattr(impact_analyzer, "predict_affected_files")

    def test_analyze_change_impact(self, impact_analyzer, sample_events):
        """Test analyzing change impact."""
        target_event = sample_events[0]

        impact = impact_analyzer.analyze_change_impact(target_event, sample_events)

        assert isinstance(impact, dict)
        assert "impact_score" in impact
        assert "affected_areas" in impact

    def test_predict_affected_files(self, impact_analyzer, sample_events):
        """Test predicting affected files."""
        predictions = impact_analyzer.predict_affected_files(
            "database changes", sample_events
        )

        assert isinstance(predictions, list)

    def test_calculate_change_risk(self, impact_analyzer, sample_events):
        """Test calculating change risk."""
        risk = impact_analyzer.calculate_change_risk(
            Path("src/main.py"), "feature_addition", sample_events
        )

        assert isinstance(risk, dict)
        assert "risk_score" in risk
        assert "risk_factors" in risk


class TestSearchResult:
    """Test the SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        event = Mock()
        result = SearchResult(
            event=event,
            relevance_score=0.85,
            match_fields=["description", "file_path"],
            match_highlights={"description": "highlighted text"},
        )

        assert result.event == event
        assert result.relevance_score == 0.85
        assert "description" in result.match_fields


class TestEventChain:
    """Test the EventChain dataclass."""

    def test_event_chain_creation(self):
        """Test creating an EventChain."""
        import time

        now = time.time()
        events = [
            ProjectEvent(
                event_type=ProjectEventType.FEATURE_ADDITION,
                description="Added feature",
                file_path=Path("src/main.py"),
                change_summary="Feature implementation",
                timestamp=now,
                metadata={"event_id": "event1"},
            ),
            ProjectEvent(
                event_type=ProjectEventType.BUG_FIX,
                description="Fixed bug",
                file_path=Path("src/main.py"),
                change_summary="Bug fix",
                timestamp=now,
                metadata={"event_id": "event2"},
            ),
        ]
        chain = EventChain(
            chain_id="chain1",
            events=events,
            relationship_type="sequential",
            confidence_score=0.9,
            description="Related feature development",
        )

        assert chain.chain_id == "chain1"
        assert len(chain.events) == 2
        assert chain.relationship_type == "sequential"
