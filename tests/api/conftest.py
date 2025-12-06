"""Fixtures for API tests."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = Mock()
    session.delete = Mock()
    return session


@pytest.fixture
def sample_user_id():
    """Generate a sample user ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_course_id():
    """Generate a sample course ID."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_student_id():
    """Generate a sample student ID."""
    return str(uuid.uuid4())


@pytest.fixture
def mock_current_user():
    """Create a mock current user."""
    user = Mock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.role = "faculty"
    user.is_faculty = True
    user.is_student = False
    user.is_admin = False
    return user


@pytest.fixture
def mock_student_user():
    """Create a mock student user."""
    user = Mock()
    user.id = uuid.uuid4()
    user.email = "student@example.com"
    user.role = "student"
    user.is_faculty = False
    user.is_student = True
    user.is_admin = False
    return user
