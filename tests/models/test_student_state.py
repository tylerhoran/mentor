"""Tests for StudentState model."""

import uuid
from datetime import datetime, timezone

import pytest

from mentor.models.student_state import StudentState


class TestStudentState:
    """Tests for StudentState model."""

    def test_student_state_creation(self):
        """Test creating a student state with required fields."""
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()

        state = StudentState(student_id=student_id, course_id=course_id)

        assert state.student_id == student_id
        assert state.course_id == course_id

    def test_student_state_concept_mastery(self):
        """Test concept mastery storage structure."""
        concept_id = str(uuid.uuid4())
        mastery = {
            concept_id: {
                "estimate": 0.75,
                "confidence": 0.8,
                "interactions": 10,
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }
        }
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concept_mastery=mastery,
        )
        assert state.concept_mastery[concept_id]["estimate"] == 0.75
        assert state.concept_mastery[concept_id]["confidence"] == 0.8

    def test_student_state_empty_concept_mastery(self):
        """Test empty concept mastery dict."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concept_mastery={},
        )
        assert state.concept_mastery == {}

    def test_student_state_engagement_metrics(self):
        """Test engagement metrics storage structure."""
        metrics = {
            "total_interactions": 50,
            "total_time_seconds": 3600,
            "average_response_time_ms": 5000,
            "session_count": 5,
            "last_session_at": datetime.now(timezone.utc).isoformat(),
        }
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            engagement_metrics=metrics,
        )
        assert state.engagement_metrics["total_interactions"] == 50
        assert state.engagement_metrics["session_count"] == 5

    def test_student_state_gaming_flags(self):
        """Test gaming flags storage structure."""
        flags = [
            {
                "type": "fast_response",
                "severity": "medium",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "evidence": "Response time of 2s for complex question",
                "resolved": False,
            },
            {
                "type": "copy_paste",
                "severity": "high",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "evidence": "Exact match with external source",
                "resolved": True,
            },
        ]
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=flags,
        )
        assert len(state.gaming_flags) == 2
        assert state.gaming_flags[0]["severity"] == "medium"
        assert state.gaming_flags[1]["resolved"] is True

    def test_student_state_empty_gaming_flags(self):
        """Test empty gaming flags list."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=[],
        )
        assert state.gaming_flags == []

    def test_student_state_current_concept(self):
        """Test current concept tracking."""
        concept_id = uuid.uuid4()
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            current_concept_id=concept_id,
        )
        assert state.current_concept_id == concept_id

    def test_student_state_concepts_completed(self):
        """Test completed concepts list."""
        completed = [str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())]
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concepts_completed=completed,
        )
        assert len(state.concepts_completed) == 3

    def test_student_state_empty_concepts_completed(self):
        """Test empty concepts_completed list."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concepts_completed=[],
        )
        assert state.concepts_completed == []

    def test_get_mastery_estimate(self):
        """Test get_mastery_estimate method."""
        concept_id = str(uuid.uuid4())
        mastery = {concept_id: {"estimate": 0.85, "confidence": 0.9, "interactions": 15}}
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concept_mastery=mastery,
        )

        assert state.get_mastery_estimate(concept_id) == 0.85

    def test_get_mastery_estimate_not_found(self):
        """Test get_mastery_estimate returns 0.0 for unknown concept."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concept_mastery={},
        )
        unknown_id = str(uuid.uuid4())

        assert state.get_mastery_estimate(unknown_id) == 0.0

    def test_get_mastery_confidence(self):
        """Test get_mastery_confidence method."""
        concept_id = str(uuid.uuid4())
        mastery = {concept_id: {"estimate": 0.85, "confidence": 0.9, "interactions": 15}}
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concept_mastery=mastery,
        )

        assert state.get_mastery_confidence(concept_id) == 0.9

    def test_get_mastery_confidence_not_found(self):
        """Test get_mastery_confidence returns 0.0 for unknown concept."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            concept_mastery={},
        )
        unknown_id = str(uuid.uuid4())

        assert state.get_mastery_confidence(unknown_id) == 0.0

    def test_has_gaming_flags_property_false(self):
        """Test has_gaming_flags property when no flags."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=[],
        )
        assert state.has_gaming_flags is False

    def test_has_gaming_flags_property_true(self):
        """Test has_gaming_flags property with unresolved flag."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=[{"type": "test", "severity": "low", "resolved": False}],
        )
        assert state.has_gaming_flags is True

    def test_has_gaming_flags_only_resolved(self):
        """Test has_gaming_flags with only resolved flags."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=[{"type": "test", "severity": "low", "resolved": True}],
        )
        assert state.has_gaming_flags is False

    def test_high_severity_flags_property(self):
        """Test high_severity_flags property."""
        flags = [
            {"type": "fast", "severity": "low", "resolved": False},
            {"type": "copy", "severity": "high", "resolved": False},
            {"type": "pattern", "severity": "high", "resolved": True},
            {"type": "ai", "severity": "high", "resolved": False},
        ]
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=flags,
        )

        high_flags = state.high_severity_flags
        # Should only include unresolved high severity flags
        assert len(high_flags) == 2
        assert all(f["severity"] == "high" for f in high_flags)
        assert all(f["resolved"] is False for f in high_flags)

    def test_high_severity_flags_empty(self):
        """Test high_severity_flags returns empty list when none exist."""
        state = StudentState(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            gaming_flags=[
                {"type": "fast", "severity": "low", "resolved": False},
                {"type": "medium", "severity": "medium", "resolved": False},
            ],
        )
        assert len(state.high_severity_flags) == 0
