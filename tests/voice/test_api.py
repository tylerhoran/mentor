"""Tests for voice API routes."""

import io
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from mentor.api.routes.voice import router


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestVoiceConfigEndpoint:
    """Tests for /voice/config endpoint."""

    def test_get_config(self, client):
        with patch("mentor.api.routes.voice.get_voice_config") as mock_config:
            mock_config.return_value = Mock(
                stt_model="medium",
                stt_device="cuda",
                tts_engine="hybrid",
                sample_rate=16000,
                voice_sample_path=None,
                vad_threshold=0.5,
                min_silence_duration_ms=700,
            )

            response = client.get("/api/voice/config")

            assert response.status_code == 200
            data = response.json()
            assert data["stt_model"] == "medium"
            assert data["tts_engine"] == "hybrid"
            assert data["sample_rate"] == 16000
            assert data["has_voice_clone"] is False


class TestVoiceSampleEndpoints:
    """Tests for voice sample upload/delete endpoints."""

    def test_upload_voice_sample(self, client, tmp_path):
        """Test uploading voice sample."""
        # Create a mock audio file
        audio_content = b"RIFF" + b"\x00" * 100  # Minimal WAV header

        with patch("mentor.api.routes.voice.get_voice_config") as mock_config:
            config = Mock()
            config.voice_sample_path = None
            mock_config.return_value = config

            with patch("pathlib.Path.mkdir"), patch("builtins.open", create=True):
                response = client.post(
                    "/api/voice/voice-sample",
                    files={"file": ("test.wav", io.BytesIO(audio_content), "audio/wav")},
                )

        assert response.status_code == 200
        data = response.json()
        assert "Voice sample uploaded" in data["message"]

    def test_upload_non_audio_file(self, client):
        """Test uploading non-audio file."""
        response = client.post(
            "/api/voice/voice-sample",
            files={"file": ("test.txt", io.BytesIO(b"text"), "text/plain")},
        )

        assert response.status_code == 400
        assert "must be an audio file" in response.json()["detail"]

    def test_upload_large_file(self, client):
        """Test uploading file that's too large."""
        # Create a file larger than 10MB
        large_content = b"0" * (11 * 1024 * 1024)

        response = client.post(
            "/api/voice/voice-sample",
            files={"file": ("large.wav", io.BytesIO(large_content), "audio/wav")},
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"]

    def test_delete_voice_sample(self, client, tmp_path):
        """Test deleting voice sample."""
        sample_path = tmp_path / "voice.wav"
        sample_path.touch()

        with patch("mentor.api.routes.voice.get_voice_config") as mock_config:
            config = Mock()
            config.voice_sample_path = sample_path
            mock_config.return_value = config

            response = client.delete("/api/voice/voice-sample")

        assert response.status_code == 200
        assert "deleted" in response.json()["message"]

    def test_delete_nonexistent_voice_sample(self, client):
        """Test deleting when no sample exists."""
        with patch("mentor.api.routes.voice.get_voice_config") as mock_config:
            config = Mock()
            config.voice_sample_path = None
            mock_config.return_value = config

            response = client.delete("/api/voice/voice-sample")

        assert response.status_code == 404


class TestTTSTestEndpoint:
    """Tests for /voice/test-tts endpoint."""

    def test_tts_success(self, client):
        """Test successful TTS synthesis."""
        with patch("mentor.api.routes.voice.get_tts_service") as mock_tts_factory:
            mock_tts = AsyncMock()
            mock_tts.synthesize.return_value = b"RIFF" + b"\x00" * 100
            mock_tts_factory.return_value = mock_tts

            response = client.post("/api/voice/test-tts?text=Hello%20world")

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/wav"

    def test_tts_empty_text(self, client):
        """Test TTS with empty text."""
        response = client.post("/api/voice/test-tts?text=")

        assert response.status_code == 422  # Validation error

    def test_tts_error(self, client):
        """Test TTS error handling."""
        with patch("mentor.api.routes.voice.get_tts_service") as mock_tts_factory:
            mock_tts = AsyncMock()
            mock_tts.synthesize.side_effect = Exception("TTS failed")
            mock_tts_factory.return_value = mock_tts

            response = client.post("/api/voice/test-tts?text=Hello")

        assert response.status_code == 500
        assert "TTS synthesis failed" in response.json()["detail"]


class TestSTTTestEndpoint:
    """Tests for /voice/test-stt endpoint."""

    def test_stt_success(self, client):
        """Test successful STT transcription."""
        # Create a minimal audio file
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(np.zeros(16000, dtype=np.int16).tobytes())
        buffer.seek(0)

        with patch("mentor.api.routes.voice.get_whisper_stt") as mock_stt_factory:
            mock_stt = Mock()
            mock_stt.transcribe.return_value = "Hello world"
            mock_stt_factory.return_value = mock_stt

            response = client.post(
                "/api/voice/test-stt",
                files={"file": ("audio.wav", buffer, "audio/wav")},
            )

        assert response.status_code == 200
        assert response.json()["transcription"] == "Hello world"

    def test_stt_with_timestamps(self, client):
        """Test STT with timestamps."""
        import wave

        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(np.zeros(16000, dtype=np.int16).tobytes())
        buffer.seek(0)

        with patch("mentor.api.routes.voice.get_whisper_stt") as mock_stt_factory:
            mock_stt = Mock()
            mock_stt.transcribe_with_timestamps.return_value = [
                {"word": "Hello", "start": 0.0, "end": 0.5, "probability": 0.9}
            ]
            mock_stt.get_speech_features.return_value = {"speech_rate_wpm": 140.0}
            mock_stt_factory.return_value = mock_stt

            response = client.post(
                "/api/voice/test-stt?with_timestamps=true",
                files={"file": ("audio.wav", buffer, "audio/wav")},
            )

        assert response.status_code == 200
        data = response.json()
        assert "words" in data
        assert "features" in data


class TestSessionEndpoints:
    """Tests for session management endpoints."""

    def test_list_sessions(self, client):
        """Test listing voice sessions."""
        with patch("mentor.api.routes.voice.get_session_manager") as mock_manager_factory:
            mock_manager = Mock()
            mock_manager.sessions = {}
            mock_manager_factory.return_value = mock_manager

            response = client.get("/api/voice/sessions")

        assert response.status_code == 200
        assert response.json()["total"] == 0

    def test_list_sessions_by_course(self, client):
        """Test listing sessions filtered by course."""
        with patch("mentor.api.routes.voice.get_session_manager") as mock_manager_factory:
            from mentor.voice.session import VoiceSession

            session = VoiceSession(
                session_id="s1",
                student_id="student",
                course_id="course-1",
            )

            mock_manager = Mock()
            mock_manager.get_course_sessions.return_value = [session]
            mock_manager_factory.return_value = mock_manager

            response = client.get("/api/voice/sessions?course_id=course-1")

        assert response.status_code == 200
        assert response.json()["total"] == 1

    def test_get_session(self, client):
        """Test getting specific session."""
        with patch("mentor.api.routes.voice.get_session_manager") as mock_manager_factory:
            from mentor.voice.session import VoiceInteraction, VoiceSession

            session = VoiceSession(
                session_id="test-session",
                student_id="student",
                course_id="course",
            )
            session.add_interaction(
                VoiceInteraction(
                    transcription="Test",
                    tutor_response_text="Response",
                )
            )

            mock_manager = Mock()
            mock_manager.get_session.return_value = session
            mock_manager_factory.return_value = mock_manager

            response = client.get("/api/voice/sessions/test-session")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert len(data["interactions"]) == 1

    def test_get_nonexistent_session(self, client):
        """Test getting nonexistent session."""
        with patch("mentor.api.routes.voice.get_session_manager") as mock_manager_factory:
            mock_manager = Mock()
            mock_manager.get_session.return_value = None
            mock_manager_factory.return_value = mock_manager

            response = client.get("/api/voice/sessions/nonexistent")

        assert response.status_code == 404

    def test_get_gaming_analysis(self, client):
        """Test getting gaming analysis for session."""
        with patch("mentor.api.routes.voice.get_session_manager") as mock_manager_factory:
            from mentor.voice.session import VoiceInteraction, VoiceSession

            session = VoiceSession(
                session_id="test",
                student_id="student",
                course_id="course",
            )
            session.add_interaction(
                VoiceInteraction(
                    gaming_confidence=0.7,
                    gaming_flags=["unnaturally_fast"],
                )
            )

            mock_manager = Mock()
            mock_manager.get_session.return_value = session
            mock_manager_factory.return_value = mock_manager

            response = client.get("/api/voice/sessions/test/gaming-analysis")

        assert response.status_code == 200
        data = response.json()
        assert "total_interactions" in data
        assert "flagged_interactions" in data

    def test_cleanup_stale_sessions(self, client):
        """Test cleaning up stale sessions."""
        with patch("mentor.api.routes.voice.get_session_manager") as mock_manager_factory:
            mock_manager = Mock()
            mock_manager.cleanup_stale_sessions.return_value = 5
            mock_manager.sessions = {}
            mock_manager_factory.return_value = mock_manager

            response = client.post("/api/voice/sessions/cleanup?max_idle_seconds=3600")

        assert response.status_code == 200
        assert response.json()["removed"] == 5


class TestHealthEndpoint:
    """Tests for /voice/health endpoint."""

    def test_health_all_services_available(self, client):
        """Test health check with all services available."""
        with (
            patch("mentor.api.routes.voice.get_whisper_stt") as mock_stt,
            patch("mentor.voice.stt.vad.get_vad") as mock_vad,
            patch("mentor.api.routes.voice.get_tts_service"),
            patch("mentor.api.routes.voice.get_voice_config") as mock_config,
        ):
            mock_stt.return_value = Mock(model=Mock())
            mock_vad.return_value = Mock(model=Mock())
            mock_config.return_value = Mock(
                sample_rate=16000,
                tts_engine="hybrid",
            )

            response = client.get("/api/voice/health")

        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert "services" in data

    def test_health_partial_services(self, client):
        """Test health check with some services unavailable."""
        with (
            patch("mentor.api.routes.voice.get_whisper_stt", side_effect=Exception),
            patch("mentor.api.routes.voice.get_tts_service", side_effect=Exception),
            patch("mentor.api.routes.voice.get_voice_config") as mock_config,
        ):
            mock_config.return_value = Mock(
                sample_rate=16000,
                tts_engine="hybrid",
            )

            response = client.get("/api/voice/health")

        assert response.status_code == 200
        data = response.json()
        assert data["healthy"] is False
