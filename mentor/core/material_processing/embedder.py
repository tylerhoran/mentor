"""
Generate embeddings for chunks.

Supports multiple embedding models:
- Local: sentence-transformers
- API: OpenAI, Voyage, Cohere
"""

from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import structlog

from mentor.config import settings

logger = structlog.get_logger()


class Embedder(ABC):
    """Abstract base class for embedding generators."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy array of shape (len(texts), dimension)
        """
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass

    async def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text. Convenience method."""
        result = await self.embed([text])
        return result[0]


class SentenceTransformerEmbedder(Embedder):
    """
    Generate embeddings using sentence-transformers.

    This runs locally and doesn't require API calls.
    """

    def __init__(self, model_name: str | None = None):
        """
        Initialize the embedder.

        Args:
            model_name: Name of the sentence-transformers model to use.
                       Defaults to settings.embedding_model.
        """
        self.model_name = model_name or settings.embedding_model
        self._model = None
        self._dimension: int | None = None

    def _load_model(self) -> Any:
        """Lazy load the model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info("loading_embedding_model", model=self.model_name)
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
                logger.info("embedding_model_loaded", dimension=self._dimension)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings for texts."""
        model = self._load_model()

        # sentence-transformers encode is synchronous, but fast enough
        # for most use cases. For very large batches, consider using
        # a thread pool.
        embeddings = model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
        )

        return embeddings

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        if self._dimension is None:
            self._load_model()
        return self._dimension or settings.embedding_dimension


class OpenAIEmbedder(Embedder):
    """Generate embeddings using OpenAI's API."""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        api_key: str | None = None,
    ):
        """
        Initialize the OpenAI embedder.

        Args:
            model: OpenAI embedding model name
            api_key: API key (defaults to settings)
        """
        self.model = model
        self.api_key = api_key or settings.openai_api_key
        self._client = None

        # Model dimensions
        self._dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    def _get_client(self) -> Any:
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                self._client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package is required for OpenAI embeddings. "
                    "Install with: pip install openai"
                )
        return self._client

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        client = self._get_client()

        # OpenAI recommends replacing newlines with spaces
        texts = [text.replace("\n", " ") for text in texts]

        response = await client.embeddings.create(
            model=self.model,
            input=texts,
        )

        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimensions.get(self.model, 1536)


class VoyageEmbedder(Embedder):
    """Generate embeddings using Voyage AI's API."""

    def __init__(
        self,
        model: str = "voyage-2",
        api_key: str | None = None,
    ):
        """
        Initialize the Voyage embedder.

        Args:
            model: Voyage model name
            api_key: API key
        """
        self.model = model
        self.api_key = api_key

        # Model dimensions
        self._dimensions = {
            "voyage-2": 1024,
            "voyage-large-2": 1536,
            "voyage-code-2": 1536,
        }

    async def embed(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings using Voyage API."""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "input": texts,
                },
            )
            response.raise_for_status()
            data = response.json()

        embeddings = [item["embedding"] for item in data["data"]]
        return np.array(embeddings)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        return self._dimensions.get(self.model, 1024)


def get_embedder(provider: str | None = None) -> Embedder:
    """
    Factory function to get an embedder instance.

    Args:
        provider: Embedding provider ('local', 'openai', 'voyage').
                 Defaults to 'local'.

    Returns:
        Configured Embedder instance
    """
    provider = provider or "local"

    if provider == "local":
        return SentenceTransformerEmbedder()
    elif provider == "openai":
        return OpenAIEmbedder()
    elif provider == "voyage":
        return VoyageEmbedder()
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")
