"""Tests for analytics schemas."""

from datetime import UTC, datetime

from mentor.schemas.analytics import (
    ClassOverview,
    ConceptStruggle,
    EngagementStats,
    MasteryDistribution,
    ProgressTimeline,
    StudentProgressResponse,
    StudentSummary,
    TimeSeriesDataPoint,
)


class TestEngagementStats:
    """Tests for EngagementStats schema."""

    def test_engagement_stats_creation(self):
        """Test creating engagement stats."""
        now = datetime.now(UTC)
        stats = EngagementStats(
            total_interactions=100,
            total_time_minutes=120.5,
            average_session_length_minutes=24.1,
            session_count=5,
            average_response_time_ms=3500,
            last_active=now,
        )

        assert stats.total_interactions == 100
        assert stats.total_time_minutes == 120.5
        assert stats.session_count == 5

    def test_engagement_stats_optional_fields(self):
        """Test optional fields can be None."""
        stats = EngagementStats(
            total_interactions=0,
            total_time_minutes=0,
            average_session_length_minutes=0,
            session_count=0,
            average_response_time_ms=None,
            last_active=None,
        )

        assert stats.average_response_time_ms is None
        assert stats.last_active is None


class TestMasteryDistribution:
    """Tests for MasteryDistribution schema."""

    def test_mastery_distribution(self):
        """Test mastery distribution schema."""
        dist = MasteryDistribution(
            concept_id="concept-123",
            concept_name="Variables",
            mastery_buckets={"0-20": 2, "20-40": 5, "40-60": 10, "60-80": 8, "80-100": 5},
            average_mastery=0.58,
            student_count=30,
        )

        assert dist.concept_name == "Variables"
        assert dist.mastery_buckets["40-60"] == 10
        assert dist.average_mastery == 0.58


class TestStudentSummary:
    """Tests for StudentSummary schema."""

    def test_student_summary(self):
        """Test student summary schema."""
        now = datetime.now(UTC)
        engagement = EngagementStats(
            total_interactions=50,
            total_time_minutes=60,
            average_session_length_minutes=20,
            session_count=3,
            average_response_time_ms=4000,
            last_active=now,
        )

        summary = StudentSummary(
            student_id="student-123",
            student_name="John Doe",
            overall_mastery=0.75,
            concepts_completed=5,
            total_concepts=8,
            engagement=engagement,
            has_gaming_flags=False,
            high_severity_flags=0,
            last_interaction=now,
        )

        assert summary.student_name == "John Doe"
        assert summary.overall_mastery == 0.75
        assert summary.concepts_completed == 5

    def test_student_summary_with_gaming_flags(self):
        """Test student with gaming flags."""
        engagement = EngagementStats(
            total_interactions=20,
            total_time_minutes=30,
            average_session_length_minutes=15,
            session_count=2,
            average_response_time_ms=1000,
            last_active=None,
        )

        summary = StudentSummary(
            student_id="student-456",
            student_name=None,
            overall_mastery=0.95,
            concepts_completed=8,
            total_concepts=8,
            engagement=engagement,
            has_gaming_flags=True,
            high_severity_flags=3,
            last_interaction=None,
        )

        assert summary.has_gaming_flags is True
        assert summary.high_severity_flags == 3


class TestConceptStruggle:
    """Tests for ConceptStruggle schema."""

    def test_concept_struggle(self):
        """Test concept struggle schema."""
        struggle = ConceptStruggle(
            concept_id="concept-123",
            concept_name="Recursion",
            struggle_rate=0.45,
            common_misconceptions=["infinite recursion", "missing base case"],
            average_time_to_mastery_minutes=90.0,
        )

        assert struggle.struggle_rate == 0.45
        assert len(struggle.common_misconceptions) == 2

    def test_concept_struggle_no_time(self):
        """Test concept with no mastery time data."""
        struggle = ConceptStruggle(
            concept_id="concept-123",
            concept_name="New Concept",
            struggle_rate=0.0,
            common_misconceptions=[],
            average_time_to_mastery_minutes=None,
        )

        assert struggle.average_time_to_mastery_minutes is None


class TestClassOverview:
    """Tests for ClassOverview schema."""

    def test_class_overview(self):
        """Test class overview schema."""
        now = datetime.now(UTC)
        engagement = EngagementStats(
            total_interactions=500,
            total_time_minutes=1200,
            average_session_length_minutes=25,
            session_count=48,
            average_response_time_ms=3500,
            last_active=now,
        )

        mastery_dist = [
            MasteryDistribution(
                concept_id="c1",
                concept_name="Variables",
                mastery_buckets={"0-20": 0, "80-100": 30},
                average_mastery=0.85,
                student_count=30,
            )
        ]

        struggling = [
            ConceptStruggle(
                concept_id="c2",
                concept_name="Recursion",
                struggle_rate=0.4,
                common_misconceptions=["base case"],
                average_time_to_mastery_minutes=60.0,
            )
        ]

        overview = ClassOverview(
            course_id="course-123",
            course_name="Python 101",
            total_students=35,
            active_students=30,
            average_mastery=0.72,
            mastery_distribution=mastery_dist,
            engagement=engagement,
            struggling_concepts=struggling,
            students_with_gaming_flags=2,
            completion_rate=0.65,
            generated_at=now,
        )

        assert overview.total_students == 35
        assert overview.active_students == 30
        assert overview.students_with_gaming_flags == 2
        assert overview.completion_rate == 0.65


class TestStudentProgressResponse:
    """Tests for StudentProgressResponse schema."""

    def test_student_progress(self):
        """Test student progress response schema."""
        now = datetime.now(UTC)
        engagement = EngagementStats(
            total_interactions=75,
            total_time_minutes=90,
            average_session_length_minutes=22.5,
            session_count=4,
            average_response_time_ms=4000,
            last_active=now,
        )

        progress = StudentProgressResponse(
            student_id="student-123",
            student_name="Jane Smith",
            course_id="course-456",
            enrolled_at=now,
            study_condition="treatment_a",
            overall_mastery=0.78,
            concept_mastery={
                "c1": {"estimate": 0.9, "confidence": 0.85},
                "c2": {"estimate": 0.6, "confidence": 0.7},
            },
            concepts_completed=["c1"],
            current_concept_id="c2",
            engagement=engagement,
            gaming_flags=[],
            trajectory_classification="genuine",
            pending_verification=False,
            last_verification=None,
        )

        assert progress.overall_mastery == 0.78
        assert progress.study_condition == "treatment_a"
        assert progress.trajectory_classification == "genuine"


class TestTimeSeriesDataPoint:
    """Tests for TimeSeriesDataPoint schema."""

    def test_time_series_data_point(self):
        """Test time series data point."""
        now = datetime.now(UTC)
        point = TimeSeriesDataPoint(timestamp=now, value=0.75)

        assert point.value == 0.75


class TestProgressTimeline:
    """Tests for ProgressTimeline schema."""

    def test_progress_timeline(self):
        """Test progress timeline schema."""
        now = datetime.now(UTC)
        mastery_points = [
            TimeSeriesDataPoint(timestamp=now, value=0.5),
            TimeSeriesDataPoint(timestamp=now, value=0.65),
            TimeSeriesDataPoint(timestamp=now, value=0.78),
        ]

        interaction_points = [
            TimeSeriesDataPoint(timestamp=now, value=10),
            TimeSeriesDataPoint(timestamp=now, value=15),
            TimeSeriesDataPoint(timestamp=now, value=8),
        ]

        timeline = ProgressTimeline(
            student_id="student-123",
            course_id="course-456",
            mastery_over_time=mastery_points,
            interactions_per_day=interaction_points,
            concept_completions=[
                {"concept_id": "c1", "completed_at": now.isoformat()},
                {"concept_id": "c2", "completed_at": now.isoformat()},
            ],
        )

        assert len(timeline.mastery_over_time) == 3
        assert len(timeline.interactions_per_day) == 3
        assert len(timeline.concept_completions) == 2
