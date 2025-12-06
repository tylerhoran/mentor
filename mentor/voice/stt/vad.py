"""Voice Activity Detection using Silero VAD."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

from ..config import VoiceConfig, get_voice_config

logger = logging.getLogger(__name__)


class SpeechState(str, Enum):
    SILENCE = "silence"
    SPEAKING = "speaking"
    FINISHED = "finished"


@dataclass
class VADResult:
    """Result from VAD processing."""

    state: SpeechState
    audio: Optional[np.ndarray] = None
    speech_probability: float = 0.0
    duration_ms: int = 0


class SileroVAD:
    """Voice Activity Detection using Silero VAD."""

    def __init__(self, config: Optional[VoiceConfig] = None):
        self.config = config or get_voice_config()
        self.model = None
        self.utils = None
        self._load_model()
        self._reset_state()

    def _load_model(self):
        """Load Silero VAD model."""
        try:
            import torch

            logger.info("Loading Silero VAD model")
            self.model, self.utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            logger.info("Silero VAD model loaded")
        except ImportError:
            logger.warning(
                "torch not installed. VAD will not be available. Install with: pip install torch"
            )
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")
            raise

    def _reset_state(self):
        """Reset VAD state for new utterance."""
        self.speech_buffer = np.array([], dtype=np.float32)
        self.silence_samples = 0
        self.speech_samples = 0
        self.is_speaking = False

    def process_chunk(self, audio_chunk: np.ndarray) -> VADResult:
        """
        Process an audio chunk and detect speech.

        Args:
            audio_chunk: Audio samples (float32, mono, 16kHz)

        Returns:
            VADResult with current state and accumulated audio if speech ended
        """
        if self.model is None:
            # Fallback: treat all audio as speech
            self.speech_buffer = np.concatenate([self.speech_buffer, audio_chunk])
            return VADResult(
                state=SpeechState.SPEAKING,
                speech_probability=1.0,
                duration_ms=len(self.speech_buffer) * 1000 // self.config.sample_rate,
            )

        import torch

        # Convert to tensor
        audio_tensor = torch.from_numpy(audio_chunk).float()

        # Get speech probability
        speech_prob = self.model(audio_tensor, self.config.sample_rate).item()

        chunk_duration_ms = len(audio_chunk) * 1000 // self.config.sample_rate

        if speech_prob >= self.config.vad_threshold:
            # Speech detected
            self.speech_buffer = np.concatenate([self.speech_buffer, audio_chunk])
            self.speech_samples += len(audio_chunk)
            self.silence_samples = 0
            self.is_speaking = True

            # Check max duration
            speech_duration_s = self.speech_samples / self.config.sample_rate
            if speech_duration_s >= self.config.max_speech_duration_s:
                # Force end of utterance
                audio = self.speech_buffer.copy()
                duration = int(speech_duration_s * 1000)
                self._reset_state()
                return VADResult(
                    state=SpeechState.FINISHED,
                    audio=audio,
                    speech_probability=speech_prob,
                    duration_ms=duration,
                )

            return VADResult(
                state=SpeechState.SPEAKING,
                speech_probability=speech_prob,
                duration_ms=int(speech_duration_s * 1000),
            )

        else:
            # Silence detected
            if self.is_speaking:
                # Add silence to buffer (we want a bit of trailing silence)
                self.speech_buffer = np.concatenate([self.speech_buffer, audio_chunk])
                self.silence_samples += len(audio_chunk)

                silence_duration_ms = self.silence_samples * 1000 // self.config.sample_rate

                if silence_duration_ms >= self.config.min_silence_duration_ms:
                    # End of utterance
                    speech_duration_ms = self.speech_samples * 1000 // self.config.sample_rate

                    if speech_duration_ms >= self.config.min_speech_duration_ms:
                        # Valid utterance
                        audio = self.speech_buffer.copy()
                        self._reset_state()
                        return VADResult(
                            state=SpeechState.FINISHED,
                            audio=audio,
                            speech_probability=speech_prob,
                            duration_ms=speech_duration_ms,
                        )
                    else:
                        # Too short, discard
                        self._reset_state()
                        return VADResult(state=SpeechState.SILENCE, speech_probability=speech_prob)

                return VADResult(
                    state=SpeechState.SPEAKING,
                    speech_probability=speech_prob,
                    duration_ms=self.speech_samples * 1000 // self.config.sample_rate,
                )

            return VADResult(state=SpeechState.SILENCE, speech_probability=speech_prob)

    def reset(self):
        """Reset for new conversation turn."""
        self._reset_state()
        if self.model is not None:
            self.model.reset_states()

    def get_current_audio(self) -> Optional[np.ndarray]:
        """Get the current audio buffer without resetting."""
        if len(self.speech_buffer) > 0:
            return self.speech_buffer.copy()
        return None


# Singleton
_vad_instance: Optional[SileroVAD] = None


def get_vad() -> SileroVAD:
    """Get or create the VAD singleton."""
    global _vad_instance
    if _vad_instance is None:
        _vad_instance = SileroVAD()
    return _vad_instance
