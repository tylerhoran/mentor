"""
Intelligent chunking for retrieval.

Features:
- Semantic chunking (respects paragraph/section boundaries)
- Overlap for context preservation
- Special handling for code blocks, equations, tables
- Metadata extraction (headers, context)
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """A chunk of text from a document."""

    text: str
    chunk_type: str  # 'explanation', 'example', 'problem', 'solution', 'code'
    metadata: dict[str, Any] = field(default_factory=dict)
    start_char: int = 0
    end_char: int = 0

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def word_count(self) -> int:
        return len(self.text.split())


class SemanticChunker:
    """
    Semantic chunker that respects document structure.

    Splits documents into chunks while:
    - Respecting paragraph and section boundaries
    - Maintaining overlap for context
    - Handling special content (code, math) appropriately
    - Extracting metadata for each chunk
    """

    def __init__(
        self,
        target_chunk_size: int = 512,
        overlap: int = 50,
        respect_boundaries: bool = True,
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000,
    ):
        """
        Initialize the chunker.

        Args:
            target_chunk_size: Target size in characters for each chunk
            overlap: Number of characters to overlap between chunks
            respect_boundaries: Whether to respect paragraph/section boundaries
            min_chunk_size: Minimum chunk size (merge smaller chunks)
            max_chunk_size: Maximum chunk size (split larger chunks)
        """
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap
        self.respect_boundaries = respect_boundaries
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk_document(
        self,
        text: str,
        structure: dict[str, Any] | None = None,
    ) -> list[Chunk]:
        """
        Chunk a document into semantic units.

        Args:
            text: The full document text
            structure: Optional structural information from document processor

        Returns:
            List of Chunk objects
        """
        if structure and "sections" in structure:
            return self._chunk_by_sections(structure)
        else:
            return self._chunk_by_paragraphs(text)

    def _chunk_by_sections(self, structure: dict[str, Any]) -> list[Chunk]:
        """Chunk document using section structure."""
        chunks = []

        for section in structure.get("sections", []):
            heading = section.get("heading", "")
            content = section.get("content", "")
            paragraphs = section.get("paragraphs", [])

            # If we have paragraphs list, join them
            if paragraphs and not content:
                content = "\n\n".join(paragraphs)

            if not content.strip():
                continue


            # Determine chunk type from heading
            chunk_type = self._infer_chunk_type(heading, content)

            # If content is small enough, keep as one chunk
            if len(content) <= self.max_chunk_size:
                chunks.append(
                    Chunk(
                        text=content,
                        chunk_type=chunk_type,
                        metadata={
                            "section_heading": heading,
                            "heading_level": section.get("heading_level", 1),
                        },
                    )
                )
            else:
                # Split large sections
                sub_chunks = self._split_large_content(content, heading)
                for sub_chunk in sub_chunks:
                    sub_chunk.metadata["section_heading"] = heading
                    chunks.append(sub_chunk)

        # Handle code blocks separately if present
        for code_block in structure.get("code_blocks", []):
            chunks.append(
                Chunk(
                    text=code_block["code"],
                    chunk_type="code",
                    metadata={"language": code_block.get("language", "")},
                )
            )

        return self._merge_small_chunks(chunks)

    def _chunk_by_paragraphs(self, text: str) -> list[Chunk]:
        """Chunk document by paragraphs when no structure is available."""
        # Split by double newlines
        paragraphs = re.split(r"\n\n+", text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk_text = ""
        current_position = 0

        for para in paragraphs:
            # Check if this is a code block
            if para.startswith("```") or para.startswith("    "):
                # Flush current chunk
                if current_chunk_text:
                    chunks.append(self._create_chunk(current_chunk_text, current_position))
                    current_position += len(current_chunk_text)
                    current_chunk_text = ""

                # Add code as separate chunk
                chunks.append(
                    Chunk(
                        text=para,
                        chunk_type="code",
                        metadata={},
                        start_char=current_position,
                        end_char=current_position + len(para),
                    )
                )
                current_position += len(para)
                continue

            # Check if adding this paragraph exceeds target size
            potential_text = current_chunk_text + ("\n\n" if current_chunk_text else "") + para

            if len(potential_text) > self.target_chunk_size and current_chunk_text:
                # Create chunk with current content
                chunks.append(self._create_chunk(current_chunk_text, current_position))
                current_position += len(current_chunk_text)

                # Start new chunk with overlap
                if self.overlap > 0 and current_chunk_text:
                    # Get last portion for overlap
                    overlap_text = current_chunk_text[-self.overlap :]
                    current_chunk_text = overlap_text + "\n\n" + para
                else:
                    current_chunk_text = para
            else:
                current_chunk_text = potential_text

        # Don't forget the last chunk
        if current_chunk_text:
            chunks.append(self._create_chunk(current_chunk_text, current_position))

        return self._merge_small_chunks(chunks)

    def _create_chunk(self, text: str, start_pos: int) -> Chunk:
        """Create a chunk with inferred type."""
        chunk_type = self._infer_chunk_type("", text)
        return Chunk(
            text=text,
            chunk_type=chunk_type,
            metadata={},
            start_char=start_pos,
            end_char=start_pos + len(text),
        )

    def _infer_chunk_type(self, heading: str, content: str) -> str:
        """Infer the type of content in a chunk."""
        heading_lower = heading.lower()
        content_lower = content.lower()

        # Check heading for clues
        if any(word in heading_lower for word in ["example", "sample", "demo"]):
            return "example"
        if any(word in heading_lower for word in ["problem", "exercise", "practice", "question"]):
            return "problem"
        if any(word in heading_lower for word in ["solution", "answer"]):
            return "solution"
        if any(word in heading_lower for word in ["code", "implementation"]):
            return "code"

        # Check content for clues
        if "```" in content or content.startswith("    "):
            return "code"
        if re.search(r"^\d+\.", content) or "?" in content[:100]:
            return "problem"
        if any(phrase in content_lower for phrase in ["for example", "consider", "let's look at"]):
            return "example"

        return "explanation"

    def _split_large_content(self, content: str, heading: str) -> list[Chunk]:
        """Split content that exceeds max chunk size."""
        chunks = []
        paragraphs = content.split("\n\n")
        current_text = ""

        for para in paragraphs:
            if len(current_text) + len(para) > self.target_chunk_size:
                if current_text:
                    chunks.append(
                        Chunk(
                            text=current_text.strip(),
                            chunk_type=self._infer_chunk_type(heading, current_text),
                            metadata={},
                        )
                    )
                current_text = para
            else:
                current_text += ("\n\n" if current_text else "") + para

        if current_text:
            chunks.append(
                Chunk(
                    text=current_text.strip(),
                    chunk_type=self._infer_chunk_type(heading, current_text),
                    metadata={},
                )
            )

        return chunks

    def _merge_small_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Merge chunks that are too small."""
        if not chunks:
            return chunks

        merged = []
        current = chunks[0]

        for next_chunk in chunks[1:]:
            # Don't merge different types (especially code)
            if current.chunk_type != next_chunk.chunk_type:
                merged.append(current)
                current = next_chunk
                continue

            # Merge if combined is under max and current is under min
            combined_len = len(current.text) + len(next_chunk.text) + 2
            if len(current.text) < self.min_chunk_size and combined_len <= self.max_chunk_size:
                current = Chunk(
                    text=current.text + "\n\n" + next_chunk.text,
                    chunk_type=current.chunk_type,
                    metadata={**current.metadata, **next_chunk.metadata},
                    start_char=current.start_char,
                    end_char=next_chunk.end_char,
                )
            else:
                merged.append(current)
                current = next_chunk

        merged.append(current)
        return merged

    def chunk_code(self, code: str, language: str) -> list[Chunk]:
        """
        Special handling for code - chunk by function/class.

        Args:
            code: The code content
            language: Programming language

        Returns:
            List of code chunks
        """
        chunks = []

        # Language-specific patterns for splitting
        if language in ("python", "py"):
            # Split on function and class definitions
            pattern = r"(?=^(?:def |class |async def ))"
        elif language in ("javascript", "js", "typescript", "ts"):
            # Split on function and class definitions
            pattern = r"(?=^(?:function |class |const \w+ = (?:async )?\(|export ))"
        else:
            # Default: split by blank lines
            pattern = r"\n\n+"

        parts = re.split(pattern, code, flags=re.MULTILINE)
        parts = [p.strip() for p in parts if p.strip()]

        for part in parts:
            # Extract function/class name if possible
            name_match = re.match(r"(?:def |class |function |const )(\w+)", part)
            name = name_match.group(1) if name_match else None

            chunks.append(
                Chunk(
                    text=part,
                    chunk_type="code",
                    metadata={
                        "language": language,
                        "name": name,
                    },
                )
            )

        return chunks
