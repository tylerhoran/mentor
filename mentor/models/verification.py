"""Verification report model for human assessment."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.course import Course
    from mentor.models.user import User


class VerificationReport(Base, UUIDMixin, TimestampMixin):
    """Generated report for human verification of student learning."""

    __tablename__ = "verification_reports"

    student_id: Mapped[str] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report content
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    report_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    # Structure: {
    #   summary: {...},
    #   mastery_by_concept: [...],
    #   concerns: [...],
    #   recommended_questions: [...],
    #   key_excerpts: [...]
    # }

    # Verification outcome
    verification_status: Mapped[str] = mapped_column(String(50), default="pending")
    verified_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verification_notes: Mapped[str | None] = mapped_column(Text)

    # Assessment scores (filled in after human verification)
    assessment_scores: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    overall_assessment: Mapped[str | None] = mapped_column(String(50))

    # Relationships
    student: Mapped["User"] = relationship(
        "User",
        back_populates="verification_reports",
        foreign_keys=[student_id],
    )
    course: Mapped["Course"] = relationship("Course", back_populates="verification_reports")
    verifier: Mapped["User | None"] = relationship(
        "User",
        back_populates="verified_reports",
        foreign_keys=[verified_by],
    )

    @property
    def is_pending(self) -> bool:
        return self.verification_status == "pending"

    @property
    def is_verified(self) -> bool:
        return self.verification_status == "completed"

    @property
    def has_concerns(self) -> bool:
        """Check if report has any concerns flagged."""
        return bool(self.report_data.get("concerns", []))

    @property
    def recommended_questions(self) -> list[dict[str, Any]]:
        """Get recommended verification questions."""
        return self.report_data.get("recommended_questions", [])
