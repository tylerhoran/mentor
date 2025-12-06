"""Tests for Text-to-Speech services."""

import sys
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from mentor.voice.config import TTSEngine, VoiceConfig
from mentor.voice.tts.base import TTSService


class TestTTSServiceBase:
    """Tests for TTSService base class."""

    def test_abstract_methods(self):
        """Test that TTSService has required abstract methods."""
        assert hasattr(TTSService, "synthesize")
        assert hasattr(TTSService, "sample_rate")
        assert hasattr(TTSService, "latency_estimate_ms")
        assert hasattr(TTSService, "synthesize_streaming")

    @pytest.mark.asyncio
    async def test_warmup_default(self):
        """Test default warmup implementation."""

        # Create a concrete implementation for testing
        class ConcreteTTS(TTSService):
            async def synthesize(self, text: str) -> bytes:
                return b""

            async def synthesize_streaming(self, text: str) -> AsyncGenerator[bytes, None]:
                yield b""

            @property
            def sample_rate(self) -> int:
                return 16000

            @property
            def latency_estimate_ms(self) -> int:
                return 100

        tts = ConcreteTTS()
        # warmup should exist and work
        await tts.warmup()


class TestPiperTTS:
    """Tests for PiperTTS service."""

    def test_initialization(self, voice_config):
        """Test Piper initialization."""
        from mentor.voice.tts.piper_service import PiperTTS

        with patch.object(PiperTTS, "_check_installation", return_value=True):
            tts = PiperTTS(voice_config)
            assert tts.config == voice_config
            assert tts._piper_available is True

    def test_sample_rate(self, voice_config):
        """Test Piper sample rate."""
        from mentor.voice.tts.piper_service import PiperTTS

        with patch.object(PiperTTS, "_check_installation", return_value=True):
            tts = PiperTTS(voice_config)
            # PiperTTS has fixed sample rate of 22050
            assert tts.sample_rate == 22050

    def test_latency_estimate(self, voice_config):
        """Test Piper latency estimate."""
        from mentor.voice.tts.piper_service import PiperTTS

        with patch.object(PiperTTS, "_check_installation", return_value=True):
            tts = PiperTTS(voice_config)
            assert tts.latency_estimate_ms == 300  # Very fast

    @pytest.mark.asyncio
    async def test_synthesize(self, voice_config):
        """Test Piper synthesis."""
        from mentor.voice.tts.piper_service import PiperTTS

        with patch.object(PiperTTS, "_check_installation", return_value=True):
            tts = PiperTTS(voice_config)

            # Mock the internal synthesis methods
            with patch.object(tts, "_synthesize_python", new_callable=AsyncMock) as mock_synth:
                mock_synth.return_value = b"audio_data"
                audio = await tts.synthesize("Hello world")

                assert audio == b"audio_data"
                mock_synth.assert_called_once_with("Hello world")

    @pytest.mark.asyncio
    async def test_synthesize_streaming(self, voice_config):
        """Test Piper streaming synthesis."""
        from mentor.voice.tts.piper_service import PiperTTS

        with patch.object(PiperTTS, "_check_installation", return_value=True):
            tts = PiperTTS(voice_config)

            # Mock synthesize for streaming (Piper doesn't support true streaming)
            with patch.object(tts, "synthesize", new_callable=AsyncMock) as mock_synth:
                mock_synth.return_value = b"audio_data"

                chunks = []
                async for chunk in tts.synthesize_streaming("Hello world"):
                    chunks.append(chunk)

                assert len(chunks) == 1
                assert chunks[0] == b"audio_data"


class TestXTTS:
    """Tests for XTTS service."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup mocks for TTS and torch."""
        self.mock_tts_instance = MagicMock()
        self.mock_tts_instance.to.return_value = self.mock_tts_instance
        self.mock_tts_instance.tts.return_value = np.zeros(24000, dtype=np.float32)
        self.mock_tts_instance.speakers = None

        self.mock_tts_class = MagicMock(return_value=self.mock_tts_instance)
        self.mock_tts_module = MagicMock()
        self.mock_tts_module.api.TTS = self.mock_tts_class

        self.mock_torch = MagicMock()
        self.mock_torch.cuda.is_available.return_value = False

        with patch.dict(
            sys.modules,
            {
                "TTS": self.mock_tts_module,
                "TTS.api": self.mock_tts_module.api,
                "torch": self.mock_torch,
            },
        ):
            yield

    def test_initialization(self, voice_config):
        """Test XTTS initialization."""
        from mentor.voice.tts.xtts_service import XTTS

        xtts = XTTS(voice_config)

        assert xtts.tts is not None
        assert xtts._device == "cpu"

    def test_initialization_with_gpu(self, voice_config):
        """Test XTTS initialization with GPU."""
        self.mock_torch.cuda.is_available.return_value = True

        from mentor.voice.tts.xtts_service import XTTS

        xtts = XTTS(voice_config)

        assert xtts._device == "cuda"

    @pytest.mark.asyncio
    async def test_synthesize(self, voice_config):
        """Test XTTS synthesis."""
        from mentor.voice.tts.xtts_service import XTTS

        xtts = XTTS(voice_config)
        audio = await xtts.synthesize("Hello world")

        assert isinstance(audio, bytes)
        assert len(audio) > 0

    @pytest.mark.asyncio
    async def test_synthesize_with_voice_clone(self, voice_config, tmp_path):
        """Test XTTS synthesis with voice cloning."""
        from mentor.voice.tts.xtts_service import XTTS

        # Create voice sample
        voice_sample = tmp_path / "voice.wav"
        voice_sample.touch()
        voice_config.voice_sample_path = voice_sample

        xtts = XTTS(voice_config)
        await xtts.synthesize("Hello")

        # Verify voice cloning was used
        call_kwargs = self.mock_tts_instance.tts.call_args[1]
        assert "speaker_wav" in call_kwargs

    def test_sample_rate(self, voice_config):
        """Test XTTS sample rate."""
        from mentor.voice.tts.xtts_service import XTTS

        xtts = XTTS(voice_config)

        assert xtts.sample_rate == 24000

    def test_latency_estimate(self, voice_config):
        """Test XTTS latency estimate."""
        from mentor.voice.tts.xtts_service import XTTS

        xtts = XTTS(voice_config)

        assert xtts.latency_estimate_ms == 3000

    def test_has_voice_clone(self, voice_config, tmp_path):
        """Test voice clone detection."""
        from mentor.voice.tts.xtts_service import XTTS

        xtts = XTTS(voice_config)

        assert xtts.has_voice_clone is False

        voice_sample = tmp_path / "voice.wav"
        voice_sample.touch()
        xtts.set_voice_sample(voice_sample)

        assert xtts.has_voice_clone is True


class TestHybridTTS:
    """Tests for HybridTTS service."""

    @patch("mentor.voice.tts.hybrid.PiperTTS")
    @patch("mentor.voice.tts.hybrid.XTTS")
    def test_initialization(self, mock_xtts_class, mock_piper_class, voice_config):
        """Test hybrid TTS initialization."""
        from mentor.voice.tts.hybrid import HybridTTS

        mock_piper = Mock()
        mock_xtts = Mock()
        mock_piper_class.return_value = mock_piper
        mock_xtts_class.return_value = mock_xtts

        hybrid = HybridTTS(voice_config)

        assert hybrid.fast_tts is mock_piper
        assert hybrid.quality_tts is mock_xtts

    @pytest.mark.asyncio
    @patch("mentor.voice.tts.hybrid.PiperTTS")
    @patch("mentor.voice.tts.hybrid.XTTS")
    async def test_synthesize_short(self, mock_xtts_class, mock_piper_class, voice_config):
        """Test synthesis of short text uses fast engine."""
        from mentor.voice.tts.hybrid import HybridTTS

        mock_piper = AsyncMock()
        mock_piper.synthesize = AsyncMock(return_value=b"piper_audio")
        mock_xtts = AsyncMock()
        mock_piper_class.return_value = mock_piper
        mock_xtts_class.return_value = mock_xtts

        hybrid = HybridTTS(voice_config)
        audio = await hybrid.synthesize("I see.")

        assert audio == b"piper_audio"
        mock_piper.synthesize.assert_called_once()

    @pytest.mark.asyncio
    @patch("mentor.voice.tts.hybrid.PiperTTS")
    @patch("mentor.voice.tts.hybrid.XTTS")
    async def test_synthesize_long(self, mock_xtts_class, mock_piper_class, voice_config):
        """Test synthesis of long text uses quality engine."""
        from mentor.voice.tts.hybrid import HybridTTS

        mock_piper = AsyncMock()
        mock_xtts = AsyncMock()
        mock_xtts.synthesize = AsyncMock(return_value=b"xtts_audio")
        mock_piper_class.return_value = mock_piper
        mock_xtts_class.return_value = mock_xtts

        hybrid = HybridTTS(voice_config)
        long_text = "This is a much longer text that should use the quality engine. " * 5
        audio = await hybrid.synthesize(long_text)

        assert audio == b"xtts_audio"
        mock_xtts.synthesize.assert_called_once()

    @patch("mentor.voice.tts.hybrid.PiperTTS")
    @patch("mentor.voice.tts.hybrid.XTTS")
    def test_get_engine_for_text(self, mock_xtts, mock_piper, voice_config):
        """Test engine selection preview."""
        from mentor.voice.tts.hybrid import HybridTTS

        mock_piper.return_value = Mock()
        mock_xtts.return_value = Mock()

        hybrid = HybridTTS(voice_config)

        assert hybrid.get_engine_for_text("OK") == "piper"
        assert hybrid.get_engine_for_text("A" * 200) == "xtts"

    @pytest.mark.asyncio
    @patch("mentor.voice.tts.hybrid.PiperTTS")
    @patch("mentor.voice.tts.hybrid.XTTS")
    async def test_warmup(self, mock_xtts_class, mock_piper_class, voice_config):
        """Test warmup calls both engines."""
        from mentor.voice.tts.hybrid import HybridTTS

        mock_piper = AsyncMock()
        mock_piper.warmup = AsyncMock()
        mock_xtts = AsyncMock()
        mock_xtts.warmup = AsyncMock()
        mock_piper_class.return_value = mock_piper
        mock_xtts_class.return_value = mock_xtts

        hybrid = HybridTTS(voice_config)
        await hybrid.warmup()

        mock_piper.warmup.assert_called_once()
        mock_xtts.warmup.assert_called_once()


class TestGetTTSService:
    """Tests for get_tts_service factory function."""

    def test_get_piper_service(self):
        """Test getting Piper service."""
        from mentor.voice.tts import get_tts_service
        from mentor.voice.tts.piper_service import PiperTTS

        with patch.object(PiperTTS, "__init__", return_value=None):
            config = VoiceConfig(tts_engine=TTSEngine.PIPER)
            tts = get_tts_service(config)
            assert isinstance(tts, PiperTTS)

    def test_get_xtts_service(self):
        """Test getting XTTS service."""
        from mentor.voice.tts import get_tts_service
        from mentor.voice.tts.xtts_service import XTTS

        with patch.object(XTTS, "__init__", return_value=None):
            config = VoiceConfig(tts_engine=TTSEngine.XTTS)
            tts = get_tts_service(config)
            assert isinstance(tts, XTTS)

    def test_get_hybrid_service(self):
        """Test getting hybrid service."""
        from mentor.voice.tts import get_tts_service
        from mentor.voice.tts.hybrid import HybridTTS

        with patch.object(HybridTTS, "__init__", return_value=None):
            config = VoiceConfig(tts_engine=TTSEngine.HYBRID)
            tts = get_tts_service(config)
            assert isinstance(tts, HybridTTS)
