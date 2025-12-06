"""Speech-to-text using faster-whisper."""

import logging
from typing import Generator, Optional

import numpy as np

from ..config import VoiceConfig, get_voice_config

logger = logging.getLogger(__name__)


class WhisperSTT:
    """Speech-to-text using faster-whisper."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or get_voice_config()
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the Whisper model."""
        try:
            from faster_whisper import WhisperModel

            logger.info(f"Loading Whisper model: {self.config.stt_model}")
            self.model = WhisperModel(
                self.config.stt_model,
                device=self.config.stt_device,
                compute_type=self.config.stt_compute_type,
            )
            logger.info("Whisper model loaded successfully")
        except ImportError:
            logger.warning(
                "faster-whisper not installed. STT will not be available. "
                "Install with: pip install faster-whisper"
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> str:
        """
        Transcribe audio to text.

        Args:
            audio: Audio samples as numpy array (float32, mono, 16kHz)
            language: Optional language code (default from config)

        Returns:
            Transcribed text
        """
        if self.model is None:
            raise RuntimeError("Whisper model not loaded")

        language = language or self.config.stt_language

        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=5,
            best_of=5,
            temperature=0.0,
            condition_on_previous_text=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=400),
        )

        # Combine all segments
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()

    def transcribe_with_timestamps(
        self, audio: np.ndarray, language: Optional[str] = None
    ) -> list[dict]:
        """
        Transcribe audio with word-level timestamps.

        Returns list of dicts with 'word', 'start', 'end', 'probability'
        """
        if self.model is None:
            raise RuntimeError("Whisper model not loaded")

        language = language or self.config.stt_language

        segments, info = self.model.transcribe(
            audio, language=language, beam_size=5, word_timestamps=True
        )

        words = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    words.append(
                        {
                            "word": word.word,
                            "start": word.start,
                            "end": word.end,
                            "probability": word.probability,
                        }
                    )

        return words

    def transcribe_streaming(
        self, audio_chunks: Generator[np.ndarray, None, None]
    ) -> Generator[str, None, None]:
        """
        Stream transcription for real-time display.
        Yields partial transcriptions as audio comes in.
        """
        buffer = np.array([], dtype=np.float32)

        for chunk in audio_chunks:
            buffer = np.concatenate([buffer, chunk])

            # Transcribe every ~2 seconds of audio
            if len(buffer) >= self.config.sample_rate * 2:
                text = self.transcribe(buffer)
                if text:
                    yield text
                # Keep last 0.5s for context
                buffer = buffer[-self.config.sample_rate // 2 :]

        # Final transcription
        if len(buffer) > 0:
            text = self.transcribe(buffer)
            if text:
                yield text

    def get_speech_features(self, audio: np.ndarray, words: list[dict]) -> dict:
        """
        Extract speech features for gaming detection.

        Returns:
            Dict with speech_rate_wpm, pause_count, avg_pause_duration_ms, etc.
        """
        if not words:
            return {
                "speech_rate_wpm": None,
                "pause_count": 0,
                "average_pause_duration_ms": 0.0,
            }

        # Calculate speech rate
        total_duration = words[-1]["end"] - words[0]["start"]
        word_count = len(words)

        if total_duration > 0:
            speech_rate_wpm = (word_count / total_duration) * 60
        else:
            speech_rate_wpm = 0

        # Count pauses (gaps > 300ms between words)
        pause_threshold_s = 0.3
        pauses = []

        for i in range(1, len(words)):
            gap = words[i]["start"] - words[i - 1]["end"]
            if gap > pause_threshold_s:
                pauses.append(gap * 1000)  # Convert to ms

        return {
            "speech_rate_wpm": speech_rate_wpm,
            "pause_count": len(pauses),
            "average_pause_duration_ms": sum(pauses) / len(pauses) if pauses else 0.0,
        }


# Singleton instance
_whisper_instance: Optional[WhisperSTT] = None


def get_whisper_stt() -> WhisperSTT:
    """Get or create the Whisper STT singleton."""
    global _whisper_instance
    if _whisper_instance is None:
        _whisper_instance = WhisperSTT()
    return _whisper_instance
