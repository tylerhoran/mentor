"""Tests for the engagement metrics module."""

from datetime import UTC, datetime, timedelta

from mentor.core.student_state.engagement_metrics import (
    EngagementMetrics,
    EngagementTracker,
    SessionMetrics,
)


class TestSessionMetrics:
    """Tests for SessionMetrics dataclass."""

    def test_creation(self):
        """Test creating session metrics."""
        now = datetime.now(UTC)
        metrics = SessionMetrics(
            session_id="session-1",
            start_time=now,
        )
        assert metrics.session_id == "session-1"
        assert metrics.start_time == now
        assert metrics.end_time is None
        assert metrics.interaction_count == 0

    def test_duration_seconds(self):
        """Test calculating duration."""
        start = datetime.now(UTC)
        end = start + timedelta(minutes=5)

        metrics = SessionMetrics(
            session_id="session-1",
            start_time=start,
            end_time=end,
        )
        assert metrics.duration_seconds == 300

    def test_duration_seconds_no_end(self):
        """Test duration with no end time."""
        metrics = SessionMetrics(
            session_id="session-1",
            start_time=datetime.now(UTC),
        )
        assert metrics.duration_seconds == 0

    def test_average_response_time(self):
        """Test calculating average response time."""
        metrics = SessionMetrics(
            session_id="session-1",
            start_time=datetime.now(UTC),
            interaction_count=4,
            total_response_time_ms=2000,
        )
        assert metrics.average_response_time_ms == 500.0

    def test_average_response_time_no_interactions(self):
        """Test average response time with no interactions."""
        metrics = SessionMetrics(
            session_id="session-1",
            start_time=datetime.now(UTC),
            interaction_count=0,
        )
        assert metrics.average_response_time_ms is None


class TestEngagementMetrics:
    """Tests for EngagementMetrics dataclass."""

    def test_creation(self):
        """Test creating engagement metrics."""
        metrics = EngagementMetrics(
            total_interactions=100,
            total_time_seconds=3600,
            session_count=5,
        )
        assert metrics.total_interactions == 100
        assert metrics.total_time_seconds == 3600
        assert metrics.session_count == 5

    def test_default_values(self):
        """Test default values."""
        metrics = EngagementMetrics()
        assert metrics.total_interactions == 0
        assert metrics.total_time_seconds == 0
        assert metrics.session_count == 0
        assert metrics.average_response_time_ms is None
        assert metrics.last_session_at is None

    def test_average_session_length_minutes(self):
        """Test average session length calculation."""
        metrics = EngagementMetrics(
            total_time_seconds=1800,  # 30 minutes
            session_count=3,
        )
        assert metrics.average_session_length_minutes == 10.0

    def test_average_session_length_no_sessions(self):
        """Test average session length with no sessions."""
        metrics = EngagementMetrics()
        assert metrics.average_session_length_minutes == 0.0

    def test_to_dict(self):
        """Test serialization to dict."""
        now = datetime.now(UTC)
        metrics = EngagementMetrics(
            total_interactions=50,
            total_time_seconds=1800,
            session_count=2,
            average_response_time_ms=500.0,
            last_session_at=now,
        )
        d = metrics.to_dict()
        assert d["total_interactions"] == 50
        assert d["total_time_seconds"] == 1800
        assert d["session_count"] == 2
        assert d["average_response_time_ms"] == 500.0
        assert d["last_session_at"] is not None

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "total_interactions": 100,
            "total_time_seconds": 3600,
            "session_count": 5,
            "average_response_time_ms": 450.0,
            "last_session_at": "2024-01-01T12:00:00+00:00",
        }
        metrics = EngagementMetrics.from_dict(data)
        assert metrics.total_interactions == 100
        assert metrics.total_time_seconds == 3600
        assert metrics.session_count == 5
        assert metrics.average_response_time_ms == 450.0


class TestEngagementTracker:
    """Tests for EngagementTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = EngagementTracker()
        assert tracker._current_session is None
        assert tracker._sessions == []

    def test_start_session(self):
        """Test starting a session."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")

        assert tracker._current_session is not None
        assert tracker._current_session.session_id == "session-1"
        assert tracker._metrics.session_count == 1

    def test_end_session(self):
        """Test ending a session."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")

        session = tracker.end_session()
        assert session is not None
        assert session.session_id == "session-1"
        assert session.end_time is not None
        assert tracker._current_session is None

    def test_end_session_no_active(self):
        """Test ending session when none is active."""
        tracker = EngagementTracker()
        result = tracker.end_session()
        assert result is None

    def test_record_interaction(self):
        """Test recording an interaction."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")
        tracker.record_interaction(response_time_ms=500)

        assert tracker._metrics.total_interactions == 1
        assert tracker._current_session.interaction_count == 1

    def test_record_interaction_with_concept(self):
        """Test recording interaction with concept."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")
        tracker.record_interaction(concept_id="concept-1")
        tracker.record_interaction(concept_id="concept-1")  # Same concept
        tracker.record_interaction(concept_id="concept-2")

        assert len(tracker._current_session.concepts_covered) == 2

    def test_record_multiple_interactions(self):
        """Test recording multiple interactions."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")

        tracker.record_interaction(response_time_ms=100)
        tracker.record_interaction(response_time_ms=200)
        tracker.record_interaction(response_time_ms=300)

        assert tracker._metrics.total_interactions == 3
        assert tracker._current_session.total_response_time_ms == 600

    def test_get_metrics(self):
        """Test getting metrics."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")
        tracker.record_interaction()
        tracker.end_session()

        metrics = tracker.get_metrics()
        assert metrics.total_interactions == 1
        assert metrics.session_count == 1

    def test_get_engagement_score(self):
        """Test calculating engagement score."""
        tracker = EngagementTracker()
        # Add some activity
        tracker.start_session("session-1")
        for _ in range(10):
            tracker.record_interaction()
        tracker.end_session()

        score = tracker.get_engagement_score()
        assert 0 <= score <= 100

    def test_get_engagement_score_empty(self):
        """Test engagement score with no activity."""
        tracker = EngagementTracker()
        score = tracker.get_engagement_score()
        assert score == 0.0

    def test_is_active_recently_true(self):
        """Test is_active_recently when active."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")
        tracker.end_session()

        assert tracker.is_active_recently(days=7) is True

    def test_is_active_recently_false(self):
        """Test is_active_recently when not active."""
        tracker = EngagementTracker()
        assert tracker.is_active_recently(days=7) is False

    def test_get_response_time_stats(self):
        """Test getting response time statistics."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")
        tracker.record_interaction(response_time_ms=100)
        tracker.record_interaction(response_time_ms=200)
        tracker.record_interaction(response_time_ms=300)

        stats = tracker.get_response_time_stats()
        assert stats["mean"] == 200.0
        assert stats["min"] == 100
        assert stats["max"] == 300

    def test_get_response_time_stats_empty(self):
        """Test response time stats with no data."""
        tracker = EngagementTracker()
        stats = tracker.get_response_time_stats()
        assert stats["mean"] is None
        assert stats["median"] is None

    def test_get_activity_trend(self):
        """Test getting activity trend."""
        tracker = EngagementTracker()
        tracker.start_session("session-1")
        tracker.record_interaction()
        tracker.record_interaction()

        trend = tracker.get_activity_trend(days=7)
        assert len(trend) == 7
        # Most recent day should have 2 interactions
        assert trend[-1]["interactions"] == 2

    def test_load_metrics(self):
        """Test loading metrics from dict."""
        tracker = EngagementTracker()
        data = {
            "total_interactions": 50,
            "total_time_seconds": 1800,
            "session_count": 3,
        }
        tracker.load_metrics(data)

        metrics = tracker.get_metrics()
        assert metrics.total_interactions == 50
        assert metrics.session_count == 3
