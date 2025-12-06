"""
Process uploaded materials into retrievable chunks.

Supports:
- PDF extraction (text, tables)
- Word documents
- Markdown
- Plain text
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class DocumentProcessor(ABC):
    """Abstract base class for document processors."""

    @abstractmethod
    async def extract_text(self, file_path: Path) -> str:
        """Extract plain text from the document."""
        pass

    @abstractmethod
    async def extract_structure(self, file_path: Path) -> dict[str, Any]:
        """Extract structured content (sections, headers, etc.)."""
        pass

    def get_mime_type(self) -> str:
        """Get the MIME type this processor handles."""
        return "application/octet-stream"


class PDFProcessor(DocumentProcessor):
    """Process PDF documents using pypdf."""

    def get_mime_type(self) -> str:
        return "application/pdf"

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from PDF."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []

            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

            return "\n\n".join(text_parts)
        except Exception as e:
            logger.error("pdf_extraction_failed", file=str(file_path), error=str(e))
            raise

    async def extract_structure(self, file_path: Path) -> dict[str, Any]:
        """Extract structured content from PDF."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))

            structure = {
                "pages": [],
                "metadata": dict(reader.metadata) if reader.metadata else {},
                "total_pages": len(reader.pages),
            }

            for i, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                structure["pages"].append(
                    {
                        "page_number": i + 1,
                        "text": page_text,
                        "char_count": len(page_text),
                    }
                )

            return structure
        except Exception as e:
            logger.error("pdf_structure_extraction_failed", file=str(file_path), error=str(e))
            raise


class DocxProcessor(DocumentProcessor):
    """Process Word documents using python-docx."""

    def get_mime_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document

            doc = Document(str(file_path))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error("docx_extraction_failed", file=str(file_path), error=str(e))
            raise

    async def extract_structure(self, file_path: Path) -> dict[str, Any]:
        """Extract structured content from DOCX."""
        try:
            from docx import Document

            doc = Document(str(file_path))

            structure = {
                "sections": [],
                "tables": [],
                "metadata": {},
            }

            current_section = {"heading": None, "paragraphs": []}

            for para in doc.paragraphs:
                if para.style.name.startswith("Heading"):
                    # Save previous section
                    if current_section["paragraphs"]:
                        structure["sections"].append(current_section)
                    current_section = {
                        "heading": para.text,
                        "heading_level": int(para.style.name[-1])
                        if para.style.name[-1].isdigit()
                        else 1,
                        "paragraphs": [],
                    }
                elif para.text.strip():
                    current_section["paragraphs"].append(para.text)

            # Save last section
            if current_section["paragraphs"] or current_section["heading"]:
                structure["sections"].append(current_section)

            # Extract tables
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                structure["tables"].append(table_data)

            return structure
        except Exception as e:
            logger.error("docx_structure_extraction_failed", file=str(file_path), error=str(e))
            raise


class MarkdownProcessor(DocumentProcessor):
    """Process Markdown files."""

    def get_mime_type(self) -> str:
        return "text/markdown"

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from Markdown (returns raw markdown)."""
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error("markdown_extraction_failed", file=str(file_path), error=str(e))
            raise

    async def extract_structure(self, file_path: Path) -> dict[str, Any]:
        """Extract structured content from Markdown."""
        try:
            content = file_path.read_text(encoding="utf-8")

            structure = {
                "sections": [],
                "code_blocks": [],
            }

            # Split by headers
            header_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)

            # Find all headers with positions
            headers = [
                (m.start(), len(m.group(1)), m.group(2)) for m in header_pattern.finditer(content)
            ]

            # Extract sections
            for i, (pos, level, title) in enumerate(headers):
                # Find end of section (next header of same or higher level, or end)
                end_pos = len(content)
                for next_pos, next_level, _ in headers[i + 1 :]:
                    if next_level <= level:
                        end_pos = next_pos
                        break

                section_content = content[pos:end_pos].strip()
                # Remove the header line from content
                section_body = re.sub(r"^#{1,6}\s+.+\n?", "", section_content, count=1).strip()

                structure["sections"].append(
                    {
                        "heading": title,
                        "heading_level": level,
                        "content": section_body,
                    }
                )

            # Extract code blocks
            code_pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
            for match in code_pattern.finditer(content):
                structure["code_blocks"].append(
                    {
                        "language": match.group(1) or "text",
                        "code": match.group(2).strip(),
                    }
                )

            return structure
        except Exception as e:
            logger.error("markdown_structure_extraction_failed", file=str(file_path), error=str(e))
            raise


class PlainTextProcessor(DocumentProcessor):
    """Process plain text files."""

    def get_mime_type(self) -> str:
        return "text/plain"

    async def extract_text(self, file_path: Path) -> str:
        """Extract text from plain text file."""
        return file_path.read_text(encoding="utf-8")

    async def extract_structure(self, file_path: Path) -> dict[str, Any]:
        """Extract structure from plain text (paragraph-based)."""
        content = file_path.read_text(encoding="utf-8")

        # Split by double newlines for paragraphs
        paragraphs = [p.strip() for p in re.split(r"\n\n+", content) if p.strip()]

        return {
            "paragraphs": paragraphs,
            "total_paragraphs": len(paragraphs),
        }


class MaterialPipeline:
    """
    Complete pipeline for processing materials.

    Handles: extraction -> chunking -> embedding -> storage
    """

    def __init__(
        self,
        embedder: "Embedder",
        chunker: "SemanticChunker",
    ):
        from mentor.core.material_processing.chunker import SemanticChunker
        from mentor.core.material_processing.embedder import Embedder

        self.embedder = embedder
        self.chunker = chunker
        self.processors: dict[str, DocumentProcessor] = {
            ".pdf": PDFProcessor(),
            ".docx": DocxProcessor(),
            ".md": MarkdownProcessor(),
            ".txt": PlainTextProcessor(),
        }

    def get_processor(self, file_path: Path) -> DocumentProcessor | None:
        """Get the appropriate processor for a file."""
        suffix = file_path.suffix.lower()
        return self.processors.get(suffix)

    async def process_material(
        self,
        file_path: Path,
        material_type: str,
        concept_ids: list[str],
        course_id: str,
    ) -> list["MaterialChunk"]:
        """
        Full pipeline: extract -> chunk -> embed -> return chunks.

        Args:
            file_path: Path to the material file
            material_type: Type of material (document, lecture_notes, etc.)
            concept_ids: Associated concept IDs
            course_id: Course ID for the material

        Returns:
            List of MaterialChunk objects ready for storage
        """
        from mentor.core.material_processing.chunker import Chunk

        processor = self.get_processor(file_path)
        if not processor:
            raise ValueError(f"No processor available for {file_path.suffix}")

        logger.info(
            "processing_material",
            file=str(file_path),
            material_type=material_type,
        )

        # Extract text and structure
        text = await processor.extract_text(file_path)
        structure = await processor.extract_structure(file_path)

        # Chunk the content
        chunks = self.chunker.chunk_document(text, structure)

        logger.info("chunking_complete", num_chunks=len(chunks))

        # Generate embeddings
        chunk_texts = [c.text for c in chunks]
        embeddings = await self.embedder.embed(chunk_texts)

        logger.info("embedding_complete", num_embeddings=len(embeddings))

        # Create MaterialChunk objects
        from dataclasses import dataclass

        @dataclass
        class MaterialChunk:
            course_id: str
            chunk_text: str
            chunk_index: int
            chunk_type: str | None
            metadata: dict
            embedding: list[float]
            concept_id: str | None

        material_chunks = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            material_chunks.append(
                MaterialChunk(
                    course_id=course_id,
                    chunk_text=chunk.text,
                    chunk_index=i,
                    chunk_type=chunk.chunk_type,
                    metadata=chunk.metadata,
                    embedding=embedding.tolist(),
                    concept_id=concept_ids[0] if concept_ids else None,
                )
            )

        return material_chunks
