"""Fixtures for model tests."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.delete = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def sample_uuid():
    """Generate a sample UUID."""
    return uuid.uuid4()


@pytest.fixture
def sample_timestamp():
    """Generate a sample timestamp."""
    return datetime.now(timezone.utc)
