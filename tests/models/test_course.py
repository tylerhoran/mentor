"""Tests for Course and CourseEnrollment models."""

import uuid

import pytest

from mentor.models.course import Course, CourseEnrollment


class TestCourse:
    """Tests for Course model."""

    def test_course_creation(self):
        """Test creating a course with required fields."""
        creator_id = uuid.uuid4()
        course = Course(name="Introduction to Python", created_by=creator_id)

        assert course.name == "Introduction to Python"
        assert course.created_by == creator_id
        assert course.description is None

    def test_course_with_status(self):
        """Test course with explicit status."""
        course = Course(name="Test Course", created_by=uuid.uuid4(), status="draft")
        assert course.status == "draft"

    def test_course_with_model_settings(self):
        """Test course with model settings."""
        course = Course(
            name="Test Course",
            created_by=uuid.uuid4(),
            base_model="llama-3.1-8b",
            temperature=0.7,
        )

        assert course.base_model == "llama-3.1-8b"
        assert course.temperature == 0.7
        assert course.adapter_path is None

    def test_course_with_description(self):
        """Test course with description."""
        course = Course(
            name="Test Course",
            created_by=uuid.uuid4(),
            description="A comprehensive course on testing",
        )
        assert course.description == "A comprehensive course on testing"

    def test_course_pedagogy_config(self):
        """Test pedagogy config structure."""
        config = {"style": "socratic"}
        course = Course(name="Test Course", created_by=uuid.uuid4(), pedagogy_config=config)

        assert isinstance(course.pedagogy_config, dict)
        assert course.pedagogy_config["style"] == "socratic"

    def test_course_custom_pedagogy_config(self):
        """Test custom pedagogy config."""
        config = {
            "style": "socratic",
            "response_patterns": [{"situation": "confusion", "strategies": ["clarify"]}],
            "boundaries": ["no direct answers"],
            "voice_description": "friendly and patient",
        }
        course = Course(
            name="Test Course",
            created_by=uuid.uuid4(),
            pedagogy_config=config,
        )
        assert course.pedagogy_config["style"] == "socratic"
        assert course.pedagogy_config["voice_description"] == "friendly and patient"

    def test_course_status_values(self):
        """Test valid course status values."""
        creator_id = uuid.uuid4()

        for status in ["draft", "active", "archived"]:
            course = Course(name="Test Course", created_by=creator_id, status=status)
            assert course.status == status

    def test_course_with_institution(self):
        """Test course with institution."""
        course = Course(
            name="Test Course",
            created_by=uuid.uuid4(),
            institution_id=uuid.uuid4(),
        )
        assert course.institution_id is not None

    def test_course_custom_temperature(self):
        """Test course with custom temperature."""
        course = Course(
            name="Test Course",
            created_by=uuid.uuid4(),
            temperature=0.5,
        )
        assert course.temperature == 0.5

    def test_course_with_adapter(self):
        """Test course with custom adapter path."""
        course = Course(
            name="Test Course",
            created_by=uuid.uuid4(),
            adapter_path="/models/custom-adapter",
        )
        assert course.adapter_path == "/models/custom-adapter"


class TestCourseEnrollment:
    """Tests for CourseEnrollment model."""

    def test_enrollment_creation(self):
        """Test creating an enrollment."""
        course_id = uuid.uuid4()
        student_id = uuid.uuid4()

        enrollment = CourseEnrollment(course_id=course_id, student_id=student_id)

        assert enrollment.course_id == course_id
        assert enrollment.student_id == student_id
        assert enrollment.study_condition is None

    def test_enrollment_with_study_condition(self):
        """Test enrollment with study condition for research."""
        enrollment = CourseEnrollment(
            course_id=uuid.uuid4(),
            student_id=uuid.uuid4(),
            study_condition="control",
        )
        assert enrollment.study_condition == "control"

    def test_enrollment_study_conditions(self):
        """Test various study conditions."""
        conditions = ["control", "treatment_a", "treatment_b", "baseline"]

        for condition in conditions:
            enrollment = CourseEnrollment(
                course_id=uuid.uuid4(),
                student_id=uuid.uuid4(),
                study_condition=condition,
            )
            assert enrollment.study_condition == condition
