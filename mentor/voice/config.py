"""Voice layer configuration."""

import os
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class STTModel(str, Enum):
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE_V3 = "large-v3"


class TTSEngine(str, Enum):
    PIPER = "piper"
    XTTS = "xtts"
    HYBRID = "hybrid"


class VoiceConfig(BaseModel):
    """Configuration for voice interaction layer."""

    # STT Configuration
    stt_model: STTModel = STTModel.MEDIUM
    stt_device: str = "cuda"  # "cuda" or "cpu"
    stt_compute_type: str = "float16"  # "float16", "int8", or "float32"
    stt_language: str = "en"

    # VAD Configuration
    vad_threshold: float = 0.5
    min_speech_duration_ms: int = 250
    min_silence_duration_ms: int = 700  # Silence before processing
    max_speech_duration_s: float = 30.0  # Max single utterance

    # TTS Configuration
    tts_engine: TTSEngine = TTSEngine.HYBRID
    piper_model: str = "en_US-lessac-medium"
    piper_model_path: Optional[Path] = None
    xtts_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    voice_sample_path: Optional[Path] = None  # For voice cloning

    # Hybrid TTS thresholds
    short_response_chars: int = 100  # Use Piper below this

    # Audio format
    sample_rate: int = 16000
    channels: int = 1

    # Latency targets
    max_stt_latency_ms: int = 2000
    max_tts_latency_ms: int = 3000

    class Config:
        use_enum_values = True


# Global config instance
_voice_config: Optional[VoiceConfig] = None


def get_voice_config() -> VoiceConfig:
    """Get the voice configuration, creating from environment if needed."""
    global _voice_config

    if _voice_config is None:
        _voice_config = VoiceConfig(
            stt_model=STTModel(os.getenv("STT_MODEL", "medium")),
            stt_device=os.getenv("STT_DEVICE", "cuda"),
            stt_compute_type=os.getenv("STT_COMPUTE_TYPE", "float16"),
            tts_engine=TTSEngine(os.getenv("TTS_ENGINE", "hybrid")),
            piper_model=os.getenv("PIPER_MODEL", "en_US-lessac-medium"),
        )

        # Check for voice sample path
        voice_sample = os.getenv("VOICE_SAMPLE_PATH")
        if voice_sample:
            _voice_config.voice_sample_path = Path(voice_sample)

    return _voice_config


def set_voice_config(config: VoiceConfig) -> None:
    """Set the global voice configuration."""
    global _voice_config
    _voice_config = config
