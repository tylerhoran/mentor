"""Voice session management."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

import numpy as np


class VoiceSessionState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class VoiceInteraction:
    """Single voice interaction record."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Input
    audio_duration_ms: int = 0
    transcription: str = ""
    transcription_confidence: float = 0.0
    response_latency_ms: int = 0  # Time from end of speech to start of response

    # Prosodic features (for gaming detection)
    speech_rate_wpm: Optional[float] = None
    pause_count: int = 0
    average_pause_duration_ms: float = 0.0
    pitch_variation: Optional[float] = None

    # Output
    tutor_response_text: str = ""
    tutor_response_audio_duration_ms: int = 0
    tts_engine_used: str = ""

    # Gaming analysis
    gaming_flags: List[str] = field(default_factory=list)
    gaming_confidence: float = 0.0


@dataclass
class VoiceSession:
    """Voice tutoring session state."""

    session_id: str
    student_id: str
    course_id: str

    state: VoiceSessionState = VoiceSessionState.IDLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    interactions: List[VoiceInteraction] = field(default_factory=list)

    # Session metrics
    total_student_speech_ms: int = 0
    total_tutor_speech_ms: int = 0
    total_interactions: int = 0

    # Current audio buffer (not persisted)
    audio_buffer: Optional[np.ndarray] = field(default=None, repr=False)

    def add_interaction(self, interaction: VoiceInteraction):
        """Add an interaction and update metrics."""
        self.interactions.append(interaction)
        self.total_interactions += 1
        self.total_student_speech_ms += interaction.audio_duration_ms
        self.total_tutor_speech_ms += interaction.tutor_response_audio_duration_ms
        self.last_activity = datetime.utcnow()

    def get_average_response_latency(self) -> float:
        """Average time from student speech end to tutor response start."""
        if not self.interactions:
            return 0.0
        latencies = [i.response_latency_ms for i in self.interactions if i.response_latency_ms > 0]
        return sum(latencies) / len(latencies) if latencies else 0.0

    def get_speech_balance(self) -> float:
        """Ratio of student to tutor speech time."""
        if self.total_tutor_speech_ms == 0:
            return float("inf")
        return self.total_student_speech_ms / self.total_tutor_speech_ms

    def get_recent_interactions(self, count: int = 10) -> List[VoiceInteraction]:
        """Get the most recent interactions."""
        return self.interactions[-count:] if self.interactions else []

    def get_average_speech_rate(self) -> Optional[float]:
        """Get average speech rate across interactions."""
        rates = [i.speech_rate_wpm for i in self.interactions if i.speech_rate_wpm]
        return sum(rates) / len(rates) if rates else None

    def to_dict(self) -> dict:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "total_interactions": self.total_interactions,
            "total_student_speech_ms": self.total_student_speech_ms,
            "total_tutor_speech_ms": self.total_tutor_speech_ms,
            "average_response_latency_ms": self.get_average_response_latency(),
            "speech_balance": self.get_speech_balance() if self.total_tutor_speech_ms > 0 else None,
        }


class VoiceSessionManager:
    """Manage active voice sessions."""

    def __init__(self):
        self.sessions: dict[str, VoiceSession] = {}

    def create_session(
        self, student_id: str, course_id: str, session_id: Optional[str] = None
    ) -> VoiceSession:
        """Create a new voice session."""
        session_id = session_id or str(uuid.uuid4())
        session = VoiceSession(session_id=session_id, student_id=student_id, course_id=course_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)

    def remove_session(self, session_id: str) -> Optional[VoiceSession]:
        """Remove and return a session."""
        return self.sessions.pop(session_id, None)

    def get_student_sessions(self, student_id: str) -> List[VoiceSession]:
        """Get all sessions for a student."""
        return [s for s in self.sessions.values() if s.student_id == student_id]

    def get_course_sessions(self, course_id: str) -> List[VoiceSession]:
        """Get all sessions for a course."""
        return [s for s in self.sessions.values() if s.course_id == course_id]

    def cleanup_stale_sessions(self, max_idle_seconds: int = 3600) -> int:
        """Remove sessions that have been idle too long."""
        now = datetime.utcnow()
        stale_ids = []

        for session_id, session in self.sessions.items():
            idle_time = (now - session.last_activity).total_seconds()
            if idle_time > max_idle_seconds:
                stale_ids.append(session_id)

        for session_id in stale_ids:
            del self.sessions[session_id]

        return len(stale_ids)


# Global session manager
_session_manager: Optional[VoiceSessionManager] = None


def get_session_manager() -> VoiceSessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = VoiceSessionManager()
    return _session_manager
