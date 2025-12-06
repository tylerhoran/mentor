"""Tests for voice configuration."""

import os
from unittest.mock import patch

from mentor.voice import config as config_module
from mentor.voice.config import (
    STTModel,
    TTSEngine,
    VoiceConfig,
    get_voice_config,
    set_voice_config,
)


class TestVoiceConfig:
    """Tests for VoiceConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = VoiceConfig()

        assert config.stt_model == STTModel.MEDIUM
        assert config.stt_device == "cuda"
        assert config.stt_compute_type == "float16"
        assert config.stt_language == "en"
        assert config.tts_engine == TTSEngine.HYBRID
        assert config.sample_rate == 16000
        assert config.channels == 1

    def test_custom_config(self, voice_config):
        """Test custom configuration."""
        assert voice_config.stt_model == STTModel.TINY
        assert voice_config.stt_device == "cpu"
        assert voice_config.tts_engine == TTSEngine.PIPER

    def test_vad_config(self):
        """Test VAD configuration values."""
        config = VoiceConfig(
            vad_threshold=0.6,
            min_speech_duration_ms=300,
            min_silence_duration_ms=800,
            max_speech_duration_s=20.0,
        )

        assert config.vad_threshold == 0.6
        assert config.min_speech_duration_ms == 300
        assert config.min_silence_duration_ms == 800
        assert config.max_speech_duration_s == 20.0

    def test_tts_config(self):
        """Test TTS configuration values."""
        config = VoiceConfig(
            tts_engine=TTSEngine.XTTS,
            piper_model="en_GB-alba-medium",
            short_response_chars=150,
        )

        assert config.tts_engine == TTSEngine.XTTS
        assert config.piper_model == "en_GB-alba-medium"
        assert config.short_response_chars == 150

    def test_voice_sample_path(self, tmp_path):
        """Test voice sample path configuration."""
        sample_path = tmp_path / "voice_sample.wav"
        sample_path.touch()

        config = VoiceConfig(voice_sample_path=sample_path)

        assert config.voice_sample_path == sample_path
        assert config.voice_sample_path.exists()

    def test_latency_targets(self):
        """Test latency target configuration."""
        config = VoiceConfig(
            max_stt_latency_ms=3000,
            max_tts_latency_ms=5000,
        )

        assert config.max_stt_latency_ms == 3000
        assert config.max_tts_latency_ms == 5000


class TestSTTModel:
    """Tests for STTModel enum."""

    def test_all_models(self):
        """Test all available models."""
        assert STTModel.TINY.value == "tiny"
        assert STTModel.BASE.value == "base"
        assert STTModel.SMALL.value == "small"
        assert STTModel.MEDIUM.value == "medium"
        assert STTModel.LARGE_V3.value == "large-v3"

    def test_model_from_string(self):
        """Test creating model from string."""
        assert STTModel("medium") == STTModel.MEDIUM
        assert STTModel("large-v3") == STTModel.LARGE_V3


class TestTTSEngine:
    """Tests for TTSEngine enum."""

    def test_all_engines(self):
        """Test all available engines."""
        assert TTSEngine.PIPER.value == "piper"
        assert TTSEngine.XTTS.value == "xtts"
        assert TTSEngine.HYBRID.value == "hybrid"

    def test_engine_from_string(self):
        """Test creating engine from string."""
        assert TTSEngine("hybrid") == TTSEngine.HYBRID
        assert TTSEngine("piper") == TTSEngine.PIPER


class TestGetVoiceConfig:
    """Tests for get_voice_config function."""

    def test_get_default_config(self):
        """Test getting default configuration."""
        # Reset global config

        config_module._voice_config = None

        config = get_voice_config()

        assert config is not None
        assert isinstance(config, VoiceConfig)

    def test_config_singleton(self):
        """Test that config is a singleton."""
        config1 = get_voice_config()
        config2 = get_voice_config()

        assert config1 is config2

    @patch.dict(
        os.environ,
        {
            "STT_MODEL": "small",
            "STT_DEVICE": "cpu",
            "TTS_ENGINE": "piper",
        },
    )
    def test_config_from_environment(self):
        """Test configuration from environment variables."""
        import mentor.voice.config as config_module

        config_module._voice_config = None

        config = get_voice_config()

        assert config.stt_model == STTModel.SMALL
        assert config.stt_device == "cpu"
        assert config.tts_engine == TTSEngine.PIPER


class TestSetVoiceConfig:
    """Tests for set_voice_config function."""

    def test_set_custom_config(self, voice_config):
        """Test setting custom configuration."""
        set_voice_config(voice_config)

        retrieved = get_voice_config()

        assert retrieved is voice_config
        assert retrieved.stt_model == STTModel.TINY

    def test_override_config(self):
        """Test overriding existing configuration."""
        config1 = VoiceConfig(stt_model=STTModel.SMALL)
        config2 = VoiceConfig(stt_model=STTModel.LARGE_V3)

        set_voice_config(config1)
        assert get_voice_config().stt_model == STTModel.SMALL

        set_voice_config(config2)
        assert get_voice_config().stt_model == STTModel.LARGE_V3
