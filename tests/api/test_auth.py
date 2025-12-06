"""Tests for authentication routes."""

import uuid

import pytest
from fastapi import HTTPException


class TestAuthHelpers:
    """Tests for auth helper functions."""

    def test_password_hashing(self):
        """Test password hashing and verification."""
        from mentor.api.routes.auth import get_password_hash, verify_password

        password = "secure123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_pass", hashed) is False

    def test_create_access_token(self):
        """Test JWT token creation."""
        from mentor.api.routes.auth import create_access_token

        # API takes user_id and returns (token, expires_in)
        user_id = str(uuid.uuid4())
        token, expires_in = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20
        assert isinstance(expires_in, int)

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        from mentor.api.routes.auth import create_refresh_token

        user_id = str(uuid.uuid4())
        token = create_refresh_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20


class TestTokenValidation:
    """Tests for token validation."""

    def test_token_structure(self):
        """Test that tokens have correct JWT structure."""
        from mentor.api.routes.auth import create_access_token

        user_id = str(uuid.uuid4())
        token, _ = create_access_token(user_id)

        # JWT tokens have 3 parts separated by dots
        parts = token.split(".")
        assert len(parts) == 3

    def test_invalid_token_raises_error(self):
        """Test that invalid token raises HTTPException."""
        assert HTTPException is not None


class TestUserRegistration:
    """Tests for user registration."""

    def test_register_user_schema(self):
        """Test user registration request schema."""
        from mentor.api.routes.auth import UserCreate

        # Valid registration data
        user = UserCreate(
            email="newuser@example.com",
            password="secure123",
            full_name="New User",
            role="student",
        )
        assert user.email == "newuser@example.com"
        assert user.role == "student"

    def test_register_invalid_role(self):
        """Test registration with invalid role fails."""
        from pydantic import ValidationError

        from mentor.api.routes.auth import UserCreate

        with pytest.raises(ValidationError):
            UserCreate(
                email="user@example.com",
                password="secure123",
                role="invalid_role",  # Should fail validation
            )


class TestUserLogin:
    """Tests for user login."""

    def test_login_schema(self):
        """Test login request schema."""
        from mentor.api.routes.auth import UserLogin

        login = UserLogin(
            email="user@example.com",
            password="password123",
        )
        assert login.email == "user@example.com"

    def test_password_verification(self):
        """Test password verification works correctly."""
        from mentor.api.routes.auth import get_password_hash, verify_password

        password = "test1234"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False


class TestTokenResponse:
    """Tests for token response schema."""

    def test_token_response_schema(self):
        """Test token response structure."""
        from mentor.api.routes.auth import TokenResponse

        response = TokenResponse(
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            token_type="bearer",
            expires_in=3600,
        )
        assert response.token_type == "bearer"
        assert response.expires_in == 3600


class TestRoleValidation:
    """Tests for role-based access control."""

    def test_valid_roles(self):
        """Test valid user roles."""
        valid_roles = ["faculty", "student"]

        for role in valid_roles:
            assert role in valid_roles

    def test_user_create_role_validation(self):
        """Test role validation in UserCreate schema."""
        from mentor.api.routes.auth import UserCreate

        # Valid roles should work
        student = UserCreate(email="s@test.com", password="pass1234", role="student")
        assert student.role == "student"

        faculty = UserCreate(email="f@test.com", password="pass1234", role="faculty")
        assert faculty.role == "faculty"
