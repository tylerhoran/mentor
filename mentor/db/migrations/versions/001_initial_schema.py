"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # Institutions table
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255)),
        sa.Column("settings", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("full_name", sa.String(255)),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("institutions.id"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "role IN ('faculty', 'student', 'admin', 'researcher')",
            name="check_user_role",
        ),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_institution", "users", ["institution_id"])

    # Courses table
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("institutions.id"),
        ),
        sa.Column(
            "pedagogy_config",
            postgresql.JSONB,
            nullable=False,
            server_default='{"style": "socratic", "response_patterns": {}, "boundaries": {"never_do": [], "always_do": []}, "voice_description": null}',
        ),
        sa.Column("system_prompt_template", sa.Text),
        sa.Column("generated_system_prompt", sa.Text),
        sa.Column("base_model", sa.String(100), server_default="llama-3.1-8b"),
        sa.Column("adapter_path", sa.String(255)),
        sa.Column("temperature", sa.Float, server_default="0.7"),
        sa.Column("status", sa.String(50), server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'archived')",
            name="check_course_status",
        ),
    )
    op.create_index("idx_courses_created_by", "courses", ["created_by"])
    op.create_index("idx_courses_institution", "courses", ["institution_id"])

    # Concepts table
    op.create_table(
        "concepts",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("prerequisites", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("estimated_time_minutes", sa.Integer),
        sa.Column("difficulty_level", sa.Integer),
        sa.Column("learning_objectives", postgresql.JSONB, server_default="[]"),
        sa.Column("sequence_order", sa.Integer),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("course_id", "name", name="uq_course_concept_name"),
        sa.CheckConstraint(
            "difficulty_level IS NULL OR (difficulty_level >= 1 AND difficulty_level <= 5)",
            name="check_difficulty_level",
        ),
    )
    op.create_index("idx_concepts_course", "concepts", ["course_id"])

    # Misconceptions table
    op.create_table(
        "misconceptions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "concept_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("concepts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("manifestation", sa.Text),
        sa.Column("diagnostic_question", sa.Text),
        sa.Column("correction_approach", sa.Text),
        sa.Column("example_student_response", sa.Text),
        sa.Column("example_tutor_response", sa.Text),
        sa.Column("times_observed", sa.Integer, server_default="0"),
        sa.Column("times_resolved", sa.Integer, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_misconceptions_concept", "misconceptions", ["concept_id"])

    # Materials table
    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("material_type", sa.String(50), nullable=False),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("file_path", sa.String(500)),
        sa.Column("mime_type", sa.String(100)),
        sa.Column("extracted_text", sa.Text),
        sa.Column("processed_content", postgresql.JSONB),
        sa.Column("concept_ids", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("processing_status", sa.String(50), server_default="pending"),
        sa.Column("processing_error", sa.Text),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "material_type IN ('document', 'lecture_notes', 'slides', 'problem_set', "
            "'worked_example', 'conversation_example', 'reading')",
            name="check_material_type",
        ),
    )
    op.create_index("idx_materials_course", "materials", ["course_id"])

    # Material chunks table
    op.create_table(
        "material_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "material_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "concept_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("concepts.id"),
        ),
        sa.Column("chunk_text", sa.Text, nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("chunk_type", sa.String(50)),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("embedding", Vector(384)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_material_chunks_material", "material_chunks", ["material_id"])
    op.create_index("idx_material_chunks_course", "material_chunks", ["course_id"])
    op.create_index("idx_material_chunks_concept", "material_chunks", ["concept_id"])
    # Vector index for similarity search
    op.execute(
        "CREATE INDEX idx_material_chunks_embedding ON material_chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # Course enrollments table
    op.create_table(
        "course_enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("study_condition", sa.String(50)),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("course_id", "student_id", name="uq_course_enrollment"),
    )
    op.create_index("idx_enrollments_course", "course_enrollments", ["course_id"])
    op.create_index("idx_enrollments_student", "course_enrollments", ["student_id"])

    # Student states table
    op.create_table(
        "student_states",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concept_mastery", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "engagement_metrics",
            postgresql.JSONB,
            nullable=False,
            server_default='{"total_interactions": 0, "total_time_seconds": 0, "average_response_time_ms": null, "session_count": 0, "last_session_at": null}',
        ),
        sa.Column("gaming_flags", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column(
            "current_concept_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("concepts.id"),
        ),
        sa.Column("concepts_completed", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("student_id", "course_id", name="uq_student_course"),
    )
    op.create_index("idx_student_states_student", "student_states", ["student_id"])
    op.create_index("idx_student_states_course", "student_states", ["course_id"])

    # Interactions table
    op.create_table(
        "interactions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id"),
            nullable=False,
        ),
        sa.Column("session_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column(
            "concept_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("concepts.id"),
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("response_time_ms", sa.Integer),
        sa.Column("student_message", sa.Text, nullable=False),
        sa.Column("tutor_response", sa.Text, nullable=False),
        sa.Column("pedagogical_move", sa.String(50)),
        sa.Column("student_message_type", sa.String(50)),
        sa.Column("response_quality", sa.String(50)),
        sa.Column(
            "misconception_observed",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("misconceptions.id"),
        ),
        sa.Column("misconception_addressed", sa.Boolean, server_default="false"),
        sa.Column("gaming_signals", postgresql.JSONB, server_default="[]"),
        sa.Column("retrieved_chunks", postgresql.ARRAY(sa.String), server_default="{}"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_interactions_student_course", "interactions", ["student_id", "course_id"])
    op.create_index("idx_interactions_session", "interactions", ["session_id"])
    op.create_index("idx_interactions_timestamp", "interactions", ["timestamp"])
    op.create_index("idx_interactions_concept", "interactions", ["concept_id"])

    # Verification reports table
    op.create_table(
        "verification_reports",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("report_data", postgresql.JSONB, nullable=False),
        sa.Column("verification_status", sa.String(50), server_default="pending"),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("users.id"),
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("verification_notes", sa.Text),
        sa.Column("assessment_scores", postgresql.JSONB),
        sa.Column("overall_assessment", sa.String(50)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_verification_reports_student", "verification_reports", ["student_id"])
    op.create_index("idx_verification_reports_course", "verification_reports", ["course_id"])


def downgrade() -> None:
    op.drop_table("verification_reports")
    op.drop_table("interactions")
    op.drop_table("student_states")
    op.drop_table("course_enrollments")
    op.drop_table("material_chunks")
    op.drop_table("materials")
    op.drop_table("misconceptions")
    op.drop_table("concepts")
    op.drop_table("courses")
    op.drop_table("users")
    op.drop_table("institutions")
