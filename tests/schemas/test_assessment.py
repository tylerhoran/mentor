"""Tests for assessment schemas."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from mentor.schemas.assessment import (
    GamingFlag,
    InteractionExcerpt,
    MasteryEstimate,
    TrajectoryAnalysis,
    VerificationQuestion,
    VerificationReportCreate,
    VerificationReportResponse,
    VerificationResults,
)


class TestMasteryEstimate:
    """Tests for MasteryEstimate schema."""

    def test_mastery_estimate_creation(self):
        """Test creating a mastery estimate."""
        now = datetime.now(UTC)
        estimate = MasteryEstimate(
            concept_id="concept-123",
            concept_name="Variables",
            estimate=0.85,
            confidence=0.9,
            interaction_count=15,
            last_updated=now,
        )

        assert estimate.concept_id == "concept-123"
        assert estimate.estimate == 0.85
        assert estimate.confidence == 0.9

    def test_estimate_bounds(self):
        """Test estimate must be between 0 and 1."""
        now = datetime.now(UTC)

        # Valid bounds
        MasteryEstimate(
            concept_id="c1",
            concept_name="Test",
            estimate=0.0,
            confidence=0.5,
            interaction_count=1,
            last_updated=now,
        )
        MasteryEstimate(
            concept_id="c1",
            concept_name="Test",
            estimate=1.0,
            confidence=0.5,
            interaction_count=1,
            last_updated=now,
        )

        # Invalid bounds
        with pytest.raises(ValidationError):
            MasteryEstimate(
                concept_id="c1",
                concept_name="Test",
                estimate=-0.1,
                confidence=0.5,
                interaction_count=1,
                last_updated=now,
            )

        with pytest.raises(ValidationError):
            MasteryEstimate(
                concept_id="c1",
                concept_name="Test",
                estimate=1.1,
                confidence=0.5,
                interaction_count=1,
                last_updated=now,
            )

    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        now = datetime.now(UTC)

        with pytest.raises(ValidationError):
            MasteryEstimate(
                concept_id="c1",
                concept_name="Test",
                estimate=0.5,
                confidence=-0.1,
                interaction_count=1,
                last_updated=now,
            )

        with pytest.raises(ValidationError):
            MasteryEstimate(
                concept_id="c1",
                concept_name="Test",
                estimate=0.5,
                confidence=1.1,
                interaction_count=1,
                last_updated=now,
            )


class TestGamingFlag:
    """Tests for GamingFlag schema."""

    def test_gaming_flag_creation(self):
        """Test creating a gaming flag."""
        now = datetime.now(UTC)
        flag = GamingFlag(
            type="fast_response",
            severity="medium",
            timestamp=now,
            evidence="Response time of 2 seconds for complex question",
        )

        assert flag.type == "fast_response"
        assert flag.severity == "medium"
        assert flag.resolved is False

    def test_severity_validation(self):
        """Test severity pattern validation."""
        now = datetime.now(UTC)

        # Valid severities
        for severity in ["low", "medium", "high"]:
            flag = GamingFlag(
                type="test",
                severity=severity,
                timestamp=now,
                evidence="test",
            )
            assert flag.severity == severity

        # Invalid severity
        with pytest.raises(ValidationError):
            GamingFlag(
                type="test",
                severity="critical",
                timestamp=now,
                evidence="test",
            )

    def test_gaming_flag_resolved(self):
        """Test resolved flag."""
        now = datetime.now(UTC)
        flag = GamingFlag(
            type="test",
            severity="low",
            timestamp=now,
            evidence="test",
            resolved=True,
        )
        assert flag.resolved is True

    def test_gaming_flag_interaction_id(self):
        """Test optional interaction ID."""
        now = datetime.now(UTC)
        flag = GamingFlag(
            type="test",
            severity="low",
            timestamp=now,
            evidence="test",
            interaction_id="interaction-123",
        )
        assert flag.interaction_id == "interaction-123"


class TestTrajectoryAnalysis:
    """Tests for TrajectoryAnalysis schema."""

    def test_trajectory_analysis_creation(self):
        """Test creating trajectory analysis."""
        now = datetime.now(UTC)
        analysis = TrajectoryAnalysis(
            student_id="student-123",
            course_id="course-456",
            classification="genuine",
            confidence=0.85,
            gaming_flags=[],
            analysis_summary="Student shows consistent learning progress",
            analyzed_at=now,
        )

        assert analysis.classification == "genuine"
        assert analysis.confidence == 0.85

    def test_classification_validation(self):
        """Test classification pattern validation."""
        now = datetime.now(UTC)

        # Valid classifications
        for classification in ["genuine", "suspected_gaming", "unclear"]:
            analysis = TrajectoryAnalysis(
                student_id="s1",
                course_id="c1",
                classification=classification,
                confidence=0.5,
                gaming_flags=[],
                analysis_summary="Test",
                analyzed_at=now,
            )
            assert analysis.classification == classification

        # Invalid classification
        with pytest.raises(ValidationError):
            TrajectoryAnalysis(
                student_id="s1",
                course_id="c1",
                classification="cheating",
                confidence=0.5,
                gaming_flags=[],
                analysis_summary="Test",
                analyzed_at=now,
            )

    def test_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        now = datetime.now(UTC)

        with pytest.raises(ValidationError):
            TrajectoryAnalysis(
                student_id="s1",
                course_id="c1",
                classification="genuine",
                confidence=1.5,
                gaming_flags=[],
                analysis_summary="Test",
                analyzed_at=now,
            )


class TestVerificationQuestion:
    """Tests for VerificationQuestion schema."""

    def test_verification_question_creation(self):
        """Test creating a verification question."""
        question = VerificationQuestion(
            concept_id="concept-123",
            concept_name="Recursion",
            question="Explain how recursion works",
            rationale="Student showed sudden mastery jump",
            look_for="Clear explanation of base case and recursive case",
        )

        assert question.concept_id == "concept-123"
        assert question.difficulty == "medium"  # default

    def test_difficulty_validation(self):
        """Test difficulty pattern validation."""
        for difficulty in ["easy", "medium", "hard"]:
            question = VerificationQuestion(
                concept_id="c1",
                concept_name="Test",
                question="Test?",
                rationale="Test",
                look_for="Test",
                difficulty=difficulty,
            )
            assert question.difficulty == difficulty

        with pytest.raises(ValidationError):
            VerificationQuestion(
                concept_id="c1",
                concept_name="Test",
                question="Test?",
                rationale="Test",
                look_for="Test",
                difficulty="very_hard",
            )


class TestInteractionExcerpt:
    """Tests for InteractionExcerpt schema."""

    def test_interaction_excerpt_creation(self):
        """Test creating an interaction excerpt."""
        now = datetime.now(UTC)
        excerpt = InteractionExcerpt(
            type="breakthrough",
            concept_id="concept-123",
            interactions=[
                {"student": "Oh I get it now!", "tutor": "Great!"},
            ],
            note="Student had aha moment",
            timestamp=now,
        )

        assert excerpt.type == "breakthrough"
        assert len(excerpt.interactions) == 1

    def test_type_validation(self):
        """Test type pattern validation."""
        now = datetime.now(UTC)

        for excerpt_type in ["breakthrough", "struggle", "gaming_flag"]:
            excerpt = InteractionExcerpt(
                type=excerpt_type,
                concept_id="c1",
                interactions=[],
                note="Test",
                timestamp=now,
            )
            assert excerpt.type == excerpt_type

        with pytest.raises(ValidationError):
            InteractionExcerpt(
                type="confusion",
                concept_id="c1",
                interactions=[],
                note="Test",
                timestamp=now,
            )


class TestVerificationReportCreate:
    """Tests for VerificationReportCreate schema."""

    def test_default_values(self):
        """Test default values."""
        create = VerificationReportCreate()

        assert create.include_excerpts is True
        assert create.max_questions == 10

    def test_max_questions_bounds(self):
        """Test max_questions bounds."""
        VerificationReportCreate(max_questions=1)
        VerificationReportCreate(max_questions=20)

        with pytest.raises(ValidationError):
            VerificationReportCreate(max_questions=0)

        with pytest.raises(ValidationError):
            VerificationReportCreate(max_questions=21)


class TestVerificationResults:
    """Tests for VerificationResults schema."""

    def test_verification_results_creation(self):
        """Test creating verification results."""
        results = VerificationResults(
            assessment_scores={"concept-1": 0.9, "concept-2": 0.75},
            overall_assessment="mastery",
            verification_notes="Student demonstrates excellent understanding",
        )

        assert results.overall_assessment == "mastery"
        assert results.assessment_scores["concept-1"] == 0.9

    def test_overall_assessment_validation(self):
        """Test overall assessment pattern validation."""
        valid_assessments = ["mastery", "partial", "insufficient", "gaming_suspected"]

        for assessment in valid_assessments:
            results = VerificationResults(
                assessment_scores={},
                overall_assessment=assessment,
            )
            assert results.overall_assessment == assessment

        with pytest.raises(ValidationError):
            VerificationResults(
                assessment_scores={},
                overall_assessment="excellent",
            )

    def test_notes_optional(self):
        """Test verification notes are optional."""
        results = VerificationResults(
            assessment_scores={},
            overall_assessment="mastery",
        )
        assert results.verification_notes is None


class TestVerificationReportResponse:
    """Tests for VerificationReportResponse schema."""

    def test_verification_report_response(self):
        """Test verification report response."""
        now = datetime.now(UTC)
        response = VerificationReportResponse(
            id="report-123",
            student_id="student-456",
            course_id="course-789",
            generated_at=now,
            verification_status="pending",
            verified_by=None,
            verified_at=None,
            verification_notes=None,
            summary={"overall_mastery": 0.75},
            mastery_by_concept=[],
            concerns=[],
            recommended_questions=[],
            key_excerpts=[],
            assessment_scores=None,
            overall_assessment=None,
        )

        assert response.id == "report-123"
        assert response.verification_status == "pending"
