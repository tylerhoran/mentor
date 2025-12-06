"""Course-related Pydantic schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResponsePattern(BaseModel):
    """Pattern for responding to specific situations."""

    situation: str
    strategies: list[str]


class PedagogyConfigSchema(BaseModel):
    """Pedagogical configuration for a course."""

    style: str = Field(default="socratic", description="Teaching style")
    response_patterns: list[ResponsePattern] = Field(default_factory=list)
    never_do: list[str] = Field(default_factory=list, description="Hard constraints")
    always_do: list[str] = Field(default_factory=list, description="Required behaviors")
    voice_description: str | None = Field(default=None, description="Tone/personality")
    hint_progression: list[str] = Field(default_factory=list)
    max_hints_before_direct: int = Field(default=5)
    probe_on_correct: bool = Field(default=True)


class CourseCreate(BaseModel):
    """Schema for creating a course."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    institution_id: str | None = None
    pedagogy_config: PedagogyConfigSchema | None = None
    base_model: str = Field(default="llama-3.1-8b")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class CourseUpdate(BaseModel):
    """Schema for updating a course."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    pedagogy_config: PedagogyConfigSchema | None = None
    system_prompt_template: str | None = None
    base_model: str | None = None
    adapter_path: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    status: str | None = Field(default=None, pattern="^(draft|active|archived)$")


class CourseResponse(BaseModel):
    """Schema for course response."""

    id: str
    name: str
    description: str | None
    created_by: str
    institution_id: str | None
    pedagogy_config: dict[str, Any]
    system_prompt_template: str | None
    generated_system_prompt: str | None
    base_model: str
    adapter_path: str | None
    temperature: float
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LearningObjective(BaseModel):
    """Learning objective for a concept."""

    description: str
    bloom_level: str | None = None


class ConceptCreate(BaseModel):
    """Schema for creating a concept."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    estimated_time_minutes: int | None = Field(default=None, ge=1)
    difficulty_level: int | None = Field(default=None, ge=1, le=5)
    learning_objectives: list[LearningObjective] = Field(default_factory=list)
    sequence_order: int | None = None


class ConceptUpdate(BaseModel):
    """Schema for updating a concept."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    prerequisites: list[str] | None = None
    estimated_time_minutes: int | None = Field(default=None, ge=1)
    difficulty_level: int | None = Field(default=None, ge=1, le=5)
    learning_objectives: list[LearningObjective] | None = None
    sequence_order: int | None = None


class ConceptResponse(BaseModel):
    """Schema for concept response."""

    id: str
    course_id: str
    name: str
    description: str | None
    prerequisites: list[str]
    estimated_time_minutes: int | None
    difficulty_level: int | None
    learning_objectives: list[dict[str, Any]]
    sequence_order: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MisconceptionCreate(BaseModel):
    """Schema for creating a misconception."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    manifestation: str | None = None
    diagnostic_question: str | None = None
    correction_approach: str | None = None
    example_student_response: str | None = None
    example_tutor_response: str | None = None


class MisconceptionResponse(BaseModel):
    """Schema for misconception response."""

    id: str
    concept_id: str
    name: str
    description: str
    manifestation: str | None
    diagnostic_question: str | None
    correction_approach: str | None
    example_student_response: str | None
    example_tutor_response: str | None
    times_observed: int
    times_resolved: int
    created_at: datetime

    model_config = {"from_attributes": True}
