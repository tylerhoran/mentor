"""Pytest fixtures for voice layer tests."""

import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import numpy as np
import pytest

from mentor.voice.config import STTModel, TTSEngine, VoiceConfig
from mentor.voice.session import VoiceInteraction, VoiceSession, VoiceSessionState
from mentor.voice.stt.vad import SpeechState, VADResult


@pytest.fixture
def voice_config():
    """Create a test voice configuration."""
    return VoiceConfig(
        stt_model=STTModel.TINY,  # Use tiny for fast tests
        stt_device="cpu",
        stt_compute_type="float32",
        tts_engine=TTSEngine.PIPER,
        sample_rate=16000,
        vad_threshold=0.5,
        min_speech_duration_ms=250,
        min_silence_duration_ms=500,
        max_speech_duration_s=10.0,
    )


@pytest.fixture
def sample_audio():
    """Generate sample audio data (1 second of sine wave)."""
    sample_rate = 16000
    duration = 1.0
    frequency = 440  # A4 note
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    audio = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
    return audio


@pytest.fixture
def silence_audio():
    """Generate 1 second of silence."""
    return np.zeros(16000, dtype=np.float32)


@pytest.fixture
def speech_like_audio():
    """Generate audio that simulates speech patterns."""
    sample_rate = 16000
    duration = 2.0
    samples = int(sample_rate * duration)

    # Create varying amplitude to simulate speech
    t = np.linspace(0, duration, samples, dtype=np.float32)
    envelope = 0.3 + 0.2 * np.sin(2 * np.pi * 3 * t)  # Varying amplitude
    carrier = np.sin(2 * np.pi * 200 * t)  # Base frequency
    audio = (envelope * carrier).astype(np.float32)

    return audio


@pytest.fixture
def voice_session():
    """Create a test voice session."""
    return VoiceSession(
        session_id="test-session-123",
        student_id="student-456",
        course_id="course-789",
    )


@pytest.fixture
def voice_interaction():
    """Create a test voice interaction."""
    return VoiceInteraction(
        audio_duration_ms=5000,
        transcription="This is a test transcription of spoken words.",
        response_latency_ms=1500,
        speech_rate_wpm=150.0,
        pause_count=2,
        average_pause_duration_ms=300.0,
        tutor_response_text="That's an interesting point. Can you elaborate?",
        tutor_response_audio_duration_ms=3000,
        tts_engine_used="HybridTTS",
    )


@pytest.fixture
def populated_session(voice_session, voice_interaction):
    """Create a session with multiple interactions."""
    for i in range(5):
        interaction = VoiceInteraction(
            audio_duration_ms=3000 + i * 500,
            transcription=f"Test message {i}",
            response_latency_ms=1000 + i * 200,
            speech_rate_wpm=140.0 + i * 5,
            pause_count=i,
            tutor_response_text=f"Response {i}",
            tutor_response_audio_duration_ms=2000 + i * 300,
        )
        voice_session.add_interaction(interaction)
    return voice_session


@pytest.fixture
def mock_whisper_model():
    """Create a mock Whisper model."""
    mock = Mock()

    # Mock segment with words
    mock_word = Mock()
    mock_word.word = "test"
    mock_word.start = 0.0
    mock_word.end = 0.5
    mock_word.probability = 0.95

    mock_segment = Mock()
    mock_segment.text = "This is a test transcription"
    mock_segment.words = [mock_word]

    mock.transcribe.return_value = ([mock_segment], Mock(language="en"))

    return mock


@pytest.fixture
def mock_vad_model():
    """Create a mock VAD model."""
    mock = Mock()
    mock.return_value = Mock(item=Mock(return_value=0.8))  # High speech probability
    mock.reset_states = Mock()
    return mock


@pytest.fixture
def mock_tts_audio():
    """Generate mock TTS audio output (WAV format header + samples)."""
    import io
    import wave

    sample_rate = 22050
    duration = 1.0
    samples = int(sample_rate * duration)

    # Generate audio samples
    t = np.linspace(0, duration, samples, dtype=np.float32)
    audio = (0.5 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)

    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(audio.tobytes())

    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.send_bytes = AsyncMock()
    ws.receive = AsyncMock()
    ws.close = AsyncMock()
    return ws


@pytest.fixture
def mock_dialogue_callback():
    """Create a mock dialogue callback function."""

    async def callback(message: str, session_id: str) -> str:
        return f"Response to: {message}"

    return callback


@pytest.fixture
def gaming_suspicious_interaction():
    """Create an interaction with gaming-like patterns."""
    return VoiceInteraction(
        audio_duration_ms=8000,
        transcription="This is a very long and detailed response that was given extremely quickly without any pauses or hesitation which is quite unnatural for spontaneous speech patterns in educational contexts",
        response_latency_ms=300,  # Suspiciously fast
        speech_rate_wpm=200.0,  # Above natural threshold
        pause_count=0,  # No pauses
        average_pause_duration_ms=0.0,
        tutor_response_text="Interesting.",
        tutor_response_audio_duration_ms=1000,
    )


@pytest.fixture
def gaming_normal_interaction():
    """Create an interaction with normal patterns."""
    return VoiceInteraction(
        audio_duration_ms=4000,
        transcription="I think the answer might be related to the concept we discussed earlier.",
        response_latency_ms=2000,  # Normal thinking time
        speech_rate_wpm=145.0,  # Normal rate
        pause_count=3,  # Natural pauses
        average_pause_duration_ms=400.0,
        tutor_response_text="Good thinking! Can you explain why?",
        tutor_response_audio_duration_ms=2500,
    )


# Note: event_loop fixture is no longer needed with pytest-asyncio 0.23+
# pytest-asyncio now handles event loop creation automatically
