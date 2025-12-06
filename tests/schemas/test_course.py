"""Tests for course schemas."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from mentor.schemas.course import (
    ConceptCreate,
    ConceptResponse,
    ConceptUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    LearningObjective,
    MisconceptionCreate,
    MisconceptionResponse,
    PedagogyConfigSchema,
    ResponsePattern,
)


class TestResponsePattern:
    """Tests for ResponsePattern schema."""

    def test_response_pattern_creation(self):
        """Test creating a response pattern."""
        pattern = ResponsePattern(
            situation="student_confused",
            strategies=["clarify", "use_example", "simplify"],
        )
        assert pattern.situation == "student_confused"
        assert len(pattern.strategies) == 3

    def test_response_pattern_empty_strategies(self):
        """Test response pattern with empty strategies."""
        pattern = ResponsePattern(situation="test", strategies=[])
        assert pattern.strategies == []


class TestPedagogyConfigSchema:
    """Tests for PedagogyConfigSchema."""

    def test_default_values(self):
        """Test default pedagogy config values."""
        config = PedagogyConfigSchema()

        assert config.style == "socratic"
        assert config.response_patterns == []
        assert config.never_do == []
        assert config.always_do == []
        assert config.voice_description is None
        assert config.hint_progression == []
        assert config.max_hints_before_direct == 5
        assert config.probe_on_correct is True

    def test_custom_config(self):
        """Test custom pedagogy config."""
        patterns = [ResponsePattern(situation="confusion", strategies=["clarify"])]
        config = PedagogyConfigSchema(
            style="direct",
            response_patterns=patterns,
            never_do=["give answers directly"],
            always_do=["ask follow-up questions"],
            voice_description="Friendly and patient",
            max_hints_before_direct=3,
            probe_on_correct=False,
        )

        assert config.style == "direct"
        assert len(config.response_patterns) == 1
        assert "give answers directly" in config.never_do
        assert config.max_hints_before_direct == 3


class TestCourseCreate:
    """Tests for CourseCreate schema."""

    def test_minimal_course_create(self):
        """Test creating course with minimal fields."""
        course = CourseCreate(name="Python 101")

        assert course.name == "Python 101"
        assert course.description is None
        assert course.base_model == "llama-3.1-8b"
        assert course.temperature == 0.7

    def test_full_course_create(self):
        """Test creating course with all fields."""
        course = CourseCreate(
            name="Advanced Python",
            description="Deep dive into Python",
            institution_id="inst-123",
            pedagogy_config=PedagogyConfigSchema(style="socratic"),
            base_model="gpt-4",
            temperature=0.5,
        )

        assert course.description == "Deep dive into Python"
        assert course.institution_id == "inst-123"
        assert course.temperature == 0.5

    def test_name_min_length(self):
        """Test name minimum length validation."""
        with pytest.raises(ValidationError):
            CourseCreate(name="")

    def test_name_max_length(self):
        """Test name maximum length validation."""
        with pytest.raises(ValidationError):
            CourseCreate(name="x" * 256)

    def test_temperature_min_value(self):
        """Test temperature minimum value."""
        with pytest.raises(ValidationError):
            CourseCreate(name="Test", temperature=-0.1)

    def test_temperature_max_value(self):
        """Test temperature maximum value."""
        with pytest.raises(ValidationError):
            CourseCreate(name="Test", temperature=2.1)

    def test_temperature_boundary_values(self):
        """Test temperature boundary values are valid."""
        course_min = CourseCreate(name="Test", temperature=0.0)
        course_max = CourseCreate(name="Test", temperature=2.0)

        assert course_min.temperature == 0.0
        assert course_max.temperature == 2.0


class TestCourseUpdate:
    """Tests for CourseUpdate schema."""

    def test_all_fields_optional(self):
        """Test that all fields are optional."""
        update = CourseUpdate()
        assert update.name is None
        assert update.description is None

    def test_partial_update(self):
        """Test partial update with some fields."""
        update = CourseUpdate(name="New Name", temperature=0.8)

        assert update.name == "New Name"
        assert update.temperature == 0.8
        assert update.description is None

    def test_status_validation(self):
        """Test status pattern validation."""
        valid_statuses = ["draft", "active", "archived"]
        for status in valid_statuses:
            update = CourseUpdate(status=status)
            assert update.status == status

    def test_invalid_status(self):
        """Test invalid status is rejected."""
        with pytest.raises(ValidationError):
            CourseUpdate(status="invalid_status")


class TestCourseResponse:
    """Tests for CourseResponse schema."""

    def test_course_response(self):
        """Test course response schema."""
        now = datetime.now(timezone.utc)
        response = CourseResponse(
            id="course-123",
            name="Python 101",
            description="Intro to Python",
            created_by="user-456",
            institution_id=None,
            pedagogy_config={"style": "socratic"},
            system_prompt_template=None,
            generated_system_prompt=None,
            base_model="llama-3.1-8b",
            adapter_path=None,
            temperature=0.7,
            status="active",
            created_at=now,
            updated_at=now,
        )

        assert response.id == "course-123"
        assert response.status == "active"


class TestLearningObjective:
    """Tests for LearningObjective schema."""

    def test_learning_objective(self):
        """Test learning objective creation."""
        obj = LearningObjective(
            description="Understand variable assignment",
            bloom_level="understand",
        )
        assert obj.description == "Understand variable assignment"
        assert obj.bloom_level == "understand"

    def test_bloom_level_optional(self):
        """Test bloom level is optional."""
        obj = LearningObjective(description="Learn something")
        assert obj.bloom_level is None


class TestConceptCreate:
    """Tests for ConceptCreate schema."""

    def test_minimal_concept_create(self):
        """Test creating concept with minimal fields."""
        concept = ConceptCreate(name="Variables")

        assert concept.name == "Variables"
        assert concept.prerequisites == []
        assert concept.learning_objectives == []

    def test_full_concept_create(self):
        """Test creating concept with all fields."""
        objectives = [LearningObjective(description="Understand vars")]
        concept = ConceptCreate(
            name="Functions",
            description="Reusable code blocks",
            prerequisites=["variables", "control-flow"],
            estimated_time_minutes=45,
            difficulty_level=3,
            learning_objectives=objectives,
            sequence_order=5,
        )

        assert concept.description == "Reusable code blocks"
        assert len(concept.prerequisites) == 2
        assert concept.estimated_time_minutes == 45
        assert concept.difficulty_level == 3

    def test_name_validation(self):
        """Test name validation."""
        with pytest.raises(ValidationError):
            ConceptCreate(name="")

    def test_difficulty_level_range(self):
        """Test difficulty level must be 1-5."""
        for level in range(1, 6):
            concept = ConceptCreate(name="Test", difficulty_level=level)
            assert concept.difficulty_level == level

        with pytest.raises(ValidationError):
            ConceptCreate(name="Test", difficulty_level=0)

        with pytest.raises(ValidationError):
            ConceptCreate(name="Test", difficulty_level=6)

    def test_estimated_time_positive(self):
        """Test estimated time must be positive."""
        with pytest.raises(ValidationError):
            ConceptCreate(name="Test", estimated_time_minutes=0)


class TestConceptUpdate:
    """Tests for ConceptUpdate schema."""

    def test_all_fields_optional(self):
        """Test all fields are optional."""
        update = ConceptUpdate()
        assert update.name is None

    def test_partial_update(self):
        """Test partial concept update."""
        update = ConceptUpdate(
            difficulty_level=4,
            estimated_time_minutes=60,
        )
        assert update.difficulty_level == 4
        assert update.name is None


class TestMisconceptionCreate:
    """Tests for MisconceptionCreate schema."""

    def test_minimal_misconception(self):
        """Test creating misconception with required fields."""
        misc = MisconceptionCreate(
            name="Variable Shadowing",
            description="Confusing local and global scope",
        )

        assert misc.name == "Variable Shadowing"
        assert misc.description == "Confusing local and global scope"

    def test_full_misconception(self):
        """Test creating misconception with all fields."""
        misc = MisconceptionCreate(
            name="Off-by-one Error",
            description="Incorrect loop bounds",
            manifestation="Loop iterates one too many times",
            diagnostic_question="What values does i take in range(5)?",
            correction_approach="Walk through loop iterations step by step",
            example_student_response="The loop goes from 1 to 5",
            example_tutor_response="Let's trace through range(5) together...",
        )

        assert misc.manifestation is not None
        assert misc.diagnostic_question is not None
        assert misc.correction_approach is not None

    def test_name_validation(self):
        """Test name cannot be empty."""
        with pytest.raises(ValidationError):
            MisconceptionCreate(name="", description="Test")

    def test_description_validation(self):
        """Test description cannot be empty."""
        with pytest.raises(ValidationError):
            MisconceptionCreate(name="Test", description="")


class TestMisconceptionResponse:
    """Tests for MisconceptionResponse schema."""

    def test_misconception_response(self):
        """Test misconception response includes counters."""
        now = datetime.now(timezone.utc)
        response = MisconceptionResponse(
            id="misc-123",
            concept_id="concept-456",
            name="Test Misconception",
            description="Description",
            manifestation=None,
            diagnostic_question=None,
            correction_approach=None,
            example_student_response=None,
            example_tutor_response=None,
            times_observed=10,
            times_resolved=8,
            created_at=now,
        )

        assert response.times_observed == 10
        assert response.times_resolved == 8
