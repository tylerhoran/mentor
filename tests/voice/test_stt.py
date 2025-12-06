"""Tests for Speech-to-Text service."""

import sys
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest


class TestWhisperSTT:
    """Tests for WhisperSTT class."""

    @pytest.fixture(autouse=True)
    def setup_mock_whisper(self):
        """Setup mock for faster_whisper module."""
        self.mock_whisper_model = MagicMock()
        self.mock_module = MagicMock()
        self.mock_module.WhisperModel = self.mock_whisper_model

        with patch.dict(sys.modules, {"faster_whisper": self.mock_module}):
            yield

    def test_initialization(self, voice_config):
        """Test STT initialization."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        stt = WhisperSTT(voice_config)

        assert stt.config == voice_config
        self.mock_whisper_model.assert_called_once_with(
            voice_config.stt_model,
            device=voice_config.stt_device,
            compute_type=voice_config.stt_compute_type,
        )

    def test_transcribe_basic(self, voice_config, sample_audio):
        """Test basic transcription."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        # Setup mock
        mock_segment = Mock()
        mock_segment.text = " Hello world "
        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([mock_segment], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)
        result = stt.transcribe(sample_audio)

        assert result == "Hello world"
        mock_model_instance.transcribe.assert_called_once()

    def test_transcribe_empty_audio(self, voice_config, silence_audio):
        """Test transcription of silence."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)
        result = stt.transcribe(silence_audio)

        assert result == ""

    def test_transcribe_multiple_segments(self, voice_config, sample_audio):
        """Test transcription with multiple segments."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_seg1 = Mock(text=" First segment ")
        mock_seg2 = Mock(text=" Second segment ")
        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([mock_seg1, mock_seg2], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)
        result = stt.transcribe(sample_audio)

        assert result == "First segment Second segment"

    def test_transcribe_with_language(self, voice_config, sample_audio):
        """Test transcription with specific language."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_segment = Mock(text=" Hola mundo ")
        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([mock_segment], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)
        result = stt.transcribe(sample_audio, language="es")

        assert result == "Hola mundo"
        call_args = mock_model_instance.transcribe.call_args
        assert call_args[1].get("language") == "es"

    def test_transcribe_with_timestamps(self, voice_config, sample_audio):
        """Test transcription with word timestamps."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_word1 = Mock(word="Hello", start=0.0, end=0.5, probability=0.95)
        mock_word2 = Mock(word="world", start=0.6, end=1.0, probability=0.92)
        mock_segment = Mock(text=" Hello world ", words=[mock_word1, mock_word2])
        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([mock_segment], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)
        words = stt.transcribe_with_timestamps(sample_audio)

        # transcribe_with_timestamps returns a list of dicts
        assert isinstance(words, list)
        assert len(words) == 2
        assert words[0]["word"] == "Hello"
        assert words[1]["word"] == "world"

    def test_get_speech_features_empty(self, voice_config, silence_audio):
        """Test getting speech features from empty words list."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)
        # get_speech_features takes audio and words list
        features = stt.get_speech_features(silence_audio, [])

        # When words is empty, returns None for speech_rate and 0 for pause metrics
        assert features["speech_rate_wpm"] is None
        assert features["pause_count"] == 0
        assert features["average_pause_duration_ms"] == 0.0

    def test_get_speech_features_with_words(self, voice_config, sample_audio):
        """Test getting speech features with words."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_model_instance = Mock()
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)

        # Provide words as the second argument
        words = [
            {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.95},
            {"word": "world", "start": 0.6, "end": 1.0, "probability": 0.92},
        ]
        features = stt.get_speech_features(sample_audio, words)

        assert features["speech_rate_wpm"] > 0
        assert "pause_count" in features
        assert "average_pause_duration_ms" in features

    def test_transcribe_streaming(self, voice_config):
        """Test streaming transcription."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        mock_segment = Mock(text=" Partial text ")
        mock_model_instance = Mock()
        mock_model_instance.transcribe.return_value = ([mock_segment], Mock())
        self.mock_whisper_model.return_value = mock_model_instance

        stt = WhisperSTT(voice_config)

        # Create audio chunks generator - need enough audio for streaming
        def audio_generator():
            # Yield 3 seconds of audio (enough to trigger transcription)
            for _ in range(3):
                yield np.zeros(voice_config.sample_rate, dtype=np.float32)

        results = list(stt.transcribe_streaming(audio_generator()))

        assert len(results) > 0

    def test_transcribe_without_model(self, voice_config, sample_audio):
        """Test transcription when model loading fails."""
        from mentor.voice.stt.whisper_service import WhisperSTT

        self.mock_whisper_model.side_effect = RuntimeError("Model load failed")

        with pytest.raises(RuntimeError, match="Model load failed"):
            WhisperSTT(voice_config)


class TestGetWhisperSTT:
    """Tests for get_whisper_stt singleton function."""

    @pytest.fixture(autouse=True)
    def setup_mock_whisper(self):
        """Setup mock for faster_whisper module."""
        self.mock_whisper_model = MagicMock()
        self.mock_module = MagicMock()
        self.mock_module.WhisperModel = self.mock_whisper_model

        with patch.dict(sys.modules, {"faster_whisper": self.mock_module}):
            yield

    def test_singleton(self):
        """Test that get_whisper_stt returns singleton."""
        from mentor.voice.stt import whisper_service

        # Reset singleton
        whisper_service._whisper_stt = None

        from mentor.voice.stt.whisper_service import get_whisper_stt

        stt1 = get_whisper_stt()
        stt2 = get_whisper_stt()

        assert stt1 is stt2
