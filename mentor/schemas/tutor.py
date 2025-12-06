"""Tutor session schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Schema for creating a tutoring session."""

    course_id: str
    concept_id: str | None = None


class SessionResponse(BaseModel):
    """Schema for session response."""

    session_id: str
    course_id: str
    student_id: str
    current_concept_id: str | None
    current_concept_name: str | None
    started_at: datetime
    message_count: int = 0


class MessageRequest(BaseModel):
    """Schema for sending a message to the tutor."""

    message: str = Field(..., min_length=1, max_length=10000)
    response_time_ms: int | None = Field(
        default=None,
        description="Time in ms the student took to respond",
    )


class MessageResponse(BaseModel):
    """Schema for tutor message response."""

    interaction_id: str
    session_id: str
    student_message: str
    tutor_response: str
    concept_id: str | None
    pedagogical_move: str | None
    timestamp: datetime


class InteractionResponse(BaseModel):
    """Schema for interaction history response."""

    id: str
    session_id: str
    student_message: str
    tutor_response: str
    concept_id: str | None
    pedagogical_move: str | None
    student_message_type: str | None
    response_quality: str | None
    timestamp: datetime
    response_time_ms: int | None
    metadata: dict[str, Any]

    model_config = {"from_attributes": True}


class SessionHistoryResponse(BaseModel):
    """Schema for session history."""

    session_id: str
    course_id: str
    student_id: str
    started_at: datetime
    ended_at: datetime | None
    interactions: list[InteractionResponse]
    total_interactions: int
