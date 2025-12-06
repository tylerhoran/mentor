"""Material and MaterialChunk models for course content."""

from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mentor.config import settings
from mentor.models.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from mentor.models.concept import Concept
    from mentor.models.course import Course


class Material(Base, UUIDMixin, TimestampMixin):
    """Uploaded course material."""

    __tablename__ = "materials"

    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Material metadata
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    material_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Original file storage
    original_filename: Mapped[str | None] = mapped_column(String(255))
    file_path: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(100))

    # Processed content
    extracted_text: Mapped[str | None] = mapped_column(Text)
    processed_content: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Concept mapping
    concept_ids: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    # Processing status
    processing_status: Mapped[str] = mapped_column(String(50), default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint(
            "material_type IN ('document', 'lecture_notes', 'slides', 'problem_set', "
            "'worked_example', 'conversation_example', 'reading')",
            name="check_material_type",
        ),
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="materials")
    chunks: Mapped[list["MaterialChunk"]] = relationship(
        "MaterialChunk", back_populates="material", cascade="all, delete-orphan"
    )


class MaterialChunk(Base, UUIDMixin, TimestampMixin):
    """Chunked and embedded material for RAG retrieval."""

    __tablename__ = "material_chunks"

    material_id: Mapped[str] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[str] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[str | None] = mapped_column(
        ForeignKey("concepts.id"),
        index=True,
    )

    # Chunk content
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Metadata for retrieval
    chunk_type: Mapped[str | None] = mapped_column(String(50))
    # Named chunk_metadata to avoid SQLAlchemy reserved name 'metadata'
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)

    # Vector embedding using pgvector
    embedding: Mapped[Any] = mapped_column(Vector(settings.embedding_dimension))

    __table_args__ = (
        Index(
            "idx_material_chunks_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    # Relationships
    material: Mapped["Material"] = relationship("Material", back_populates="chunks")
    course: Mapped["Course"] = relationship("Course")
    concept: Mapped["Concept | None"] = relationship("Concept", back_populates="material_chunks")
