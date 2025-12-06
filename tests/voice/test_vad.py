"""Tests for Voice Activity Detection."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from mentor.voice.stt.vad import SileroVAD, SpeechState, VADResult, get_vad


class TestVADResult:
    """Tests for VADResult dataclass."""

    def test_silence_result(self):
        """Test silence VAD result."""
        result = VADResult(
            state=SpeechState.SILENCE,
            speech_probability=0.1,
        )

        assert result.state == SpeechState.SILENCE
        assert result.audio is None
        assert result.speech_probability == 0.1
        assert result.duration_ms == 0

    def test_speaking_result(self):
        """Test speaking VAD result."""
        result = VADResult(
            state=SpeechState.SPEAKING,
            speech_probability=0.9,
            duration_ms=1500,
        )

        assert result.state == SpeechState.SPEAKING
        assert result.duration_ms == 1500

    def test_finished_result(self, sample_audio):
        """Test finished VAD result with audio."""
        result = VADResult(
            state=SpeechState.FINISHED,
            audio=sample_audio,
            speech_probability=0.2,
            duration_ms=2000,
        )

        assert result.state == SpeechState.FINISHED
        assert result.audio is not None
        assert len(result.audio) == len(sample_audio)


class TestSpeechState:
    """Tests for SpeechState enum."""

    def test_states(self):
        """Test all speech states."""
        assert SpeechState.SILENCE.value == "silence"
        assert SpeechState.SPEAKING.value == "speaking"
        assert SpeechState.FINISHED.value == "finished"


class TestSileroVAD:
    """Tests for SileroVAD class."""

    @patch("torch.hub.load")
    def test_initialization(self, mock_hub_load, voice_config):
        """Test VAD initialization."""
        mock_model = Mock()
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)

        assert vad.model is mock_model
        assert vad.config == voice_config
        mock_hub_load.assert_called_once()

    @patch("torch.hub.load")
    def test_reset_state(self, mock_hub_load, voice_config):
        """Test resetting VAD state."""
        mock_model = Mock()
        mock_model.reset_states = Mock()
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)
        vad.speech_buffer = np.ones(1000, dtype=np.float32)
        vad.speech_samples = 1000
        vad.silence_samples = 500
        vad.is_speaking = True

        vad.reset()

        assert len(vad.speech_buffer) == 0
        assert vad.speech_samples == 0
        assert vad.silence_samples == 0
        assert vad.is_speaking is False

    @patch("torch.hub.load")
    def test_process_silence_chunk(self, mock_hub_load, voice_config, silence_audio):
        """Test processing silence when not speaking."""
        mock_model = Mock()
        mock_model.return_value = Mock(item=Mock(return_value=0.1))  # Low probability
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)

        # Process a small chunk
        chunk = silence_audio[:1600]  # 100ms
        result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SILENCE
        assert result.speech_probability == 0.1

    @patch("torch.hub.load")
    def test_process_speech_chunk(self, mock_hub_load, voice_config, sample_audio):
        """Test processing speech chunk."""
        mock_model = Mock()
        mock_model.return_value = Mock(item=Mock(return_value=0.9))  # High probability
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)

        chunk = sample_audio[:1600]  # 100ms
        result = vad.process_chunk(chunk)

        assert result.state == SpeechState.SPEAKING
        assert result.speech_probability == 0.9
        assert vad.is_speaking is True

    @patch("torch.hub.load")
    def test_speech_to_silence_transition(self, mock_hub_load, voice_config):
        """Test transition from speech to silence (utterance end)."""
        mock_model = Mock()
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)
        vad.config.min_silence_duration_ms = 100  # Short for testing
        vad.config.min_speech_duration_ms = 50

        # First, simulate speech
        mock_model.return_value = Mock(item=Mock(return_value=0.9))
        speech_chunk = np.random.randn(3200).astype(np.float32)  # 200ms
        vad.process_chunk(speech_chunk)

        assert vad.is_speaking is True

        # Then simulate silence
        mock_model.return_value = Mock(item=Mock(return_value=0.1))
        silence_chunk = np.zeros(3200, dtype=np.float32)  # 200ms > min_silence
        result = vad.process_chunk(silence_chunk)

        assert result.state == SpeechState.FINISHED
        assert result.audio is not None

    @patch("torch.hub.load")
    def test_max_duration_cutoff(self, mock_hub_load, voice_config):
        """Test max speech duration cutoff."""
        mock_model = Mock()
        mock_model.return_value = Mock(item=Mock(return_value=0.9))
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)
        vad.config.max_speech_duration_s = 0.5  # Short for testing

        # Send enough audio to exceed max duration
        for _ in range(10):
            chunk = np.random.randn(8000).astype(np.float32)  # 500ms each
            result = vad.process_chunk(chunk)
            if result.state == SpeechState.FINISHED:
                break

        assert result.state == SpeechState.FINISHED

    @patch("torch.hub.load")
    def test_too_short_speech_discarded(self, mock_hub_load, voice_config):
        """Test that speech shorter than threshold is discarded."""
        mock_model = Mock()
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)
        vad.config.min_speech_duration_ms = 500
        vad.config.min_silence_duration_ms = 100

        # Short speech
        mock_model.return_value = Mock(item=Mock(return_value=0.9))
        short_speech = np.random.randn(800).astype(np.float32)  # 50ms
        vad.process_chunk(short_speech)

        # Silence
        mock_model.return_value = Mock(item=Mock(return_value=0.1))
        silence = np.zeros(3200, dtype=np.float32)  # 200ms
        result = vad.process_chunk(silence)

        # Should be discarded as too short
        assert result.state == SpeechState.SILENCE
        assert vad.is_speaking is False

    @patch("torch.hub.load")
    def test_get_current_audio(self, mock_hub_load, voice_config, sample_audio):
        """Test getting current audio buffer."""
        mock_model = Mock()
        mock_model.return_value = Mock(item=Mock(return_value=0.9))
        mock_hub_load.return_value = (mock_model, Mock())

        vad = SileroVAD(voice_config)

        # No audio yet
        assert vad.get_current_audio() is None

        # Add audio
        vad.process_chunk(sample_audio[:1600])
        audio = vad.get_current_audio()

        assert audio is not None
        assert len(audio) == 1600

    @patch("torch.hub.load")
    def test_fallback_without_model(self, mock_hub_load, voice_config, sample_audio):
        """Test fallback behavior when model fails to load."""
        mock_hub_load.side_effect = RuntimeError("Load failed")

        with pytest.raises(RuntimeError, match="Load failed"):
            SileroVAD(voice_config)


class TestGetVAD:
    """Tests for get_vad singleton function."""

    @patch("torch.hub.load")
    def test_singleton(self, mock_hub_load):
        """Test VAD singleton pattern."""
        mock_model = Mock()
        mock_hub_load.return_value = (mock_model, Mock())

        import mentor.voice.stt.vad as vad_module

        vad_module._vad_instance = None

        vad1 = get_vad()
        vad2 = get_vad()

        assert vad1 is vad2
