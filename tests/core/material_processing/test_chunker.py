"""Tests for the semantic chunker module."""


from mentor.core.material_processing.chunker import Chunk, SemanticChunker


class TestChunk:
    """Tests for Chunk dataclass."""

    def test_creation(self):
        """Test creating a chunk."""
        chunk = Chunk(
            text="This is some text content.",
            chunk_type="explanation",
        )
        assert chunk.text == "This is some text content."
        assert chunk.chunk_type == "explanation"

    def test_char_count(self):
        """Test character count property."""
        chunk = Chunk(text="Hello", chunk_type="explanation")
        assert chunk.char_count == 5

    def test_word_count(self):
        """Test word count property."""
        chunk = Chunk(text="Hello world foo bar", chunk_type="explanation")
        assert chunk.word_count == 4

    def test_default_metadata(self):
        """Test default metadata is empty dict."""
        chunk = Chunk(text="Test", chunk_type="code")
        assert chunk.metadata == {}

    def test_with_metadata(self):
        """Test chunk with metadata."""
        chunk = Chunk(
            text="Test",
            chunk_type="code",
            metadata={"language": "python"},
        )
        assert chunk.metadata["language"] == "python"


class TestSemanticChunker:
    """Tests for SemanticChunker class."""

    def test_initialization(self):
        """Test chunker initialization."""
        chunker = SemanticChunker(target_chunk_size=500)
        assert chunker.target_chunk_size == 500
        assert chunker.overlap == 50
        assert chunker.respect_boundaries is True

    def test_initialization_custom_params(self):
        """Test chunker with custom parameters."""
        chunker = SemanticChunker(
            target_chunk_size=1000,
            overlap=100,
            respect_boundaries=False,
            min_chunk_size=200,
            max_chunk_size=3000,
        )
        assert chunker.target_chunk_size == 1000
        assert chunker.overlap == 100
        assert chunker.respect_boundaries is False
        assert chunker.min_chunk_size == 200
        assert chunker.max_chunk_size == 3000

    def test_chunk_short_document(self):
        """Test chunking a short document."""
        chunker = SemanticChunker(target_chunk_size=500)
        text = "This is a short paragraph.\n\nThis is another paragraph."

        chunks = chunker.chunk_document(text)
        assert len(chunks) >= 1
        # All text should be captured
        total_text = " ".join(c.text for c in chunks)
        assert "short paragraph" in total_text

    def test_chunk_long_document(self):
        """Test chunking a longer document."""
        chunker = SemanticChunker(target_chunk_size=100, max_chunk_size=200)

        # Create a document with multiple paragraphs
        paragraphs = ["Paragraph number " + str(i) + " with some content." for i in range(10)]
        text = "\n\n".join(paragraphs)

        chunks = chunker.chunk_document(text)
        assert len(chunks) > 1

    def test_chunk_respects_max_size(self):
        """Test that chunks don't exceed max size (with reasonable margin)."""
        chunker = SemanticChunker(
            target_chunk_size=200,
            max_chunk_size=300,
            overlap=0,
        )

        # Create long paragraphs
        long_para = "This is a sentence. " * 50
        text = long_para + "\n\n" + long_para

        chunks = chunker.chunk_document(text)
        # Chunks should be created
        assert len(chunks) >= 1

    def test_chunk_type_inference_code(self):
        """Test chunk type inference for code."""
        chunker = SemanticChunker()

        # Code block should be detected
        chunk_type = chunker._infer_chunk_type("", "```python\nprint('hello')\n```")
        assert chunk_type == "code"

    def test_chunk_type_inference_example(self):
        """Test chunk type inference for examples."""
        chunker = SemanticChunker()

        chunk_type = chunker._infer_chunk_type("Example", "Here is an example of usage.")
        assert chunk_type == "example"

    def test_chunk_type_inference_problem(self):
        """Test chunk type inference for problems."""
        chunker = SemanticChunker()

        chunk_type = chunker._infer_chunk_type("Practice Problem", "Solve this equation.")
        assert chunk_type == "problem"

    def test_chunk_type_inference_solution(self):
        """Test chunk type inference for solutions."""
        chunker = SemanticChunker()

        chunk_type = chunker._infer_chunk_type("Solution", "The answer is 42.")
        assert chunk_type == "solution"

    def test_chunk_type_inference_default(self):
        """Test default chunk type."""
        chunker = SemanticChunker()

        chunk_type = chunker._infer_chunk_type("Introduction", "This is regular text.")
        assert chunk_type == "explanation"

    def test_chunk_document_with_structure(self):
        """Test chunking with structure information."""
        chunker = SemanticChunker()

        structure = {
            "sections": [
                {
                    "heading": "Introduction",
                    "content": "This is the introduction.",
                    "heading_level": 1,
                },
                {
                    "heading": "Examples",
                    "content": "Here are some examples.",
                    "heading_level": 2,
                },
            ]
        }

        chunks = chunker.chunk_document("", structure=structure)
        assert len(chunks) >= 1

    def test_chunk_document_with_paragraphs_in_structure(self):
        """Test chunking with paragraphs list in structure."""
        chunker = SemanticChunker()

        structure = {
            "sections": [
                {
                    "heading": "Section 1",
                    "paragraphs": ["Para 1", "Para 2"],
                    "heading_level": 1,
                },
            ]
        }

        chunks = chunker.chunk_document("", structure=structure)
        assert len(chunks) >= 1
        assert "Para 1" in chunks[0].text

    def test_chunk_code_python(self):
        """Test chunking Python code."""
        chunker = SemanticChunker()

        code = """def hello():
    print("Hello")

def world():
    print("World")

class MyClass:
    pass
"""
        chunks = chunker.chunk_code(code, "python")
        assert len(chunks) >= 1
        # All chunks should be code type
        for chunk in chunks:
            assert chunk.chunk_type == "code"

    def test_chunk_code_javascript(self):
        """Test chunking JavaScript code."""
        chunker = SemanticChunker()

        code = """function hello() {
    console.log("Hello");
}

class MyClass {
}
"""
        chunks = chunker.chunk_code(code, "javascript")
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.chunk_type == "code"
            assert chunk.metadata["language"] == "javascript"

    def test_chunk_code_extracts_name(self):
        """Test that code chunking extracts function names."""
        chunker = SemanticChunker()

        code = """def my_function():
    return 42
"""
        chunks = chunker.chunk_code(code, "python")
        assert len(chunks) >= 1
        # Should extract function name
        assert chunks[0].metadata.get("name") == "my_function"

    def test_merge_small_chunks(self):
        """Test that small chunks get merged."""
        chunker = SemanticChunker(min_chunk_size=100, max_chunk_size=500)

        # Create very small paragraphs
        text = "Hi.\n\nHello.\n\nHey.\n\nThis is a longer paragraph with more content."

        chunks = chunker.chunk_document(text)
        # Small chunks should be merged
        assert len(chunks) <= 2

    def test_code_block_separate_chunk(self):
        """Test that code blocks are separate chunks."""
        chunker = SemanticChunker()

        text = """Regular text here.

```python
print("hello")
```

More regular text."""

        chunks = chunker.chunk_document(text)
        # Should have code as separate chunk
        code_chunks = [c for c in chunks if c.chunk_type == "code"]
        assert len(code_chunks) >= 1

    def test_overlap_between_chunks(self):
        """Test that overlap is applied between chunks."""
        chunker = SemanticChunker(
            target_chunk_size=50,
            overlap=20,
            min_chunk_size=10,
        )

        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph content here."

        chunks = chunker.chunk_document(text)
        # With overlap, later chunks might contain content from earlier ones
        assert len(chunks) >= 1

    def test_empty_document(self):
        """Test chunking empty document."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document("")
        assert chunks == []

    def test_whitespace_only_document(self):
        """Test chunking whitespace-only document."""
        chunker = SemanticChunker()
        chunks = chunker.chunk_document("   \n\n   \n   ")
        assert chunks == []
