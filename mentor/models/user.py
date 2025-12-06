"""User and Institution models."""

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.course import Course, CourseEnrollment
    from mentor.models.interaction import Interaction
    from mentor.models.student_state import StudentState
    from mentor.models.verification import VerificationReport


class Institution(Base, UUIDMixin, TimestampMixin):
    """Institution model for multi-tenant support."""

    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(255))
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="institution")
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="institution")


class User(Base, UUIDMixin, TimestampMixin):
    """User model for faculty, students, admins, and researchers."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    institution_id: Mapped[str | None] = mapped_column(
        ForeignKey("institutions.id"),
        index=True,
    )

    # Relationships
    institution: Mapped["Institution | None"] = relationship("Institution", back_populates="users")
    created_courses: Mapped[list["Course"]] = relationship(
        "Course", back_populates="creator", foreign_keys="Course.created_by"
    )
    enrollments: Mapped[list["CourseEnrollment"]] = relationship(
        "CourseEnrollment", back_populates="student"
    )
    student_states: Mapped[list["StudentState"]] = relationship(
        "StudentState", back_populates="student"
    )
    interactions: Mapped[list["Interaction"]] = relationship(
        "Interaction", back_populates="student"
    )
    verification_reports: Mapped[list["VerificationReport"]] = relationship(
        "VerificationReport",
        back_populates="student",
        foreign_keys="VerificationReport.student_id",
    )
    verified_reports: Mapped[list["VerificationReport"]] = relationship(
        "VerificationReport",
        back_populates="verifier",
        foreign_keys="VerificationReport.verified_by",
    )

    @property
    def is_faculty(self) -> bool:
        return self.role == "faculty"

    @property
    def is_student(self) -> bool:
        return self.role == "student"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_researcher(self) -> bool:
        return self.role == "researcher"
