"""Concept and Misconception models."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.course import Course
    from mentor.models.interaction import Interaction
    from mentor.models.material import MaterialChunk
    from mentor.models.student_state import StudentState


class Concept(Base, UUIDMixin, TimestampMixin):
    """Concept in the course knowledge graph."""

    __tablename__ = "concepts"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Position in knowledge graph - array of concept IDs
    prerequisites: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Learning parameters
    estimated_time_minutes: Mapped[int | None] = mapped_column(Integer)
    difficulty_level: Mapped[int | None] = mapped_column(Integer)

    # Learning objectives as structured JSONB
    learning_objectives: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)

    # Ordering within course
    sequence_order: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint(
            "difficulty_level IS NULL OR (difficulty_level >= 1 AND difficulty_level <= 5)",
            name="check_difficulty_level",
        ),
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="concepts")
    misconceptions: Mapped[list["Misconception"]] = relationship(
        "Misconception", back_populates="concept", cascade="all, delete-orphan"
    )
    material_chunks: Mapped[list["MaterialChunk"]] = relationship(
        "MaterialChunk", back_populates="concept"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="concept"
    )
    current_students: Mapped[list["StudentState"]] = relationship(
        "StudentState",
        back_populates="current_concept",
        foreign_keys="StudentState.current_concept_id",
    )


class Misconception(Base, UUIDMixin, TimestampMixin):
    """Common misconception for a concept."""

    __tablename__ = "misconceptions"

    concept_id: Mapped[str] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # How to identify and address
    manifestation: Mapped[str | None] = mapped_column(Text)
    diagnostic_question: Mapped[str | None] = mapped_column(Text)
    correction_approach: Mapped[str | None] = mapped_column(Text)

    # Example exchanges
    example_student_response: Mapped[str | None] = mapped_column(Text)
    example_tutor_response: Mapped[str | None] = mapped_column(Text)

    # Frequency tracking
    times_observed: Mapped[int] = mapped_column(Integer, default=0)
    times_resolved: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    concept: Mapped["Concept"] = relationship("Concept", back_populates="misconceptions")
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="misconception_observed_rel"
    )
