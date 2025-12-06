"""Pydantic schemas for API validation."""

from mentor.schemas.analytics import (
    ClassOverview,
    EngagementStats,
    MasteryDistribution,
)
from mentor.schemas.assessment import (
    MasteryEstimate,
    MasteryReport,
    TrajectoryAnalysis,
    VerificationQuestion,
    VerificationReportCreate,
    VerificationReportResponse,
    VerificationResults,
)
from mentor.schemas.course import (
    ConceptCreate,
    ConceptResponse,
    ConceptUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    MisconceptionCreate,
    MisconceptionResponse,
    PedagogyConfigSchema,
)
from mentor.schemas.tutor import (
    MessageRequest,
    MessageResponse,
    SessionCreate,
    SessionResponse,
)

__all__ = [
    # Course
    "CourseCreate",
    "CourseUpdate",
    "CourseResponse",
    "ConceptCreate",
    "ConceptUpdate",
    "ConceptResponse",
    "MisconceptionCreate",
    "MisconceptionResponse",
    "PedagogyConfigSchema",
    # Tutor
    "SessionCreate",
    "SessionResponse",
    "MessageRequest",
    "MessageResponse",
    # Assessment
    "MasteryEstimate",
    "MasteryReport",
    "TrajectoryAnalysis",
    "VerificationQuestion",
    "VerificationReportCreate",
    "VerificationReportResponse",
    "VerificationResults",
    # Analytics
    "ClassOverview",
    "EngagementStats",
    "MasteryDistribution",
]
