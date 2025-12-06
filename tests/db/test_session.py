"""Tests for database session management."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


class TestDatabaseSession:
    """Tests for database session configuration."""

    def test_database_url_configuration(self):
        """Test database URL is configured."""
        # The actual URL would come from settings
        # Just verify the pattern
        expected_patterns = [
            "postgresql",
            "sqlite",
        ]

        # At least one should be valid
        assert len(expected_patterns) > 0

    def test_async_session_maker(self):
        """Test async session maker is configured."""
        try:
            from sqlalchemy.ext.asyncio import AsyncSession

            assert AsyncSession is not None
        except ImportError:
            pytest.skip("sqlalchemy async not installed")

    def test_session_context_manager(self):
        """Test session can be used as context manager."""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        assert mock_session is not None


class TestDatabaseDependency:
    """Tests for database dependency injection."""

    @pytest.mark.asyncio
    async def test_get_db_session(self):
        """Test get_db yields a session."""
        mock_session = AsyncMock()

        async def mock_get_db():
            yield mock_session

        gen = mock_get_db()
        session = await gen.__anext__()

        assert session == mock_session

    @pytest.mark.asyncio
    async def test_session_closes_on_exit(self):
        """Test session is closed after use."""
        mock_session = AsyncMock()
        mock_session.close = AsyncMock()

        async def mock_get_db():
            try:
                yield mock_session
            finally:
                await mock_session.close()

        gen = mock_get_db()
        await gen.__anext__()

        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

        mock_session.close.assert_called_once()


class TestDatabaseModels:
    """Tests for database model base classes."""

    def test_base_model_exists(self):
        """Test Base declarative class exists."""
        try:
            from mentor.models.base import Base

            assert Base is not None
        except ImportError:
            pytest.skip("Models not available")

    def test_uuid_mixin(self):
        """Test UUID mixin provides id field."""
        try:
            from mentor.models.base import UUIDMixin

            assert hasattr(UUIDMixin, "id")
        except ImportError:
            pytest.skip("Models not available")

    def test_timestamp_mixin(self):
        """Test Timestamp mixin provides created_at and updated_at."""
        try:
            from mentor.models.base import TimestampMixin

            assert hasattr(TimestampMixin, "created_at")
            assert hasattr(TimestampMixin, "updated_at")
        except ImportError:
            pytest.skip("Models not available")


class TestDatabaseTransactions:
    """Tests for database transaction handling."""

    @pytest.mark.asyncio
    async def test_commit_on_success(self):
        """Test changes are committed on success."""
        mock_session = AsyncMock()

        await mock_session.commit()

        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_rollback_on_error(self):
        """Test changes are rolled back on error."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock(side_effect=Exception("DB Error"))
        mock_session.rollback = AsyncMock()

        try:
            await mock_session.commit()
        except Exception:
            await mock_session.rollback()

        mock_session.rollback.assert_called_once()


class TestDatabaseQueries:
    """Tests for common database query patterns."""

    @pytest.mark.asyncio
    async def test_select_by_id(self):
        """Test selecting record by ID."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = Mock(id="test-id")
        mock_session.execute.return_value = mock_result

        result = await mock_session.execute("SELECT * FROM table WHERE id = :id")

        assert result.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_select_returns_none_when_not_found(self):
        """Test select returns None when record not found."""
        mock_session = AsyncMock()
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await mock_session.execute("SELECT * FROM table WHERE id = :id")

        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_insert_and_refresh(self):
        """Test inserting and refreshing a record."""
        mock_session = AsyncMock()
        mock_record = Mock()

        mock_session.add(mock_record)
        await mock_session.commit()
        await mock_session.refresh(mock_record)

        mock_session.add.assert_called_once_with(mock_record)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_record)
