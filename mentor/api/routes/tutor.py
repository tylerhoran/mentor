"""Tutoring session routes."""

from datetime import datetime, timezone
from typing import AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from mentor.api.deps import CurrentStudent, CurrentUser, DbSession
from mentor.models import Concept, Course, CourseEnrollment, Interaction, StudentState
from mentor.schemas.tutor import (
    MessageRequest,
    MessageResponse,
    SessionCreate,
    SessionResponse,
)

router = APIRouter(prefix="/tutor", tags=["tutor"])


# In-memory session store (should be Redis in production)
active_sessions: dict[str, dict] = {}


class SessionEndResponse(BaseModel):
    """Response for ending a session."""

    session_id: str
    total_interactions: int
    duration_seconds: int


@router.post("/session/start", response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate,
    db: DbSession,
    current_user: CurrentStudent,
) -> SessionResponse:
    """Start a new tutoring session."""
    # Verify enrollment
    result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.course_id == session_data.course_id,
            CourseEnrollment.student_id == current_user.id,
        )
    )
    enrollment = result.scalar_one_or_none()

    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled in this course")

    # Get or create student state
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == current_user.id,
            StudentState.course_id == session_data.course_id,
        )
    )
    student_state = result.scalar_one_or_none()

    if not student_state:
        student_state = StudentState(
            student_id=current_user.id,
            course_id=session_data.course_id,
        )
        db.add(student_state)
        await db.flush()

    # Determine current concept
    current_concept_id = session_data.concept_id or student_state.current_concept_id
    current_concept_name = None

    if current_concept_id:
        result = await db.execute(select(Concept).where(Concept.id == current_concept_id))
        concept = result.scalar_one_or_none()
        if concept:
            current_concept_name = concept.name

    # Create session
    session_id = str(uuid4())
    now = datetime.now(timezone.utc)

    # Store session in memory (use Redis in production)
    active_sessions[session_id] = {
        "student_id": current_user.id,
        "course_id": session_data.course_id,
        "current_concept_id": current_concept_id,
        "started_at": now,
        "message_count": 0,
        "conversation_history": [],
    }

    # Update engagement metrics
    metrics = student_state.engagement_metrics.copy()
    metrics["session_count"] = metrics.get("session_count", 0) + 1
    metrics["last_session_at"] = now.isoformat()
    student_state.engagement_metrics = metrics

    await db.flush()

    return SessionResponse(
        session_id=session_id,
        course_id=session_data.course_id,
        student_id=current_user.id,
        current_concept_id=current_concept_id,
        current_concept_name=current_concept_name,
        started_at=now,
        message_count=0,
    )


@router.post("/session/{session_id}/message", response_model=MessageResponse)
async def send_message(
    session_id: str,
    message: MessageRequest,
    db: DbSession,
    current_user: CurrentStudent,
) -> MessageResponse:
    """Send a message to the tutor and get a response."""
    # Validate session
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["student_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get course for tutor configuration
    result = await db.execute(select(Course).where(Course.id == session["course_id"]))
    course = result.scalar_one_or_none()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # TODO: Use DialogueManager to generate response
    # For now, return a placeholder response
    tutor_response = (
        f"I understand you're asking about: {message.message[:100]}... "
        "Let me help you work through this step by step. "
        "What have you tried so far?"
    )

    # Create interaction record
    interaction = Interaction(
        student_id=current_user.id,
        course_id=session["course_id"],
        session_id=session_id,
        concept_id=session.get("current_concept_id"),
        student_message=message.message,
        tutor_response=tutor_response,
        response_time_ms=message.response_time_ms,
        pedagogical_move="scaffold",  # TODO: Determine from DialogueManager
        timestamp=datetime.now(timezone.utc),
    )
    db.add(interaction)
    await db.flush()
    await db.refresh(interaction)

    # Update session
    session["message_count"] += 1
    session["conversation_history"].append(
        {
            "role": "student",
            "content": message.message,
        }
    )
    session["conversation_history"].append(
        {
            "role": "tutor",
            "content": tutor_response,
        }
    )

    # Update student state engagement metrics
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == current_user.id,
            StudentState.course_id == session["course_id"],
        )
    )
    student_state = result.scalar_one_or_none()

    if student_state:
        metrics = student_state.engagement_metrics.copy()
        metrics["total_interactions"] = metrics.get("total_interactions", 0) + 1
        student_state.engagement_metrics = metrics

    await db.flush()

    return MessageResponse(
        interaction_id=interaction.id,
        session_id=session_id,
        student_message=message.message,
        tutor_response=tutor_response,
        concept_id=session.get("current_concept_id"),
        pedagogical_move=interaction.pedagogical_move,
        timestamp=interaction.timestamp,
    )


@router.post("/session/{session_id}/message/stream")
async def send_message_stream(
    session_id: str,
    message: MessageRequest,
    db: DbSession,
    current_user: CurrentStudent,
) -> StreamingResponse:
    """Send a message and stream the response."""
    # Validate session
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["student_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    async def generate_response() -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        # TODO: Integrate with LLM client for actual streaming
        response_parts = [
            "I understand ",
            "you're asking about ",
            "this topic. ",
            "Let me help you ",
            "work through it ",
            "step by step. ",
            "What have you ",
            "tried so far?",
        ]

        for part in response_parts:
            yield f"data: {part}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_response(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    db: DbSession,
    current_user: CurrentUser,
) -> dict:
    """Get history of a tutoring session."""
    # Get interactions for this session
    result = await db.execute(
        select(Interaction)
        .where(Interaction.session_id == session_id)
        .order_by(Interaction.timestamp)
    )
    interactions = result.scalars().all()

    if not interactions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify access
    first_interaction = interactions[0]
    if first_interaction.student_id != current_user.id and not (
        current_user.is_faculty or current_user.is_admin
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "session_id": session_id,
        "course_id": first_interaction.course_id,
        "student_id": first_interaction.student_id,
        "interactions": [
            {
                "id": i.id,
                "student_message": i.student_message,
                "tutor_response": i.tutor_response,
                "concept_id": i.concept_id,
                "pedagogical_move": i.pedagogical_move,
                "timestamp": i.timestamp.isoformat(),
                "response_time_ms": i.response_time_ms,
            }
            for i in interactions
        ],
        "total_interactions": len(interactions),
    }


@router.post("/session/{session_id}/end", response_model=SessionEndResponse)
async def end_session(
    session_id: str,
    db: DbSession,
    current_user: CurrentStudent,
) -> SessionEndResponse:
    """End a tutoring session."""
    session = active_sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["student_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Calculate duration
    started_at = session["started_at"]
    ended_at = datetime.now(timezone.utc)
    duration_seconds = int((ended_at - started_at).total_seconds())

    # Update student state with session time
    result = await db.execute(
        select(StudentState).where(
            StudentState.student_id == current_user.id,
            StudentState.course_id == session["course_id"],
        )
    )
    student_state = result.scalar_one_or_none()

    if student_state:
        metrics = student_state.engagement_metrics.copy()
        metrics["total_time_seconds"] = metrics.get("total_time_seconds", 0) + duration_seconds
        student_state.engagement_metrics = metrics
        await db.flush()

    # Remove session from memory
    total_interactions = session["message_count"]
    del active_sessions[session_id]

    return SessionEndResponse(
        session_id=session_id,
        total_interactions=total_interactions,
        duration_seconds=duration_seconds,
    )
