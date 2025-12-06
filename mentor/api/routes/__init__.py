"""API routes package."""

from mentor.api.routes import (
    analytics,
    assessment,
    auth,
    courses,
    materials,
    students,
    tutor,
    voice,
)

__all__ = [
    "auth",
    "courses",
    "materials",
    "tutor",
    "students",
    "assessment",
    "analytics",
    "voice",
]
