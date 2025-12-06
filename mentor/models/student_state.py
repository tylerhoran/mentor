"""Student state model for tracking mastery and engagement."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.concept import Concept
    from mentor.models.course import Course
    from mentor.models.user import User


class StudentState(Base, UUIDMixin, TimestampMixin):
    """Tracks student progress and mastery within a course."""

    __tablename__ = "student_states"

    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Mastery estimates per concept
    # Structure: {concept_id: {estimate: 0.0-1.0, confidence: 0.0-1.0, interactions: int, last_updated: timestamp}}
    concept_mastery: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Engagement metrics
    # Structure: {total_interactions: int, total_time_seconds: int, average_response_time_ms: float,
    #             session_count: int, last_session_at: timestamp}
    engagement_metrics: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {
            "total_interactions": 0,
            "total_time_seconds": 0,
            "average_response_time_ms": None,
            "session_count": 0,
            "last_session_at": None,
        },
    )

    # Gaming detection
    # Structure: [{type: string, severity: string, timestamp: string, evidence: string, resolved: bool}]
    gaming_flags: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Progress tracking
    current_concept_id: Mapped[str | None] = mapped_column(
        ForeignKey("concepts.id"),
        index=True,
    )
    concepts_completed: Mapped[list[str]] = mapped_column(ARRAY(str), default=list)

    __table_args__ = (UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="student_states")
    course: Mapped["Course"] = relationship("Course", back_populates="student_states")
    current_concept: Mapped["Concept | None"] = relationship(
        "Concept",
        back_populates="current_students",
        foreign_keys=[current_concept_id],
    )

    def get_mastery_estimate(self, concept_id: str) -> float:
        """Get mastery estimate for a concept, defaulting to 0.0."""
        if concept_id in self.concept_mastery:
            return self.concept_mastery[concept_id].get("estimate", 0.0)
        return 0.0

    def get_mastery_confidence(self, concept_id: str) -> float:
        """Get confidence in mastery estimate for a concept."""
        if concept_id in self.concept_mastery:
            return self.concept_mastery[concept_id].get("confidence", 0.0)
        return 0.0

    @property
    def has_gaming_flags(self) -> bool:
        """Check if student has any unresolved gaming flags."""
        return any(not flag.get("resolved", False) for flag in self.gaming_flags)

    @property
    def high_severity_flags(self) -> list[dict[str, Any]]:
        """Get high severity unresolved gaming flags."""
        return [
            flag
            for flag in self.gaming_flags
            if flag.get("severity") == "high" and not flag.get("resolved", False)
        ]
