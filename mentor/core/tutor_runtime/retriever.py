"""
Retrieve relevant context for tutoring responses.

Features:
- Hybrid search (semantic + keyword)
- Concept-aware filtering
- Reranking
- Context window management
"""

from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mentor.core.material_processing.embedder import Embedder, get_embedder

logger = structlog.get_logger()


@dataclass
class RetrievalResult:
    """A retrieved chunk with relevance information."""

    chunk_id: str
    text: str
    score: float
    metadata: dict[str, Any]
    concept_id: str | None = None
    chunk_type: str | None = None


class Retriever:
    """
    Retriever for course materials using vector similarity search.

    Supports:
    - Semantic search using embeddings
    - Concept filtering
    - Chunk type filtering
    - Context window management
    """

    def __init__(
        self,
        course_id: str,
        embedder: Embedder | None = None,
        db_session: AsyncSession | None = None,
    ):
        """
        Initialize the retriever.

        Args:
            course_id: Course ID to retrieve from
            embedder: Embedder for query embedding
            db_session: Database session for queries
        """
        self.course_id = course_id
        self.embedder = embedder or get_embedder()
        self.db_session = db_session

    async def retrieve(
        self,
        query: str,
        concept_id: str | None = None,
        top_k: int = 5,
        chunk_types: list[str] | None = None,
        similarity_threshold: float = 0.5,
    ) -> list[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: The search query
            concept_id: Optional concept to filter by
            top_k: Number of results to return
            chunk_types: Optional list of chunk types to include
            similarity_threshold: Minimum similarity score

        Returns:
            List of RetrievalResult objects
        """
        if not self.db_session:
            logger.warning("no_db_session_for_retrieval")
            return []

        # Generate query embedding
        query_embedding = await self.embedder.embed_single(query)

        # Build the vector similarity query
        # Using pgvector's cosine distance operator <=>
        embedding_str = f"[{','.join(map(str, query_embedding.tolist()))}]"

        # Build filter conditions
        conditions = [f"course_id = '{self.course_id}'"]
        if concept_id:
            conditions.append(f"concept_id = '{concept_id}'")
        if chunk_types:
            types_str = ",".join(f"'{t}'" for t in chunk_types)
            conditions.append(f"chunk_type IN ({types_str})")

        where_clause = " AND ".join(conditions)

        # Execute vector similarity search
        query_sql = text(f"""
            SELECT
                id,
                chunk_text,
                chunk_type,
                concept_id,
                metadata,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM material_chunks
            WHERE {where_clause}
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT {top_k}
        """)

        result = await self.db_session.execute(query_sql)
        rows = result.fetchall()

        results = []
        for row in rows:
            similarity = float(row.similarity)
            if similarity >= similarity_threshold:
                results.append(
                    RetrievalResult(
                        chunk_id=row.id,
                        text=row.chunk_text,
                        score=similarity,
                        metadata=row.metadata or {},
                        concept_id=row.concept_id,
                        chunk_type=row.chunk_type,
                    )
                )

        logger.info(
            "retrieval_complete",
            query_length=len(query),
            results_count=len(results),
            concept_filter=concept_id,
        )

        return results

    async def retrieve_by_keyword(
        self,
        keyword: str,
        concept_id: str | None = None,
        top_k: int = 5,
    ) -> list[RetrievalResult]:
        """
        Retrieve chunks using keyword search (for hybrid retrieval).

        Args:
            keyword: Keyword to search for
            concept_id: Optional concept filter
            top_k: Number of results

        Returns:
            List of matching chunks
        """
        if not self.db_session:
            return []

        # Build query with text search
        conditions = [f"course_id = '{self.course_id}'"]
        if concept_id:
            conditions.append(f"concept_id = '{concept_id}'")

        where_clause = " AND ".join(conditions)

        # Use PostgreSQL text search
        query_sql = text(f"""
            SELECT
                id,
                chunk_text,
                chunk_type,
                concept_id,
                metadata,
                ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', :keyword)) as rank
            FROM material_chunks
            WHERE {where_clause}
              AND to_tsvector('english', chunk_text) @@ plainto_tsquery('english', :keyword)
            ORDER BY rank DESC
            LIMIT {top_k}
        """)

        result = await self.db_session.execute(query_sql, {"keyword": keyword})
        rows = result.fetchall()

        return [
            RetrievalResult(
                chunk_id=row.id,
                text=row.chunk_text,
                score=float(row.rank),
                metadata=row.metadata or {},
                concept_id=row.concept_id,
                chunk_type=row.chunk_type,
            )
            for row in rows
        ]

    async def hybrid_retrieve(
        self,
        query: str,
        concept_id: str | None = None,
        top_k: int = 5,
        semantic_weight: float = 0.7,
    ) -> list[RetrievalResult]:
        """
        Hybrid retrieval combining semantic and keyword search.

        Args:
            query: Search query
            concept_id: Optional concept filter
            top_k: Number of results
            semantic_weight: Weight for semantic results (0-1)

        Returns:
            Combined and reranked results
        """
        # Get semantic results
        semantic_results = await self.retrieve(query, concept_id, top_k=top_k * 2)

        # Extract keywords from query (simple approach)
        keywords = [w for w in query.split() if len(w) > 3]
        keyword_query = " ".join(keywords[:5])

        # Get keyword results
        keyword_results = await self.retrieve_by_keyword(keyword_query, concept_id, top_k=top_k * 2)

        # Combine results
        combined: dict[str, RetrievalResult] = {}

        # Add semantic results
        for result in semantic_results:
            combined[result.chunk_id] = RetrievalResult(
                chunk_id=result.chunk_id,
                text=result.text,
                score=result.score * semantic_weight,
                metadata=result.metadata,
                concept_id=result.concept_id,
                chunk_type=result.chunk_type,
            )

        # Add keyword results
        keyword_weight = 1 - semantic_weight
        for result in keyword_results:
            if result.chunk_id in combined:
                # Boost score if in both
                combined[result.chunk_id].score += result.score * keyword_weight
            else:
                combined[result.chunk_id] = RetrievalResult(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    score=result.score * keyword_weight,
                    metadata=result.metadata,
                    concept_id=result.concept_id,
                    chunk_type=result.chunk_type,
                )

        # Sort by combined score and return top_k
        sorted_results = sorted(
            combined.values(),
            key=lambda r: r.score,
            reverse=True,
        )

        return sorted_results[:top_k]

    async def get_context_for_response(
        self,
        student_message: str,
        current_concept: str | None,
        conversation_history: list[dict[str, str]],
        max_tokens: int = 2000,
    ) -> str:
        """
        Build context string for LLM, respecting token budget.

        Args:
            student_message: Current student message
            current_concept: Current concept being discussed
            conversation_history: Recent conversation
            max_tokens: Maximum tokens for context

        Returns:
            Formatted context string
        """
        # Estimate available tokens (rough: 4 chars per token)
        available_chars = max_tokens * 4

        # Retrieve relevant chunks
        results = await self.hybrid_retrieve(
            student_message,
            concept_id=current_concept,
            top_k=10,
        )

        # Build context string
        context_parts = []
        current_chars = 0

        # Add most relevant chunks
        for result in results:
            chunk_text = f"[{result.chunk_type or 'content'}]\n{result.text}\n"
            chunk_chars = len(chunk_text)

            if current_chars + chunk_chars > available_chars:
                break

            context_parts.append(chunk_text)
            current_chars += chunk_chars

        if not context_parts:
            return ""

        context = "## Relevant Course Material\n\n" + "\n---\n".join(context_parts)

        logger.info(
            "context_built",
            num_chunks=len(context_parts),
            total_chars=current_chars,
        )

        return context

    async def get_examples_for_concept(
        self,
        concept_id: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        """Get example chunks for a concept."""
        return await self.retrieve(
            query="example",
            concept_id=concept_id,
            top_k=top_k,
            chunk_types=["example", "worked_example"],
        )

    async def get_problems_for_concept(
        self,
        concept_id: str,
        top_k: int = 3,
    ) -> list[RetrievalResult]:
        """Get problem chunks for a concept."""
        return await self.retrieve(
            query="problem exercise",
            concept_id=concept_id,
            top_k=top_k,
            chunk_types=["problem"],
        )
