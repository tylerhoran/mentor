"""High-quality TTS using Coqui XTTS with voice cloning."""

import asyncio
import io
import logging
from collections.abc import AsyncGenerator
from pathlib import Path

import numpy as np

from ..config import VoiceConfig, get_voice_config
from .base import TTSService

logger = logging.getLogger(__name__)


class XTTS(TTSService):
    """High-quality TTS using Coqui XTTS with voice cloning capability."""

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or get_voice_config()
        self.tts = None
        self._device = "cpu"
        self._load_model()

    def _load_model(self):
        """Load XTTS model."""
        try:
            import torch
            from TTS.api import TTS

            logger.info(f"Loading XTTS model: {self.config.xtts_model}")

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self.tts = TTS(self.config.xtts_model).to(self._device)

            logger.info(f"XTTS model loaded on {self._device}")

        except ImportError:
            logger.warning(
                "Coqui TTS not found. XTTS will not be available. Install with: pip install TTS"
            )
        except Exception as e:
            logger.error(f"Failed to load XTTS model: {e}")

    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech using XTTS."""
        if self.tts is None:
            raise RuntimeError("XTTS model not loaded")

        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        audio = await loop.run_in_executor(None, self._synthesize_sync, text)

        return audio

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous synthesis."""
        import scipy.io.wavfile as wavfile

        # Generate speech
        if self.config.voice_sample_path and self.config.voice_sample_path.exists():
            # Voice cloning
            wav = self.tts.tts(
                text=text, speaker_wav=str(self.config.voice_sample_path), language="en"
            )
        else:
            # Default voice - use first available speaker
            speakers = getattr(self.tts, "speakers", None)
            if speakers:
                wav = self.tts.tts(text=text, speaker=speakers[0], language="en")
            else:
                wav = self.tts.tts(text=text, language="en")

        # Convert to numpy array
        wav_array = np.array(wav, dtype=np.float32)

        # Normalize to int16 range
        wav_int16 = (wav_array * 32767).astype(np.int16)

        # Write to buffer
        buffer = io.BytesIO()
        wavfile.write(buffer, self.sample_rate, wav_int16)
        buffer.seek(0)

        return buffer.read()

    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        XTTS streaming support.

        For true streaming, we'd need the lower-level XTTS API.
        For now, yield complete audio.
        """
        audio = await self.synthesize(text)
        yield audio

    @property
    def sample_rate(self) -> int:
        return 24000  # XTTS default

    @property
    def latency_estimate_ms(self) -> int:
        return 3000  # 2-4 seconds typical

    async def warmup(self) -> None:
        """Warmup by synthesizing a short phrase."""
        if self.tts is not None:
            try:
                await self.synthesize("Hello.")
                logger.info("XTTS warmed up")
            except Exception as e:
                logger.warning(f"XTTS warmup failed: {e}")

    def set_voice_sample(self, path: Path) -> None:
        """Set the voice sample for cloning."""
        if path.exists():
            self.config.voice_sample_path = path
            logger.info(f"Voice sample set to: {path}")
        else:
            raise FileNotFoundError(f"Voice sample not found: {path}")

    @property
    def has_voice_clone(self) -> bool:
        """Check if voice cloning is configured."""
        return self.config.voice_sample_path is not None and self.config.voice_sample_path.exists()
