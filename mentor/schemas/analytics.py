"""Analytics schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EngagementStats(BaseModel):
    """Engagement statistics for a student or class."""

    total_interactions: int
    total_time_minutes: float
    average_session_length_minutes: float
    session_count: int
    average_response_time_ms: float | None
    last_active: datetime | None


class MasteryDistribution(BaseModel):
    """Distribution of mastery levels for a concept."""

    concept_id: str
    concept_name: str
    mastery_buckets: dict[str, int]  # e.g., {"0-20": 5, "20-40": 10, ...}
    average_mastery: float
    student_count: int


class StudentSummary(BaseModel):
    """Summary of a student's progress."""

    student_id: str
    student_name: str | None
    overall_mastery: float
    concepts_completed: int
    total_concepts: int
    engagement: EngagementStats
    has_gaming_flags: bool
    high_severity_flags: int
    last_interaction: datetime | None


class ConceptStruggle(BaseModel):
    """Concept that students commonly struggle with."""

    concept_id: str
    concept_name: str
    struggle_rate: float  # Percentage of students below threshold
    common_misconceptions: list[str]
    average_time_to_mastery_minutes: float | None


class ClassOverview(BaseModel):
    """Overview of class-wide analytics."""

    course_id: str
    course_name: str
    total_students: int
    active_students: int  # Active in last 7 days
    average_mastery: float
    mastery_distribution: list[MasteryDistribution]
    engagement: EngagementStats
    struggling_concepts: list[ConceptStruggle]
    students_with_gaming_flags: int
    completion_rate: float  # Percentage who completed all concepts
    generated_at: datetime


class StudentProgressResponse(BaseModel):
    """Detailed student progress for faculty view."""

    student_id: str
    student_name: str | None
    course_id: str
    enrolled_at: datetime
    study_condition: str | None

    # Mastery
    overall_mastery: float
    concept_mastery: dict[str, dict[str, Any]]
    concepts_completed: list[str]
    current_concept_id: str | None

    # Engagement
    engagement: EngagementStats

    # Gaming
    gaming_flags: list[dict[str, Any]]
    trajectory_classification: str | None

    # Verification
    pending_verification: bool
    last_verification: datetime | None


class TimeSeriesDataPoint(BaseModel):
    """Single data point in a time series."""

    timestamp: datetime
    value: float


class ProgressTimeline(BaseModel):
    """Timeline of student progress."""

    student_id: str
    course_id: str
    mastery_over_time: list[TimeSeriesDataPoint]
    interactions_per_day: list[TimeSeriesDataPoint]
    concept_completions: list[dict[str, Any]]  # {concept_id, completed_at}
