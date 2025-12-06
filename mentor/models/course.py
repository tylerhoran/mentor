"""Course and enrollment models."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.concept import Concept
    from mentor.models.interaction import Interaction
    from mentor.models.material import Material
    from mentor.models.student_state import StudentState
    from mentor.models.user import Institution, User
    from mentor.models.verification import VerificationReport


class Course(Base, UUIDMixin, TimestampMixin):
    """Course model with pedagogical configuration."""

    __tablename__ = "courses"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[str | None] = mapped_column(
        ForeignKey("institutions.id"),
        index=True,
    )

    # Pedagogical configuration
    pedagogy_config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        default=lambda: {
            "style": "socratic",
            "response_patterns": {},
            "boundaries": {"never_do": [], "always_do": []},
            "voice_description": None,
        },
    )

    # System prompt components
    system_prompt_template: Mapped[str | None] = mapped_column(Text)
    generated_system_prompt: Mapped[str | None] = mapped_column(Text)

    # Model configuration
    base_model: Mapped[str] = mapped_column(String(100), default="llama-3.1-8b")
    adapter_path: Mapped[str | None] = mapped_column(String(255))
    temperature: Mapped[float] = mapped_column(Float, default=0.7)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name="check_course_status",
        ),
    )

    # Relationships
    creator: Mapped["User"] = relationship(
        "User", back_populates="created_courses", foreign_keys=[created_by]
    )
    institution: Mapped["Institution | None"] = relationship(
        "Institution", back_populates="courses"
    )
    concepts: Mapped[list["Concept"]] = relationship(
        "Concept", back_populates="course", cascade="all, delete-orphan"
    )
    materials: Mapped[list["Material"]] = relationship(
        "Material", back_populates="course", cascade="all, delete-orphan"
    )
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(
        "CourseEnrollment", back_populates="course", cascade="all, delete-orphan"
    )
    student_states: Mapped[list["StudentState"]] = relationship(
        "StudentState", back_populates="course", cascade="all, delete-orphan"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="course", cascade="all, delete-orphan"
    )
    verification_reports: Mapped[list["VerificationReport"]] = relationship(
        "VerificationReport", back_populates="course", cascade="all, delete-orphan"
    )


class CourseEnrollment(Base, UUIDMixin):
    """Student enrollment in a course."""

    __tablename__ = "course_enrollments"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Research study assignment
    study_condition: Mapped[str | None] = mapped_column(String(50))

    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
    )

    __table_args__ = (
        # Unique constraint on course_id and student_id
        {"sqlite_autoincrement": True},
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    student: Mapped["User"] = relationship("User", back_populates="enrollments")
