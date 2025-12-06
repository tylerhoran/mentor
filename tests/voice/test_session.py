"""Tests for voice session management."""

from datetime import datetime, timedelta

from mentor.voice.session import (
    VoiceInteraction,
    VoiceSessionManager,
    VoiceSessionState,
    get_session_manager,
)


class TestVoiceInteraction:
    """Tests for VoiceInteraction dataclass."""

    def test_default_values(self):
        """Test default interaction values."""
        interaction = VoiceInteraction()

        assert interaction.id is not None
        assert interaction.timestamp is not None
        assert interaction.audio_duration_ms == 0
        assert interaction.transcription == ""
        assert interaction.gaming_flags == []
        assert interaction.gaming_confidence == 0.0

    def test_custom_values(self, voice_interaction):
        """Test interaction with custom values."""
        assert voice_interaction.audio_duration_ms == 5000
        assert voice_interaction.transcription == "This is a test transcription of spoken words."
        assert voice_interaction.response_latency_ms == 1500
        assert voice_interaction.speech_rate_wpm == 150.0
        assert voice_interaction.pause_count == 2

    def test_gaming_fields(self):
        """Test gaming detection fields."""
        interaction = VoiceInteraction(
            gaming_flags=["unnaturally_fast", "no_hesitation"],
            gaming_confidence=0.75,
        )

        assert len(interaction.gaming_flags) == 2
        assert interaction.gaming_confidence == 0.75


class TestVoiceSessionState:
    """Tests for VoiceSessionState enum."""

    def test_all_states(self):
        """Test all session states."""
        assert VoiceSessionState.IDLE.value == "idle"
        assert VoiceSessionState.LISTENING.value == "listening"
        assert VoiceSessionState.PROCESSING.value == "processing"
        assert VoiceSessionState.SPEAKING.value == "speaking"
        assert VoiceSessionState.ERROR.value == "error"


class TestVoiceSession:
    """Tests for VoiceSession dataclass."""

    def test_creation(self, voice_session):
        """Test session creation."""
        assert voice_session.session_id == "test-session-123"
        assert voice_session.student_id == "student-456"
        assert voice_session.course_id == "course-789"
        assert voice_session.state == VoiceSessionState.IDLE
        assert voice_session.total_interactions == 0

    def test_add_interaction(self, voice_session, voice_interaction):
        """Test adding interaction to session."""
        initial_time = voice_session.last_activity

        voice_session.add_interaction(voice_interaction)

        assert voice_session.total_interactions == 1
        assert voice_session.total_student_speech_ms == 5000
        assert voice_session.total_tutor_speech_ms == 3000
        assert len(voice_session.interactions) == 1
        assert voice_session.last_activity >= initial_time

    def test_get_average_response_latency_empty(self, voice_session):
        """Test average latency with no interactions."""
        assert voice_session.get_average_response_latency() == 0.0

    def test_get_average_response_latency(self, populated_session):
        """Test average response latency calculation."""
        avg_latency = populated_session.get_average_response_latency()

        # Latencies: 1000, 1200, 1400, 1600, 1800
        expected = (1000 + 1200 + 1400 + 1600 + 1800) / 5
        assert avg_latency == expected

    def test_get_speech_balance_no_tutor_speech(self, voice_session):
        """Test speech balance with no tutor speech."""
        interaction = VoiceInteraction(
            audio_duration_ms=5000,
            tutor_response_audio_duration_ms=0,
        )
        voice_session.add_interaction(interaction)
        assert voice_session.get_speech_balance() == float("inf")

    def test_get_speech_balance(self, populated_session):
        """Test speech balance calculation."""
        balance = populated_session.get_speech_balance()

        # Should be student_speech / tutor_speech
        expected = (
            populated_session.total_student_speech_ms / populated_session.total_tutor_speech_ms
        )
        assert balance == expected

    def test_get_recent_interactions(self, populated_session):
        """Test getting recent interactions."""
        recent = populated_session.get_recent_interactions(3)

        assert len(recent) == 3
        assert recent[-1] == populated_session.interactions[-1]

    def test_get_recent_interactions_more_than_available(self, voice_session, voice_interaction):
        """Test getting more interactions than available."""
        voice_session.add_interaction(voice_interaction)

        recent = voice_session.get_recent_interactions(10)

        assert len(recent) == 1

    def test_get_average_speech_rate_empty(self, voice_session):
        """Test average speech rate with no interactions."""
        assert voice_session.get_average_speech_rate() is None

    def test_get_average_speech_rate(self, populated_session):
        """Test average speech rate calculation."""
        avg_rate = populated_session.get_average_speech_rate()

        # Rates: 140, 145, 150, 155, 160
        expected = (140 + 145 + 150 + 155 + 160) / 5
        assert avg_rate == expected

    def test_to_dict(self, voice_session, voice_interaction):
        """Test session serialization."""
        voice_session.add_interaction(voice_interaction)

        data = voice_session.to_dict()

        assert data["session_id"] == "test-session-123"
        assert data["student_id"] == "student-456"
        assert data["course_id"] == "course-789"
        assert data["state"] == "idle"
        assert data["total_interactions"] == 1
        assert "created_at" in data
        assert "last_activity" in data

    def test_state_transitions(self, voice_session):
        """Test session state transitions."""
        assert voice_session.state == VoiceSessionState.IDLE

        voice_session.state = VoiceSessionState.LISTENING
        assert voice_session.state == VoiceSessionState.LISTENING

        voice_session.state = VoiceSessionState.PROCESSING
        assert voice_session.state == VoiceSessionState.PROCESSING

        voice_session.state = VoiceSessionState.SPEAKING
        assert voice_session.state == VoiceSessionState.SPEAKING

        voice_session.state = VoiceSessionState.IDLE
        assert voice_session.state == VoiceSessionState.IDLE


class TestVoiceSessionManager:
    """Tests for VoiceSessionManager."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = VoiceSessionManager()

        session = manager.create_session(
            student_id="student-1",
            course_id="course-1",
        )

        assert session.student_id == "student-1"
        assert session.course_id == "course-1"
        assert session.session_id is not None
        assert session.session_id in manager.sessions

    def test_create_session_with_id(self):
        """Test creating session with specific ID."""
        manager = VoiceSessionManager()

        session = manager.create_session(
            student_id="student-1",
            course_id="course-1",
            session_id="custom-session-id",
        )

        assert session.session_id == "custom-session-id"

    def test_get_session(self):
        """Test getting a session by ID."""
        manager = VoiceSessionManager()
        created = manager.create_session("student", "course", "session-1")

        retrieved = manager.get_session("session-1")

        assert retrieved is created

    def test_get_nonexistent_session(self):
        """Test getting nonexistent session."""
        manager = VoiceSessionManager()

        assert manager.get_session("nonexistent") is None

    def test_remove_session(self):
        """Test removing a session."""
        manager = VoiceSessionManager()
        session = manager.create_session("student", "course", "session-1")

        removed = manager.remove_session("session-1")

        assert removed is session
        assert manager.get_session("session-1") is None

    def test_remove_nonexistent_session(self):
        """Test removing nonexistent session."""
        manager = VoiceSessionManager()

        assert manager.remove_session("nonexistent") is None

    def test_get_student_sessions(self):
        """Test getting sessions by student."""
        manager = VoiceSessionManager()
        manager.create_session("student-1", "course-a", "s1")
        manager.create_session("student-1", "course-b", "s2")
        manager.create_session("student-2", "course-a", "s3")

        sessions = manager.get_student_sessions("student-1")

        assert len(sessions) == 2
        assert all(s.student_id == "student-1" for s in sessions)

    def test_get_course_sessions(self):
        """Test getting sessions by course."""
        manager = VoiceSessionManager()
        manager.create_session("student-1", "course-a", "s1")
        manager.create_session("student-2", "course-a", "s2")
        manager.create_session("student-1", "course-b", "s3")

        sessions = manager.get_course_sessions("course-a")

        assert len(sessions) == 2
        assert all(s.course_id == "course-a" for s in sessions)

    def test_cleanup_stale_sessions(self):
        """Test cleaning up stale sessions."""
        manager = VoiceSessionManager()

        # Create sessions
        manager.create_session("student-1", "course", "active")
        stale = manager.create_session("student-2", "course", "stale")

        # Make one stale
        stale.last_activity = datetime.utcnow() - timedelta(hours=2)

        removed = manager.cleanup_stale_sessions(max_idle_seconds=3600)

        assert removed == 1
        assert manager.get_session("active") is not None
        assert manager.get_session("stale") is None


class TestGetSessionManager:
    """Tests for get_session_manager singleton."""

    def test_singleton(self):
        """Test session manager singleton."""
        import mentor.voice.session as session_module

        session_module._session_manager = None

        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2
