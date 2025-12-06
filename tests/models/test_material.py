"""Tests for Material and MaterialChunk models."""

import uuid

import pytest

from mentor.models.material import Material, MaterialChunk


class TestMaterial:
    """Tests for Material model."""

    def test_material_creation(self):
        """Test creating a material with required fields."""
        course_id = uuid.uuid4()
        material = Material(
            course_id=course_id,
            title="Chapter 1: Introduction",
            material_type="document",
        )

        assert material.course_id == course_id
        assert material.title == "Chapter 1: Introduction"
        assert material.material_type == "document"

    def test_material_types(self):
        """Test valid material types."""
        valid_types = [
            "document",
            "lecture_notes",
            "slides",
            "problem_set",
            "worked_example",
            "conversation_example",
            "reading",
        ]

        for mat_type in valid_types:
            material = Material(
                course_id=uuid.uuid4(),
                title=f"Test {mat_type}",
                material_type=mat_type,
            )
            assert material.material_type == mat_type

    def test_material_file_metadata(self):
        """Test material with file metadata."""
        material = Material(
            course_id=uuid.uuid4(),
            title="Lecture Notes",
            material_type="lecture_notes",
            original_filename="lecture_01.pdf",
            file_path="/uploads/lecture_01.pdf",
            mime_type="application/pdf",
        )

        assert material.original_filename == "lecture_01.pdf"
        assert material.file_path == "/uploads/lecture_01.pdf"
        assert material.mime_type == "application/pdf"

    def test_material_extracted_text(self):
        """Test material with extracted text."""
        material = Material(
            course_id=uuid.uuid4(),
            title="Document",
            material_type="document",
            extracted_text="This is the extracted content from the PDF.",
        )
        assert material.extracted_text is not None

    def test_material_processed_content(self):
        """Test material with processed content."""
        processed = {
            "sections": [{"title": "Intro", "content": "..."}],
            "word_count": 1500,
        }
        material = Material(
            course_id=uuid.uuid4(),
            title="Document",
            material_type="document",
            processed_content=processed,
        )
        assert material.processed_content["word_count"] == 1500

    def test_material_concept_mapping(self):
        """Test material with concept IDs."""
        concept_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        material = Material(
            course_id=uuid.uuid4(),
            title="Document",
            material_type="document",
            concept_ids=concept_ids,
        )
        assert len(material.concept_ids) == 2

    def test_material_empty_concept_ids(self):
        """Test material with empty concept_ids list."""
        material = Material(
            course_id=uuid.uuid4(),
            title="Document",
            material_type="document",
            concept_ids=[],
        )
        assert material.concept_ids == []

    def test_material_processing_status(self):
        """Test processing status workflow."""
        statuses = ["pending", "processing", "completed", "error"]

        for status in statuses:
            material = Material(
                course_id=uuid.uuid4(),
                title="Document",
                material_type="document",
                processing_status=status,
            )
            assert material.processing_status == status

    def test_material_processing_error(self):
        """Test material with processing error."""
        material = Material(
            course_id=uuid.uuid4(),
            title="Document",
            material_type="document",
            processing_status="error",
            processing_error="Failed to extract text from PDF",
        )
        assert material.processing_error is not None


class TestMaterialChunk:
    """Tests for MaterialChunk model."""

    def test_chunk_creation(self):
        """Test creating a material chunk."""
        material_id = uuid.uuid4()
        course_id = uuid.uuid4()

        chunk = MaterialChunk(
            material_id=material_id,
            course_id=course_id,
            chunk_text="This is a chunk of text from the material.",
            chunk_index=0,
        )

        assert chunk.material_id == material_id
        assert chunk.course_id == course_id
        assert chunk.chunk_index == 0
        assert "chunk of text" in chunk.chunk_text

    def test_chunk_with_concept(self):
        """Test chunk linked to a concept."""
        concept_id = uuid.uuid4()
        chunk = MaterialChunk(
            material_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            chunk_text="Content about variables",
            chunk_index=0,
            concept_id=concept_id,
        )
        assert chunk.concept_id == concept_id

    def test_chunk_types(self):
        """Test different chunk types."""
        chunk_types = ["explanation", "example", "code", "definition", "exercise"]

        for ct in chunk_types:
            chunk = MaterialChunk(
                material_id=uuid.uuid4(),
                course_id=uuid.uuid4(),
                chunk_text="Some content",
                chunk_index=0,
                chunk_type=ct,
            )
            assert chunk.chunk_type == ct

    def test_chunk_metadata(self):
        """Test chunk with metadata."""
        metadata = {
            "source_page": 5,
            "heading": "Introduction",
            "has_code": True,
        }
        chunk = MaterialChunk(
            material_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            chunk_text="Content",
            chunk_index=0,
            chunk_metadata=metadata,
        )
        assert chunk.chunk_metadata["source_page"] == 5
        assert chunk.chunk_metadata["has_code"] is True

    def test_chunk_empty_metadata(self):
        """Test chunk with empty metadata."""
        chunk = MaterialChunk(
            material_id=uuid.uuid4(),
            course_id=uuid.uuid4(),
            chunk_text="Content",
            chunk_index=0,
            chunk_metadata={},
        )
        assert chunk.chunk_metadata == {}

    def test_chunk_ordering(self):
        """Test chunks maintain ordering via chunk_index."""
        material_id = uuid.uuid4()
        course_id = uuid.uuid4()

        chunks = []
        for i in range(5):
            chunk = MaterialChunk(
                material_id=material_id,
                course_id=course_id,
                chunk_text=f"Chunk {i}",
                chunk_index=i,
            )
            chunks.append(chunk)

        # Verify ordering
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i
