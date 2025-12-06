"""Tests for Interaction model."""

import uuid
from datetime import datetime, timezone

import pytest

from mentor.models.interaction import Interaction


class TestInteraction:
    """Tests for Interaction model."""

    def test_interaction_creation(self):
        """Test creating an interaction with required fields."""
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()
        session_id = uuid.uuid4()

        interaction = Interaction(
            student_id=student_id,
            course_id=course_id,
            session_id=session_id,
            student_message="How do I create a variable?",
            tutor_response="Great question! A variable is created by...",
        )

        assert interaction.student_id == student_id
        assert interaction.course_id == course_id
        assert interaction.session_id == session_id
        assert "variable" in interaction.student_message
        assert interaction.tutor_response is not None

    def test_interaction_with_concept(self):
        """Test interaction linked to a concept."""
        concept_id = uuid.uuid4()
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Question about variables",
            tutor_response="Response about variables",
            concept_id=concept_id,
        )
        assert interaction.concept_id == concept_id

    def test_interaction_response_time(self):
        """Test interaction with response time tracking."""
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Quick question",
            tutor_response="Quick response",
            response_time_ms=1500,
        )
        assert interaction.response_time_ms == 1500

    def test_interaction_pedagogical_move(self):
        """Test interaction with pedagogical move."""
        moves = ["probe", "hint", "explain", "confirm", "redirect", "encourage"]

        for move in moves:
            interaction = Interaction(
                student_id=uuid.uuid4(),
                course_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                student_message="Student says something",
                tutor_response="Tutor responds",
                pedagogical_move=move,
            )
            assert interaction.pedagogical_move == move

    def test_interaction_message_types(self):
        """Test student message type classification."""
        message_types = ["question", "answer", "confusion", "request", "statement"]

        for msg_type in message_types:
            interaction = Interaction(
                student_id=uuid.uuid4(),
                course_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                student_message="Student message",
                tutor_response="Tutor response",
                student_message_type=msg_type,
            )
            assert interaction.student_message_type == msg_type

    def test_interaction_response_quality(self):
        """Test response quality classification."""
        qualities = ["correct", "incorrect", "partial", "off_topic"]

        for quality in qualities:
            interaction = Interaction(
                student_id=uuid.uuid4(),
                course_id=uuid.uuid4(),
                session_id=uuid.uuid4(),
                student_message="Student answer",
                tutor_response="Tutor feedback",
                response_quality=quality,
            )
            assert interaction.response_quality == quality

    def test_interaction_misconception_tracking(self):
        """Test misconception observation and addressing."""
        misconception_id = uuid.uuid4()
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="I think x always equals y",
            tutor_response="Let me clarify that...",
            misconception_observed=misconception_id,
            misconception_addressed=True,
        )
        assert interaction.misconception_observed == misconception_id
        assert interaction.misconception_addressed is True

    def test_interaction_misconception_addressed_false(self):
        """Test misconception_addressed can be set to False."""
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Question",
            tutor_response="Answer",
            misconception_addressed=False,
        )
        assert interaction.misconception_addressed is False

    def test_interaction_gaming_signals(self):
        """Test gaming signals storage."""
        signals = [
            {"type": "fast_response", "severity": "medium", "evidence": "5s response"},
            {"type": "copy_paste", "severity": "high", "evidence": "exact match"},
        ]
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Student message",
            tutor_response="Tutor response",
            gaming_signals=signals,
        )
        assert len(interaction.gaming_signals) == 2
        assert interaction.gaming_signals[0]["type"] == "fast_response"

    def test_interaction_empty_gaming_signals(self):
        """Test interaction with empty gaming_signals list."""
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Question",
            tutor_response="Answer",
            gaming_signals=[],
        )
        assert interaction.gaming_signals == []

    def test_interaction_retrieved_chunks(self):
        """Test retrieved chunk IDs."""
        chunk_ids = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Complex question",
            tutor_response="Detailed answer",
            retrieved_chunks=chunk_ids,
        )
        assert len(interaction.retrieved_chunks) == 3

    def test_interaction_empty_retrieved_chunks(self):
        """Test interaction with empty retrieved_chunks."""
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Question",
            tutor_response="Answer",
            retrieved_chunks=[],
        )
        assert interaction.retrieved_chunks == []

    def test_interaction_metadata(self):
        """Test interaction metadata storage."""
        metadata = {
            "model_used": "llama-3.1-8b",
            "tokens_used": 150,
            "latency_breakdown": {"retrieval": 100, "generation": 200},
        }
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Question",
            tutor_response="Answer",
            interaction_metadata=metadata,
        )
        assert interaction.interaction_metadata["model_used"] == "llama-3.1-8b"
        assert interaction.interaction_metadata["tokens_used"] == 150

    def test_interaction_empty_metadata(self):
        """Test interaction with empty metadata."""
        interaction = Interaction(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            session_id=uuid.uuid4(),
            student_message="Question",
            tutor_response="Answer",
            interaction_metadata={},
        )
        assert interaction.interaction_metadata == {}

    def test_interaction_session_grouping(self):
        """Test that interactions can be grouped by session."""
        session_id = uuid.uuid4()
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()

        interactions = []
        for i in range(3):
            interaction = Interaction(
                student_id=student_id,
                course_id=course_id,
                session_id=session_id,
                student_message=f"Message {i}",
                tutor_response=f"Response {i}",
            )
            interactions.append(interaction)

        # All interactions should share the same session
        assert all(i.session_id == session_id for i in interactions)
