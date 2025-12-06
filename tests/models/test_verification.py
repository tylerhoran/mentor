"""Tests for VerificationReport model."""

import uuid
from datetime import datetime, timezone

import pytest

from mentor.models.verification import VerificationReport


class TestVerificationReport:
    """Tests for VerificationReport model."""

    def test_verification_report_creation(self):
        """Test creating a verification report with required fields."""
        student_id = uuid.uuid4()
        course_id = uuid.uuid4()
        report_data = {
            "summary": {"overall_mastery": 0.75},
            "mastery_by_concept": [],
            "concerns": [],
            "recommended_questions": [],
            "key_excerpts": [],
        }

        report = VerificationReport(
            student_id=student_id,
            course_id=course_id,
            report_data=report_data,
        )

        assert report.student_id == student_id
        assert report.course_id == course_id
        assert report.report_data is not None

    def test_verification_report_default_status(self):
        """Test verification status with explicit pending value."""
        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            verification_status="pending",
        )
        assert report.verification_status == "pending"

    def test_verification_report_status_values(self):
        """Test valid verification status values."""
        statuses = ["pending", "completed", "in_review"]

        for status in statuses:
            report = VerificationReport(
                student_id=uuid.uuid4(),
                course_id=uuid.uuid4(),
                report_data={"summary": {}},
                verification_status=status,
            )
            assert report.verification_status == status

    def test_verification_report_with_verifier(self):
        """Test report with verifier information."""
        verifier_id = uuid.uuid4()
        verified_at = datetime.now(timezone.utc)

        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            verification_status="completed",
            verified_by=verifier_id,
            verified_at=verified_at,
            verification_notes="Student demonstrates good understanding.",
        )

        assert report.verified_by == verifier_id
        assert report.verified_at == verified_at
        assert report.verification_notes is not None

    def test_verification_report_assessment_scores(self):
        """Test report with assessment scores."""
        scores = {
            "concept_1": 0.9,
            "concept_2": 0.75,
            "concept_3": 0.6,
        }
        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            assessment_scores=scores,
        )
        assert report.assessment_scores["concept_1"] == 0.9

    def test_verification_report_overall_assessment(self):
        """Test report with overall assessment."""
        assessments = ["mastery", "partial", "insufficient", "gaming_suspected"]

        for assessment in assessments:
            report = VerificationReport(
                student_id=uuid.uuid4(),
                course_id=uuid.uuid4(),
                report_data={"summary": {}},
                overall_assessment=assessment,
            )
            assert report.overall_assessment == assessment

    def test_is_pending_property(self):
        """Test is_pending property."""
        pending_report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            verification_status="pending",
        )
        assert pending_report.is_pending is True

        completed_report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            verification_status="completed",
        )
        assert completed_report.is_pending is False

    def test_is_verified_property(self):
        """Test is_verified property."""
        pending_report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            verification_status="pending",
        )
        assert pending_report.is_verified is False

        completed_report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
            verification_status="completed",
        )
        assert completed_report.is_verified is True

    def test_has_concerns_property(self):
        """Test has_concerns property."""
        # No concerns
        report_clean = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={
                "summary": {},
                "concerns": [],
            },
        )
        assert report_clean.has_concerns is False

        # With concerns
        report_concerns = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={
                "summary": {},
                "concerns": [{"type": "gaming", "severity": "high"}],
            },
        )
        assert report_concerns.has_concerns is True

    def test_has_concerns_missing_key(self):
        """Test has_concerns when concerns key is missing."""
        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
        )
        # Should return False when key is missing
        assert report.has_concerns is False

    def test_recommended_questions_property(self):
        """Test recommended_questions property."""
        questions = [
            {
                "concept_id": "c1",
                "question": "Explain recursion",
                "rationale": "Test understanding",
            },
            {
                "concept_id": "c2",
                "question": "What is a loop?",
                "rationale": "Basic concept check",
            },
        ]
        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={
                "summary": {},
                "recommended_questions": questions,
            },
        )

        result = report.recommended_questions
        assert len(result) == 2
        assert result[0]["question"] == "Explain recursion"

    def test_recommended_questions_empty(self):
        """Test recommended_questions returns empty list when missing."""
        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data={"summary": {}},
        )
        assert report.recommended_questions == []

    def test_report_data_structure(self):
        """Test complete report data structure."""
        report_data = {
            "summary": {
                "overall_mastery": 0.78,
                "concepts_completed": 5,
                "total_concepts": 8,
                "completion_percentage": 62.5,
                "total_interactions": 45,
                "total_time_minutes": 120,
            },
            "mastery_by_concept": [
                {"concept_id": "c1", "name": "Variables", "estimate": 0.9},
                {"concept_id": "c2", "name": "Functions", "estimate": 0.7},
            ],
            "concerns": [
                {"type": "fast_responses", "severity": "medium"},
            ],
            "recommended_questions": [
                {"concept_id": "c2", "question": "Explain scope"},
            ],
            "key_excerpts": [
                {"type": "breakthrough", "concept_id": "c1"},
            ],
        }

        report = VerificationReport(
            student_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            report_data=report_data,
        )

        assert report.report_data["summary"]["overall_mastery"] == 0.78
        assert len(report.report_data["mastery_by_concept"]) == 2
        assert len(report.report_data["concerns"]) == 1
