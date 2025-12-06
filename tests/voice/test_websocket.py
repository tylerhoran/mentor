"""Tests for voice WebSocket handler."""

import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import numpy as np
import pytest

from mentor.voice.session import VoiceInteraction, VoiceSession, VoiceSessionState


class TestVoiceWebSocketHandler:
    """Tests for VoiceWebSocketHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a WebSocket handler."""
        from mentor.voice.websocket import VoiceWebSocketHandler

        h = VoiceWebSocketHandler()
        h._initialized = True
        h.stt = Mock()
        h.vad = Mock()
        h.tts = AsyncMock()
        h.gaming_detector = Mock()
        return h

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket."""
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        ws.send_bytes = AsyncMock()
        ws.receive = AsyncMock()
        ws.close = AsyncMock()
        return ws

    @pytest.fixture
    def mock_session(self):
        """Create a mock voice session."""
        return VoiceSession(
            session_id="test-session",
            student_id="student-123",
            course_id="course-456",
        )

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test handler initialization."""
        from mentor.voice.websocket import VoiceWebSocketHandler

        handler = VoiceWebSocketHandler()

        with patch("mentor.voice.websocket.get_whisper_stt") as mock_stt:
            with patch("mentor.voice.websocket.get_vad") as mock_vad:
                with patch("mentor.voice.websocket.get_tts_service") as mock_tts:
                    mock_stt.return_value = Mock()
                    mock_vad.return_value = Mock()
                    mock_tts_instance = AsyncMock()
                    mock_tts_instance.warmup = AsyncMock()
                    mock_tts.return_value = mock_tts_instance

                    await handler.initialize()

                    assert handler._initialized is True

    @pytest.mark.asyncio
    async def test_send_status(self, handler, mock_websocket):
        """Test sending status messages."""
        await handler._send_status(mock_websocket, "ready", {"sample_rate": 16000})

        mock_websocket.send_json.assert_called_once()
        call_args = mock_websocket.send_json.call_args[0][0]

        assert call_args["status"] == "ready"
        assert call_args["data"]["sample_rate"] == 16000

    @pytest.mark.asyncio
    async def test_send_status_without_data(self, handler, mock_websocket):
        """Test sending status without additional data."""
        await handler._send_status(mock_websocket, "idle")

        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "idle"
        # When no data passed, "data" key should not be present
        assert "data" not in call_args

    @pytest.mark.asyncio
    async def test_handle_control_reset(self, handler, mock_websocket, mock_session):
        """Test handling reset command."""
        handler.vad = Mock()
        handler.vad.reset = Mock()

        await handler._handle_control(
            mock_websocket,
            json.dumps({"command": "reset"}),
            mock_session,
        )

        handler.vad.reset.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_control_ping(self, handler, mock_websocket, mock_session):
        """Test handling ping command."""
        await handler._handle_control(
            mock_websocket,
            json.dumps({"command": "ping"}),
            mock_session,
        )

        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "pong"

    @pytest.mark.asyncio
    async def test_handle_control_get_metrics(self, handler, mock_websocket, mock_session):
        """Test handling get_metrics command."""
        mock_session.total_interactions = 5
        mock_session.total_student_speech_ms = 10000

        await handler._handle_control(
            mock_websocket,
            json.dumps({"command": "get_metrics"}),
            mock_session,
        )

        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "metrics"

    @pytest.mark.asyncio
    async def test_handle_control_get_session(self, handler, mock_websocket, mock_session):
        """Test handling get_session command."""
        await handler._handle_control(
            mock_websocket,
            json.dumps({"command": "get_session"}),
            mock_session,
        )

        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "session"
        assert call_args["data"]["session_id"] == mock_session.session_id

    @pytest.mark.asyncio
    async def test_handle_control_end(self, handler, mock_websocket, mock_session):
        """Test handling end command."""
        await handler._handle_control(
            mock_websocket,
            json.dumps({"command": "end"}),
            mock_session,
        )

        # End command sends "ended" status and closes websocket
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "ended"
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_control_unknown(self, handler, mock_websocket, mock_session):
        """Test handling unknown command."""
        await handler._handle_control(
            mock_websocket,
            json.dumps({"command": "unknown_command"}),
            mock_session,
        )

        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "unknown_command"

    @pytest.mark.asyncio
    async def test_handle_control_invalid_json(self, handler, mock_websocket, mock_session):
        """Test handling invalid JSON."""
        await handler._handle_control(
            mock_websocket,
            "not valid json",
            mock_session,
        )

        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["status"] == "error"
        assert "Invalid JSON" in call_args["data"]["message"]

    @pytest.mark.asyncio
    async def test_handle_audio_no_services(self, mock_websocket, mock_session):
        """Test audio handling when services not initialized."""
        from mentor.voice.websocket import VoiceWebSocketHandler

        handler = VoiceWebSocketHandler()
        handler._initialized = False

        audio_data = np.zeros(4096, dtype=np.float32).tobytes()

        async def mock_callback(msg, sid):
            return "response"

        # Should not raise, just return early
        await handler._handle_audio(
            mock_websocket,
            audio_data,
            mock_session,
            mock_callback,
        )

    @pytest.mark.asyncio
    async def test_handle_audio_speaking(self, handler, mock_websocket, mock_session):
        """Test audio handling when speaking (should process VAD anyway)."""
        mock_session.state = VoiceSessionState.SPEAKING

        from mentor.voice.stt.vad import SpeechState, VADResult

        handler.vad.process_chunk = Mock(
            return_value=VADResult(state=SpeechState.SILENCE, speech_probability=0.1)
        )

        audio_data = np.zeros(4096, dtype=np.float32).tobytes()

        async def mock_callback(msg, sid):
            return "response"

        await handler._handle_audio(
            mock_websocket,
            audio_data,
            mock_session,
            mock_callback,
        )

    @pytest.mark.asyncio
    async def test_process_utterance_empty_transcription(
        self, handler, mock_websocket, mock_session
    ):
        """Test processing empty transcription."""
        handler.stt.transcribe_with_timestamps.return_value = []
        handler.stt.transcribe.return_value = ""
        handler.stt.get_speech_features.return_value = {}
        handler.vad.reset = Mock()

        audio = np.zeros(16000, dtype=np.float32)

        async def mock_callback(msg, sid):
            return "response"

        await handler._process_utterance(
            mock_websocket,
            audio,
            mock_session,
            mock_callback,
        )

        # Should not call TTS for empty transcription
        handler.tts.synthesize.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_utterance_full_flow(self, handler, mock_websocket, mock_session):
        """Test full utterance processing flow."""
        handler.stt.transcribe_with_timestamps.return_value = [
            {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.95},
            {"word": "tutor", "start": 0.6, "end": 1.0, "probability": 0.92},
        ]
        handler.stt.get_speech_features.return_value = {
            "speech_rate_wpm": 120.0,
            "pause_count": 0,
            "average_pause_duration_ms": 0.0,
        }
        handler.tts.synthesize = AsyncMock(return_value=b"audio_response")
        handler.tts.sample_rate = 16000
        # Mock gaming analysis result with all needed attributes
        mock_analysis = Mock()
        mock_analysis.confidence = 0.1
        mock_analysis.flags = []
        mock_analysis.has_flags = False
        handler.gaming_detector.analyze_interaction.return_value = mock_analysis
        handler.vad.reset = Mock()

        audio = np.zeros(16000, dtype=np.float32)

        async def mock_callback(msg, sid):
            return "Tutor response"

        await handler._process_utterance(
            mock_websocket,
            audio,
            mock_session,
            mock_callback,
        )

        # Verify transcription was sent
        assert any(
            call[0][0].get("status") == "transcription"
            for call in mock_websocket.send_json.call_args_list
        )


class TestGetVoiceHandler:
    """Tests for get_voice_handler function."""

    def test_returns_handler(self):
        """Test that get_voice_handler returns a handler."""
        from mentor.voice.websocket import get_voice_handler

        handler = get_voice_handler()

        assert handler is not None

    def test_returns_singleton(self):
        """Test that get_voice_handler returns the same instance."""
        from mentor.voice.websocket import get_voice_handler

        handler1 = get_voice_handler()
        handler2 = get_voice_handler()

        assert handler1 is handler2
