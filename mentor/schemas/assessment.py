"""Assessment and verification schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MasteryEstimate(BaseModel):
    """Mastery estimate for a single concept."""

    concept_id: str
    concept_name: str
    estimate: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    interaction_count: int
    last_updated: datetime | None


class MasteryReport(BaseModel):
    """Full mastery report for a student."""

    student_id: str
    course_id: str
    overall_mastery: float
    overall_confidence: float
    concepts: list[MasteryEstimate]
    concepts_completed: list[str]
    current_concept_id: str | None
    generated_at: datetime


class GamingFlag(BaseModel):
    """Gaming flag for suspicious behavior."""

    type: str
    severity: str = Field(..., pattern="^(low|medium|high)$")
    timestamp: datetime
    evidence: str
    interaction_id: str | None = None
    resolved: bool = False


class TrajectoryAnalysis(BaseModel):
    """Analysis of student learning trajectory."""

    student_id: str
    course_id: str
    classification: str = Field(..., pattern="^(genuine|suspected_gaming|unclear)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    gaming_flags: list[GamingFlag]
    analysis_summary: str
    analyzed_at: datetime


class VerificationQuestion(BaseModel):
    """Question recommended for human verification."""

    concept_id: str
    concept_name: str
    question: str
    rationale: str
    look_for: str
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")


class InteractionExcerpt(BaseModel):
    """Key interaction excerpt for verification report."""

    type: str = Field(..., pattern="^(breakthrough|struggle|gaming_flag)$")
    concept_id: str | None
    interactions: list[dict[str, Any]]
    note: str
    timestamp: datetime


class VerificationReportCreate(BaseModel):
    """Schema for generating a verification report."""

    include_excerpts: bool = True
    max_questions: int = Field(default=10, ge=1, le=20)


class VerificationReportResponse(BaseModel):
    """Schema for verification report response."""

    id: str
    student_id: str
    course_id: str
    generated_at: datetime
    verification_status: str
    verified_by: str | None
    verified_at: datetime | None
    verification_notes: str | None

    # Report content
    summary: dict[str, Any]
    mastery_by_concept: list[MasteryEstimate]
    concerns: list[GamingFlag]
    recommended_questions: list[VerificationQuestion]
    key_excerpts: list[InteractionExcerpt]

    # Assessment results (after verification)
    assessment_scores: dict[str, float] | None
    overall_assessment: str | None

    model_config = {"from_attributes": True}


class VerificationResults(BaseModel):
    """Schema for recording verification results."""

    assessment_scores: dict[str, float] = Field(
        ...,
        description="Concept ID to score mapping",
    )
    overall_assessment: str = Field(
        ...,
        pattern="^(mastery|partial|insufficient|gaming_suspected)$",
    )
    verification_notes: str | None = None
