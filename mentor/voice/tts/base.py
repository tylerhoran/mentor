"""Abstract base class for TTS services."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator


class TTSService(ABC):
    """Abstract base class for TTS services."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize

        Returns:
            Audio bytes (WAV format)
        """
        pass

    @abstractmethod
    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Stream synthesized speech.

        Yields audio chunks as they're generated.
        """
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Output sample rate."""
        pass

    @property
    @abstractmethod
    def latency_estimate_ms(self) -> int:
        """Estimated latency before first audio."""
        pass

    async def warmup(self) -> None:
        """Optional warmup to preload models."""
        pass
