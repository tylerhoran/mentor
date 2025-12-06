"""Fast TTS using Piper."""

import asyncio
import importlib.util
import logging
import shutil
import tempfile
from collections.abc import AsyncGenerator
from pathlib import Path

from ..config import VoiceConfig, get_voice_config
from .base import TTSService

logger = logging.getLogger(__name__)


class PiperTTS(TTSService):
    """Fast TTS using Piper for low-latency responses."""

    def __init__(self, config: VoiceConfig | None = None):
        self.config = config or get_voice_config()
        self._piper_available = self._check_installation()

    def _check_installation(self) -> bool:
        """Check if Piper is installed and available."""
        piper_path = shutil.which("piper")
        if piper_path:
            logger.info(f"Piper TTS found at: {piper_path}")
            return True

        # Try piper-tts Python package
        if importlib.util.find_spec("piper"):
            logger.info("Piper TTS available via Python package")
            return True

        logger.warning(
            "Piper not found. Install with: pip install piper-tts "
            "or download from https://github.com/rhasspy/piper"
        )
        return False

    async def synthesize(self, text: str) -> bytes:
        """Synthesize speech using Piper."""
        if not self._piper_available:
            raise RuntimeError("Piper TTS is not available")

        # Try Python API first
        try:
            return await self._synthesize_python(text)
        except (ImportError, Exception) as e:
            logger.debug(f"Python Piper failed: {e}, trying CLI")

        # Fall back to CLI
        return await self._synthesize_cli(text)

    async def _synthesize_python(self, text: str) -> bytes:
        """Synthesize using Piper Python API."""
        import io
        import wave

        import piper

        loop = asyncio.get_event_loop()

        def _synth():
            voice = piper.PiperVoice.load(self.config.piper_model_path or self.config.piper_model)

            # Generate audio
            audio_data = b""
            for audio_bytes in voice.synthesize_stream_raw(text):
                audio_data += audio_bytes

            # Wrap in WAV
            buffer = io.BytesIO()
            with wave.open(buffer, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(self.sample_rate)
                wav.writeframes(audio_data)

            buffer.seek(0)
            return buffer.read()

        return await loop.run_in_executor(None, _synth)

    async def _synthesize_cli(self, text: str) -> bytes:
        """Synthesize using Piper CLI."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            output_path = f.name

        try:
            model_path = self.config.piper_model_path or self.config.piper_model

            process = await asyncio.create_subprocess_exec(
                "piper",
                "--model",
                str(model_path),
                "--output_file",
                output_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate(input=text.encode())

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Piper error: {error_msg}")
                raise RuntimeError(f"Piper synthesis failed: {error_msg}")

            # Read output file
            with open(output_path, "rb") as f:
                audio_bytes = f.read()

            return audio_bytes

        finally:
            # Cleanup
            Path(output_path).unlink(missing_ok=True)

    async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Piper doesn't support true streaming via CLI.
        Synthesize complete audio and yield it.
        """
        audio = await self.synthesize(text)
        yield audio

    @property
    def sample_rate(self) -> int:
        return 22050  # Piper default

    @property
    def latency_estimate_ms(self) -> int:
        return 300  # Very fast

    async def warmup(self) -> None:
        """Warmup by synthesizing a short phrase."""
        if self._piper_available:
            try:
                await self.synthesize("Hello.")
                logger.info("Piper TTS warmed up")
            except Exception as e:
                logger.warning(f"Piper warmup failed: {e}")
