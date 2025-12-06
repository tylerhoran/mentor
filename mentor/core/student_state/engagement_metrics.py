"""
Track student engagement metrics.

Monitors:
- Session frequency and duration
- Response times
- Interaction patterns
- Activity over time
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any


@dataclass
class SessionMetrics:
    """Metrics for a single tutoring session."""

    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    interaction_count: int = 0
    total_response_time_ms: int = 0
    concepts_covered: list[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        """Get session duration in seconds."""
        if not self.end_time:
            return 0
        return int((self.end_time - self.start_time).total_seconds())

    @property
    def average_response_time_ms(self) -> float | None:
        """Get average response time in milliseconds."""
        if self.interaction_count == 0:
            return None
        return self.total_response_time_ms / self.interaction_count


@dataclass
class EngagementMetrics:
    """Aggregate engagement metrics for a student."""

    total_interactions: int = 0
    total_time_seconds: int = 0
    session_count: int = 0
    average_response_time_ms: float | None = None
    last_session_at: datetime | None = None

    # Additional tracking
    interactions_by_day: dict[str, int] = field(default_factory=dict)
    sessions_by_week: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "total_interactions": self.total_interactions,
            "total_time_seconds": self.total_time_seconds,
            "session_count": self.session_count,
            "average_response_time_ms": self.average_response_time_ms,
            "last_session_at": self.last_session_at.isoformat() if self.last_session_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EngagementMetrics":
        """Create from dictionary."""
        last_session = data.get("last_session_at")
        if isinstance(last_session, str):
            last_session = datetime.fromisoformat(last_session.replace("Z", "+00:00"))

        return cls(
            total_interactions=data.get("total_interactions", 0),
            total_time_seconds=data.get("total_time_seconds", 0),
            session_count=data.get("session_count", 0),
            average_response_time_ms=data.get("average_response_time_ms"),
            last_session_at=last_session,
        )

    @property
    def average_session_length_minutes(self) -> float:
        """Get average session length in minutes."""
        if self.session_count == 0:
            return 0.0
        return (self.total_time_seconds / self.session_count) / 60

    @property
    def total_time_minutes(self) -> float:
        """Get total time in minutes."""
        return self.total_time_seconds / 60


class EngagementTracker:
    """
    Track and analyze student engagement patterns.

    Provides insights into:
    - How frequently the student engages
    - How long sessions typically last
    - Response time patterns
    - Engagement trends over time
    """

    def __init__(self):
        """Initialize the engagement tracker."""
        self._metrics = EngagementMetrics()
        self._current_session: SessionMetrics | None = None
        self._sessions: list[SessionMetrics] = []
        self._response_times: list[int] = []

    def start_session(self, session_id: str) -> None:
        """Start tracking a new session."""
        self._current_session = SessionMetrics(
            session_id=session_id,
            start_time=datetime.now(timezone.utc),
        )
        self._metrics.session_count += 1
        self._metrics.last_session_at = self._current_session.start_time

        # Track weekly sessions
        week_key = self._current_session.start_time.strftime("%Y-W%W")
        self._metrics.sessions_by_week[week_key] = (
            self._metrics.sessions_by_week.get(week_key, 0) + 1
        )

    def end_session(self) -> SessionMetrics | None:
        """End the current session and return metrics."""
        if not self._current_session:
            return None

        self._current_session.end_time = datetime.now(timezone.utc)
        self._metrics.total_time_seconds += self._current_session.duration_seconds

        session = self._current_session
        self._sessions.append(session)
        self._current_session = None

        return session

    def record_interaction(
        self,
        response_time_ms: int | None = None,
        concept_id: str | None = None,
    ) -> None:
        """Record an interaction."""
        self._metrics.total_interactions += 1

        # Track daily interactions
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._metrics.interactions_by_day[today] = (
            self._metrics.interactions_by_day.get(today, 0) + 1
        )

        # Update current session
        if self._current_session:
            self._current_session.interaction_count += 1
            if concept_id and concept_id not in self._current_session.concepts_covered:
                self._current_session.concepts_covered.append(concept_id)

        # Track response time
        if response_time_ms is not None:
            self._response_times.append(response_time_ms)
            if self._current_session:
                self._current_session.total_response_time_ms += response_time_ms

            # Update average
            self._metrics.average_response_time_ms = sum(self._response_times) / len(
                self._response_times
            )

    def get_metrics(self) -> EngagementMetrics:
        """Get current engagement metrics."""
        return self._metrics

    def load_metrics(self, data: dict[str, Any]) -> None:
        """Load metrics from stored data."""
        self._metrics = EngagementMetrics.from_dict(data)

    def get_engagement_score(self) -> float:
        """
        Calculate an overall engagement score (0-100).

        Based on:
        - Session frequency
        - Session duration
        - Interaction count
        - Recency of activity
        """
        score = 0.0

        # Session frequency (up to 25 points)
        # More sessions = higher score
        session_score = min(25, self._metrics.session_count * 2.5)
        score += session_score

        # Session duration (up to 25 points)
        # Average 20+ minutes is ideal
        avg_duration = self._metrics.average_session_length_minutes
        duration_score = min(25, avg_duration * 1.25)
        score += duration_score

        # Interaction count (up to 25 points)
        # More interactions = more engagement
        interaction_score = min(25, self._metrics.total_interactions * 0.25)
        score += interaction_score

        # Recency (up to 25 points)
        # Recent activity scores higher
        if self._metrics.last_session_at:
            days_since = (datetime.now(timezone.utc) - self._metrics.last_session_at).days
            if days_since == 0:
                recency_score = 25
            elif days_since <= 7:
                recency_score = 20
            elif days_since <= 14:
                recency_score = 10
            else:
                recency_score = max(0, 25 - days_since)
            score += recency_score

        return min(100, score)

    def get_activity_trend(self, days: int = 14) -> list[dict[str, Any]]:
        """
        Get activity trend over recent days.

        Args:
            days: Number of days to include

        Returns:
            List of daily activity data
        """
        trend = []
        today = datetime.now(timezone.utc).date()

        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            interactions = self._metrics.interactions_by_day.get(date_str, 0)
            trend.append(
                {
                    "date": date_str,
                    "interactions": interactions,
                }
            )

        return list(reversed(trend))

    def is_active_recently(self, days: int = 7) -> bool:
        """Check if student has been active in the last N days."""
        if not self._metrics.last_session_at:
            return False

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        return self._metrics.last_session_at > cutoff

    def get_response_time_stats(self) -> dict[str, float | None]:
        """Get statistics about response times."""
        if not self._response_times:
            return {
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
            }

        sorted_times = sorted(self._response_times)
        n = len(sorted_times)

        return {
            "mean": sum(sorted_times) / n,
            "median": sorted_times[n // 2],
            "min": min(sorted_times),
            "max": max(sorted_times),
        }
