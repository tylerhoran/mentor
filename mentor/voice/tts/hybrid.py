"""Hybrid TTS strategy combining Piper (fast) and XTTS (quality)."""

import logging
import re
from typing import AsyncGenerator, Optional

from ..config import TTSEngine, VoiceConfig, get_voice_config
from .base import TTSService
from .piper_service import PiperTTS
from .xtts_service import XTTS

logger = logging.getLogger(__name__)


class HybridTTS(TTSService):
    """
    Hybrid TTS strategy:
    - Piper for short responses (acknowledgments, prompts)
    - XTTS for longer, substantive responses
    """

    # Patterns that indicate quick acknowledgment responses
    ACKNOWLEDGMENT_PATTERNS = [
        r"^i see\.?$",
        r"^okay\.?$",
        r"^right\.?$",
        r"^go on\.?$",
        r"^continue\.?$",
        r"^interesting\.?$",
        r"^tell me more\.?$",
        r"^good\.?$",
        r"^hmm\.?$",
        r"^let'?s think about",
        r"^what do you think",
        r"^that'?s (right|correct|good)",
        r"^yes,?\s",
        r"^no,?\s",
        r"^well,?\s",
    ]

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or get_voice_config()
        self.fast_tts: Optional[TTSService] = None
        self.quality_tts: Optional[TTSService] = None
        self._init_engines()

        # Compile patterns
        self._ack_patterns = [re.compile(p, re.IGNORECASE) for p in self.ACKNOWLEDGMENT_PATTERNS]

    def _init_engines(self):
        """Initialize TTS engines."""
        try:
            self.fast_tts = PiperTTS(self.config)
        except Exception as e:
            logger.warning(f"Failed to initialize Piper: {e}")

        try:
            self.quality_tts = XTTS(self.config)
        except Exception as e:
            logger.warning(f"Failed to initialize XTTS: {e}")

        if self.fast_tts is None and self.quality_tts is None:
            raise RuntimeError("No TTS engine available")

    def _should_use_fast(self, text: str) -> bool:
        """Determine if we should use fast TTS."""
        # Short responses
        if len(text) <= self.config.short_response_chars:
            return True

        # Acknowledgment patterns
        text_clean = text.strip().lower()
        for pattern in self._ack_patterns:
            if pattern.match(text_clean):
                return True

        return False

    def _get_available_engine(self, prefer_fast: bool) -> TTSService:
        """Get an available TTS engine."""
        if prefer_fast:
            if self.fast_tts is not None:
                return self.fast_tts
            if self.quality_tts is not None:
                return self.quality_tts
        else:
            if self.quality_tts is not None:
                return self.quality_tts
            if self.fast_tts is not None:
                return self.fast_tts

        raise RuntimeError("No TTS engine available")

    async def synthesize(self, text: str) -> bytes:
        """Synthesize using appropriate engine."""
        use_fast = self._should_use_fast(text)
        engine = self._get_available_engine(use_fast)

        engine_name = "Piper" if engine == self.fast_tts else "XTTS"
        logger.debug(f"Using {engine_name} for synthesis ({len(text)} chars)")

        return await engine.synthesize(text)

    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream from appropriate engine."""
        use_fast = self._should_use_fast(text)
        engine = self._get_available_engine(use_fast)

        async for chunk in engine.synthesize_streaming(text):
            yield chunk

    @property
    def sample_rate(self) -> int:
        """Return sample rate of primary engine."""
        if self.quality_tts is not None:
            return self.quality_tts.sample_rate
        if self.fast_tts is not None:
            return self.fast_tts.sample_rate
        return 22050  # Default

    @property
    def latency_estimate_ms(self) -> int:
        """Return average latency estimate."""
        latencies = []
        if self.fast_tts is not None:
            latencies.append(self.fast_tts.latency_estimate_ms)
        if self.quality_tts is not None:
            latencies.append(self.quality_tts.latency_estimate_ms)

        return sum(latencies) // len(latencies) if latencies else 1000

    async def warmup(self) -> None:
        """Warmup both engines."""
        if self.fast_tts is not None:
            await self.fast_tts.warmup()
        if self.quality_tts is not None:
            await self.quality_tts.warmup()

    def get_engine_for_text(self, text: str) -> str:
        """Get which engine would be used for given text."""
        return "piper" if self._should_use_fast(text) else "xtts"


def get_tts_service(config: Optional[VoiceConfig] = None) -> TTSService:
    """Factory function for TTS service based on configuration."""
    config = config or get_voice_config()

    if config.tts_engine == TTSEngine.PIPER:
        return PiperTTS(config)
    elif config.tts_engine == TTSEngine.XTTS:
        return XTTS(config)
    else:  # hybrid
        return HybridTTS(config)
