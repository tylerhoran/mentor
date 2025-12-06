"""Tests for Concept and Misconception models."""

import uuid

import pytest

from mentor.models.concept import Concept, Misconception


class TestConcept:
    """Tests for Concept model."""

    def test_concept_creation(self):
        """Test creating a concept with required fields."""
        course_id = uuid.uuid4()
        concept = Concept(course_id=course_id, name="Variables")

        assert concept.course_id == course_id
        assert concept.name == "Variables"

    def test_concept_with_description(self):
        """Test concept with description."""
        concept = Concept(
            course_id=uuid.uuid4(),
            name="Functions",
            description="Reusable blocks of code",
        )
        assert concept.description == "Reusable blocks of code"

    def test_concept_with_prerequisites(self):
        """Test concept with prerequisites."""
        prereq_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        concept = Concept(
            course_id=uuid.uuid4(),
            name="Recursion",
            prerequisites=prereq_ids,
        )
        assert len(concept.prerequisites) == 2

    def test_concept_difficulty_levels(self):
        """Test valid difficulty levels (1-5)."""
        for level in range(1, 6):
            concept = Concept(
                course_id=uuid.uuid4(),
                name=f"Concept Level {level}",
                difficulty_level=level,
            )
            assert concept.difficulty_level == level

    def test_concept_estimated_time(self):
        """Test estimated time in minutes."""
        concept = Concept(
            course_id=uuid.uuid4(),
            name="Quick Concept",
            estimated_time_minutes=30,
        )
        assert concept.estimated_time_minutes == 30

    def test_concept_learning_objectives(self):
        """Test learning objectives structure."""
        objectives = [
            {"description": "Understand variables", "bloom_level": "understand"},
            {"description": "Apply variables in code", "bloom_level": "apply"},
        ]
        concept = Concept(
            course_id=uuid.uuid4(),
            name="Variables",
            learning_objectives=objectives,
        )
        assert len(concept.learning_objectives) == 2

    def test_concept_sequence_order(self):
        """Test concept sequence ordering."""
        concept = Concept(
            course_id=uuid.uuid4(),
            name="First Concept",
            sequence_order=1,
        )
        assert concept.sequence_order == 1


class TestMisconception:
    """Tests for Misconception model."""

    def test_misconception_creation(self):
        """Test creating a misconception with required fields."""
        concept_id = uuid.uuid4()
        misconception = Misconception(
            concept_id=concept_id,
            name="Variable Shadowing Confusion",
            description="Student confuses local and global variables",
        )

        assert misconception.concept_id == concept_id
        assert misconception.name == "Variable Shadowing Confusion"

    def test_misconception_with_manifestation(self):
        """Test misconception with manifestation."""
        misconception = Misconception(
            concept_id=uuid.uuid4(),
            name="Test Misconception",
            description="Test description",
            manifestation="Student uses global variable name inside function",
        )
        assert misconception.manifestation is not None

    def test_misconception_diagnostic_question(self):
        """Test misconception with diagnostic question."""
        misconception = Misconception(
            concept_id=uuid.uuid4(),
            name="Test Misconception",
            description="Test description",
            diagnostic_question="What happens when you define a variable inside a function?",
        )
        assert misconception.diagnostic_question is not None

    def test_misconception_correction_approach(self):
        """Test misconception with correction approach."""
        misconception = Misconception(
            concept_id=uuid.uuid4(),
            name="Test Misconception",
            description="Test description",
            correction_approach="Use visual diagrams to show variable scope",
        )
        assert misconception.correction_approach is not None

    def test_misconception_default_counters(self):
        """Test observation counters with explicit zero values."""
        misconception = Misconception(
            concept_id=uuid.uuid4(),
            name="Test Misconception",
            description="Test description",
            times_observed=0,
            times_resolved=0,
        )
        assert misconception.times_observed == 0
        assert misconception.times_resolved == 0

    def test_misconception_counter_tracking(self):
        """Test observation and resolution counters."""
        misconception = Misconception(
            concept_id=uuid.uuid4(),
            name="Test Misconception",
            description="Test description",
            times_observed=10,
            times_resolved=7,
        )
        assert misconception.times_observed == 10
        assert misconception.times_resolved == 7
