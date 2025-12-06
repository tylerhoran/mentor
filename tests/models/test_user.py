"""Tests for User and Institution models."""

import uuid

import pytest

from mentor.models.user import Institution, User


class TestInstitution:
    """Tests for Institution model."""

    def test_institution_creation(self):
        """Test creating an institution with required fields."""
        inst = Institution(name="Test University")
        assert inst.name == "Test University"
        assert inst.domain is None

    def test_institution_with_domain(self):
        """Test institution with domain."""
        inst = Institution(name="Test University", domain="test.edu")
        assert inst.domain == "test.edu"

    def test_institution_with_settings(self):
        """Test institution with custom settings."""
        settings = {"theme": "dark", "max_students": 1000}
        inst = Institution(name="Test University", settings=settings)
        assert inst.settings == settings
        assert inst.settings["theme"] == "dark"

    def test_institution_empty_settings(self):
        """Test institution with empty settings."""
        inst = Institution(name="Test University", settings={})
        assert inst.settings == {}


class TestUser:
    """Tests for User model."""

    def test_user_creation(self):
        """Test creating a user with required fields."""
        user = User(email="test@example.com", role="student")
        assert user.email == "test@example.com"
        assert user.role == "student"
        assert user.full_name is None
        assert user.hashed_password is None

    def test_user_with_full_name(self):
        """Test user with full name."""
        user = User(email="test@example.com", role="faculty", full_name="John Doe")
        assert user.full_name == "John Doe"

    def test_is_faculty_property(self):
        """Test is_faculty property."""
        faculty = User(email="faculty@example.com", role="faculty")
        student = User(email="student@example.com", role="student")

        assert faculty.is_faculty is True
        assert student.is_faculty is False

    def test_is_student_property(self):
        """Test is_student property."""
        faculty = User(email="faculty@example.com", role="faculty")
        student = User(email="student@example.com", role="student")

        assert faculty.is_student is False
        assert student.is_student is True

    def test_is_admin_property(self):
        """Test is_admin property."""
        admin = User(email="admin@example.com", role="admin")
        student = User(email="student@example.com", role="student")

        assert admin.is_admin is True
        assert student.is_admin is False

    def test_is_researcher_property(self):
        """Test is_researcher property."""
        researcher = User(email="researcher@example.com", role="researcher")
        student = User(email="student@example.com", role="student")

        assert researcher.is_researcher is True
        assert student.is_researcher is False

    def test_all_roles_mutually_exclusive(self):
        """Test that role properties are mutually exclusive."""
        roles = ["faculty", "student", "admin", "researcher"]

        for role in roles:
            user = User(email=f"{role}@example.com", role=role)
            role_checks = [user.is_faculty, user.is_student, user.is_admin, user.is_researcher]
            assert sum(role_checks) == 1, f"Role {role} should have exactly one True property"

    def test_user_with_institution(self):
        """Test user with institution relationship."""
        inst_id = uuid.uuid4()
        user = User(email="test@example.com", role="student", institution_id=inst_id)
        assert user.institution_id == inst_id
