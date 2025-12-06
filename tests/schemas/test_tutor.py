"""Tests for tutor session schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mentor.schemas.tutor import (
    InteractionResponse,
    MessageRequest,
    MessageResponse,
    SessionCreate,
    SessionHistoryResponse,
    SessionResponse,
)


class TestSessionCreate:
    """Tests for SessionCreate schema."""

    def test_session_create_minimal(self):
        """Test creating session with minimal fields."""
        session = SessionCreate(course_id="course-123")

        assert session.course_id == "course-123"
        assert session.concept_id is None

    def test_session_create_with_concept(self):
        """Test creating session with specific concept."""
        session = SessionCreate(
            course_id="course-123",
            concept_id="concept-456",
        )

        assert session.concept_id == "concept-456"


class TestSessionResponse:
    """Tests for SessionResponse schema."""

    def test_session_response(self):
        """Test session response schema."""
        now = datetime.now(UTC)
        response = SessionResponse(
            session_id="session-123",
            course_id="course-456",
            student_id="student-789",
            current_concept_id="concept-abc",
            current_concept_name="Variables",
            started_at=now,
            message_count=5,
        )

        assert response.session_id == "session-123"
        assert response.message_count == 5

    def test_session_response_default_message_count(self):
        """Test default message count is 0."""
        now = datetime.now(UTC)
        response = SessionResponse(
            session_id="session-123",
            course_id="course-456",
            student_id="student-789",
            current_concept_id=None,
            current_concept_name=None,
            started_at=now,
        )

        assert response.message_count == 0


class TestMessageRequest:
    """Tests for MessageRequest schema."""

    def test_message_request(self):
        """Test creating a message request."""
        request = MessageRequest(message="How do I create a variable?")

        assert request.message == "How do I create a variable?"
        assert request.response_time_ms is None

    def test_message_request_with_response_time(self):
        """Test message request with response time."""
        request = MessageRequest(
            message="I think the answer is x = 5",
            response_time_ms=5000,
        )

        assert request.response_time_ms == 5000

    def test_message_min_length(self):
        """Test message minimum length validation."""
        with pytest.raises(ValidationError):
            MessageRequest(message="")

    def test_message_max_length(self):
        """Test message maximum length validation."""
        # 10000 characters is the max
        long_message = "x" * 10001
        with pytest.raises(ValidationError):
            MessageRequest(message=long_message)

    def test_message_boundary_lengths(self):
        """Test message boundary lengths are valid."""
        # Min valid (1 char)
        MessageRequest(message="a")

        # Max valid (10000 chars)
        MessageRequest(message="x" * 10000)


class TestMessageResponse:
    """Tests for MessageResponse schema."""

    def test_message_response(self):
        """Test message response schema."""
        now = datetime.now(UTC)
        response = MessageResponse(
            interaction_id="interaction-123",
            session_id="session-456",
            student_message="What is a variable?",
            tutor_response="A variable is a container for storing data values.",
            concept_id="concept-789",
            pedagogical_move="explain",
            timestamp=now,
        )

        assert response.interaction_id == "interaction-123"
        assert response.pedagogical_move == "explain"

    def test_message_response_optional_fields(self):
        """Test message response with optional fields as None."""
        now = datetime.now(UTC)
        response = MessageResponse(
            interaction_id="interaction-123",
            session_id="session-456",
            student_message="Hello",
            tutor_response="Hi there!",
            concept_id=None,
            pedagogical_move=None,
            timestamp=now,
        )

        assert response.concept_id is None
        assert response.pedagogical_move is None


class TestInteractionResponse:
    """Tests for InteractionResponse schema."""

    def test_interaction_response(self):
        """Test interaction response schema."""
        now = datetime.now(UTC)
        response = InteractionResponse(
            id="interaction-123",
            session_id="session-456",
            student_message="I don't understand loops",
            tutor_response="Let me explain loops step by step...",
            concept_id="loops-concept",
            pedagogical_move="explain",
            student_message_type="confusion",
            response_quality="correct",
            timestamp=now,
            response_time_ms=3000,
            metadata={"model": "llama-3.1-8b"},
        )

        assert response.id == "interaction-123"
        assert response.student_message_type == "confusion"
        assert response.response_quality == "correct"
        assert response.response_time_ms == 3000
        assert response.metadata["model"] == "llama-3.1-8b"

    def test_interaction_response_minimal(self):
        """Test interaction response with minimal fields."""
        now = datetime.now(UTC)
        response = InteractionResponse(
            id="interaction-123",
            session_id="session-456",
            student_message="Hello",
            tutor_response="Hi!",
            concept_id=None,
            pedagogical_move=None,
            student_message_type=None,
            response_quality=None,
            timestamp=now,
            response_time_ms=None,
            metadata={},
        )

        assert response.concept_id is None
        assert response.metadata == {}


class TestSessionHistoryResponse:
    """Tests for SessionHistoryResponse schema."""

    def test_session_history_response(self):
        """Test session history response schema."""
        now = datetime.now(UTC)
        interactions = [
            InteractionResponse(
                id="i1",
                session_id="s1",
                student_message="Q1",
                tutor_response="A1",
                concept_id=None,
                pedagogical_move=None,
                student_message_type=None,
                response_quality=None,
                timestamp=now,
                response_time_ms=None,
                metadata={},
            ),
            InteractionResponse(
                id="i2",
                session_id="s1",
                student_message="Q2",
                tutor_response="A2",
                concept_id=None,
                pedagogical_move=None,
                student_message_type=None,
                response_quality=None,
                timestamp=now,
                response_time_ms=None,
                metadata={},
            ),
        ]

        history = SessionHistoryResponse(
            session_id="session-123",
            course_id="course-456",
            student_id="student-789",
            started_at=now,
            ended_at=now,
            interactions=interactions,
            total_interactions=2,
        )

        assert history.session_id == "session-123"
        assert len(history.interactions) == 2
        assert history.total_interactions == 2

    def test_session_history_ended_at_optional(self):
        """Test ended_at is optional (for active sessions)."""
        now = datetime.now(UTC)
        history = SessionHistoryResponse(
            session_id="session-123",
            course_id="course-456",
            student_id="student-789",
            started_at=now,
            ended_at=None,
            interactions=[],
            total_interactions=0,
        )

        assert history.ended_at is None
