"""Interaction model for logging tutor conversations."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.concept import Concept, Misconception
    from mentor.models.course import Course
    from mentor.models.user import User


class Interaction(Base, UUIDMixin):
    """Single interaction in a tutoring session."""

    __tablename__ = "interactions"

    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        nullable=False,
        index=True,
    )

    # Concept being addressed
    concept_id: Mapped[str | None] = mapped_column(
        ForeignKey("concepts.id"),
        index=True,
    )

    # Timing
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    response_time_ms: Mapped[int | None] = mapped_column(Integer)

    # Content
    student_message: Mapped[str] = mapped_column(Text, nullable=False)
    tutor_response: Mapped[str] = mapped_column(Text, nullable=False)

    # Classification
    pedagogical_move: Mapped[str | None] = mapped_column(String(50))
    student_message_type: Mapped[str | None] = mapped_column(String(50))
    response_quality: Mapped[str | None] = mapped_column(String(50))

    # Misconception tracking
    misconception_observed: Mapped[str | None] = mapped_column(
        ForeignKey("misconceptions.id"),
    )
    misconception_addressed: Mapped[bool] = mapped_column(default=False)

    # Gaming detection for this interaction
    gaming_signals: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Retrieved context (for debugging/analysis)
    retrieved_chunks: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Full metadata (named interaction_metadata to avoid SQLAlchemy reserved name)
    interaction_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_interactions_student_course", "student_id", "course_id"),
        Index("idx_interactions_session", "session_id"),
        Index("idx_interactions_timestamp", "timestamp"),
        Index("idx_interactions_concept", "concept_id"),
    )

    # Relationships
    student: Mapped["User"] = relationship("User", back_populates="interactions")
    course: Mapped["Course"] = relationship("Course", back_populates="interactions")
    concept: Mapped["Concept | None"] = relationship("Concept", back_populates="interactions")
    misconception_observed_rel: Mapped["Misconception | None"] = relationship(
        "Misconception", back_populates="interactions"
    )
