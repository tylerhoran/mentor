"""WebSocket handler for voice tutoring sessions."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Awaitable, Callable, Optional

import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from .config import get_voice_config
from .gaming_detection import VoiceGamingDetector
from .session import VoiceInteraction, VoiceSession, VoiceSessionState, get_session_manager
from .stt.vad import SileroVAD, SpeechState, get_vad
from .stt.whisper_service import WhisperSTT, get_whisper_stt
from .tts.base import TTSService
from .tts.hybrid import get_tts_service

logger = logging.getLogger(__name__)

# Type for dialogue callback
DialogueCallback = Callable[[str, str], Awaitable[str]]


class VoiceWebSocketHandler:
    """Handle voice WebSocket connections for tutoring sessions."""

    def __init__(self):
        self.config = get_voice_config()
        self.stt: Optional[WhisperSTT] = None
        self.vad: Optional[SileroVAD] = None
        self.tts: Optional[TTSService] = None
        self.gaming_detector = VoiceGamingDetector()
        self.session_manager = get_session_manager()
        self._initialized = False

    async def initialize(self):
        """Initialize voice services (lazy loading)."""
        if self._initialized:
            return

        try:
            self.stt = get_whisper_stt()
        except Exception as e:
            logger.warning(f"STT initialization failed: {e}")

        try:
            self.vad = get_vad()
        except Exception as e:
            logger.warning(f"VAD initialization failed: {e}")

        try:
            self.tts = get_tts_service()
            await self.tts.warmup()
        except Exception as e:
            logger.warning(f"TTS initialization failed: {e}")

        self._initialized = True

    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: str,
        student_id: str,
        course_id: str,
        get_tutor_response: DialogueCallback,
    ):
        """
        Main WebSocket handler for voice tutoring.

        Protocol:
        - Client sends binary audio chunks (16kHz, mono, float32)
        - Client sends JSON control messages
        - Server sends JSON status messages
        - Server sends binary audio responses

        Args:
            websocket: The WebSocket connection
            session_id: Unique session identifier
            student_id: Student identifier
            course_id: Course identifier
            get_tutor_response: Async callback to get tutor response text
        """
        await websocket.accept()
        await self.initialize()

        # Create or get session
        session = self.session_manager.get_session(session_id)
        if session is None:
            session = self.session_manager.create_session(
                student_id=student_id, course_id=course_id, session_id=session_id
            )

        # Send ready message
        await self._send_status(
            websocket,
            "ready",
            {
                "session_id": session_id,
                "sample_rate": self.config.sample_rate,
                "stt_available": self.stt is not None,
                "tts_available": self.tts is not None,
            },
        )

        try:
            while True:
                message = await websocket.receive()

                if "bytes" in message:
                    # Audio data
                    await self._handle_audio(
                        websocket, message["bytes"], session, get_tutor_response
                    )
                elif "text" in message:
                    # Control message
                    await self._handle_control(websocket, message["text"], session)

        except WebSocketDisconnect:
            logger.info(f"Voice session {session_id} disconnected")
        except Exception as e:
            logger.error(f"Voice session error: {e}", exc_info=True)
            await self._send_status(websocket, "error", {"message": str(e)})
        finally:
            # Update session state
            session.state = VoiceSessionState.IDLE

    async def _handle_audio(
        self,
        websocket: WebSocket,
        audio_bytes: bytes,
        session: VoiceSession,
        get_tutor_response: DialogueCallback,
    ):
        """Process incoming audio chunk."""
        if self.vad is None or self.stt is None:
            await self._send_status(websocket, "error", {"message": "Voice services not available"})
            return

        # Convert bytes to numpy array
        audio_chunk = np.frombuffer(audio_bytes, dtype=np.float32)

        # Process through VAD
        vad_result = self.vad.process_chunk(audio_chunk)

        if vad_result.state == SpeechState.SPEAKING:
            session.state = VoiceSessionState.LISTENING
            await self._send_status(
                websocket,
                "listening",
                {
                    "duration_ms": vad_result.duration_ms,
                    "speech_probability": round(vad_result.speech_probability, 2),
                },
            )

        elif vad_result.state == SpeechState.FINISHED:
            await self._process_utterance(websocket, vad_result.audio, session, get_tutor_response)

    async def _process_utterance(
        self,
        websocket: WebSocket,
        audio: np.ndarray,
        session: VoiceSession,
        get_tutor_response: DialogueCallback,
    ):
        """Process a complete utterance."""
        session.state = VoiceSessionState.PROCESSING
        await self._send_status(websocket, "processing")

        # Record timing
        speech_end_time = datetime.utcnow()
        audio_duration_ms = len(audio) * 1000 // self.config.sample_rate

        # Transcribe with timestamps for feature extraction
        try:
            words = self.stt.transcribe_with_timestamps(audio)
            transcription = " ".join(w["word"].strip() for w in words)
            speech_features = self.stt.get_speech_features(audio, words)
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            transcription = self.stt.transcribe(audio)
            speech_features = {}

        if not transcription.strip():
            session.state = VoiceSessionState.IDLE
            await self._send_status(websocket, "idle")
            self.vad.reset()
            return

        # Send transcription
        await self._send_status(websocket, "transcription", {"text": transcription})

        # Get tutor response
        try:
            response_text = await get_tutor_response(transcription, session.session_id)
        except Exception as e:
            logger.error(f"Tutor response error: {e}")
            response_text = "I'm sorry, I had trouble processing that. Could you try again?"

        # Record response timing
        response_start_time = datetime.utcnow()
        response_latency_ms = int((response_start_time - speech_end_time).total_seconds() * 1000)

        # Create interaction record
        interaction = VoiceInteraction(
            audio_duration_ms=audio_duration_ms,
            transcription=transcription,
            response_latency_ms=response_latency_ms,
            tutor_response_text=response_text,
            speech_rate_wpm=speech_features.get("speech_rate_wpm"),
            pause_count=speech_features.get("pause_count", 0),
            average_pause_duration_ms=speech_features.get("average_pause_duration_ms", 0),
        )

        # Analyze for gaming
        gaming_analysis = self.gaming_detector.analyze_interaction(interaction, session)

        interaction.gaming_confidence = gaming_analysis.confidence
        interaction.gaming_flags = [f.signal_type.value for f in gaming_analysis.flags]

        if gaming_analysis.confidence > 0.7:
            logger.warning(
                f"High gaming confidence ({gaming_analysis.confidence:.2f}) "
                f"in session {session.session_id}: {interaction.gaming_flags}"
            )

        # Send text response
        await self._send_status(
            websocket,
            "response",
            {
                "text": response_text,
                "gaming_confidence": round(gaming_analysis.confidence, 2)
                if gaming_analysis.has_flags
                else None,
            },
        )

        # Synthesize speech if TTS available
        if self.tts is not None:
            session.state = VoiceSessionState.SPEAKING
            await self._send_status(websocket, "speaking")

            try:
                audio_response = await self.tts.synthesize(response_text)

                # Send audio
                await websocket.send_bytes(audio_response)

                # Estimate audio duration (rough: assume 16-bit mono)
                audio_samples = len(audio_response) // 2
                interaction.tutor_response_audio_duration_ms = (
                    audio_samples * 1000 // self.tts.sample_rate
                )
                interaction.tts_engine_used = type(self.tts).__name__

            except Exception as e:
                logger.error(f"TTS error: {e}")
                await self._send_status(
                    websocket, "tts_error", {"message": "Speech synthesis failed"}
                )

        # Store interaction
        session.add_interaction(interaction)

        session.state = VoiceSessionState.IDLE
        await self._send_status(websocket, "idle", {"interaction_id": interaction.id})

        # Reset VAD for next utterance
        self.vad.reset()

    async def _handle_control(self, websocket: WebSocket, message: str, session: VoiceSession):
        """Handle control messages from client."""
        try:
            data = json.loads(message)
            command = data.get("command")

            if command == "reset":
                if self.vad:
                    self.vad.reset()
                session.state = VoiceSessionState.IDLE
                await self._send_status(websocket, "reset")

            elif command == "ping":
                await self._send_status(
                    websocket, "pong", {"timestamp": datetime.utcnow().isoformat()}
                )

            elif command == "get_metrics":
                await self._send_status(
                    websocket,
                    "metrics",
                    {
                        "total_interactions": session.total_interactions,
                        "total_student_speech_ms": session.total_student_speech_ms,
                        "total_tutor_speech_ms": session.total_tutor_speech_ms,
                        "average_latency_ms": round(session.get_average_response_latency(), 1),
                        "speech_balance": round(session.get_speech_balance(), 2)
                        if session.total_tutor_speech_ms > 0
                        else None,
                    },
                )

            elif command == "get_session":
                await self._send_status(websocket, "session", session.to_dict())

            elif command == "end":
                await self._send_status(websocket, "ended", session.to_dict())
                await websocket.close()

            else:
                await self._send_status(websocket, "unknown_command", {"command": command})

        except json.JSONDecodeError:
            logger.error(f"Invalid control message: {message}")
            await self._send_status(websocket, "error", {"message": "Invalid JSON"})

    async def _send_status(self, websocket: WebSocket, status: str, data: Optional[dict] = None):
        """Send a JSON status message to the client."""
        message = {"status": status}
        if data:
            message["data"] = data
        await websocket.send_json(message)


# Singleton handler
_voice_handler: Optional[VoiceWebSocketHandler] = None


def get_voice_handler() -> VoiceWebSocketHandler:
    """Get or create the voice WebSocket handler."""
    global _voice_handler
    if _voice_handler is None:
        _voice_handler = VoiceWebSocketHandler()
    return _voice_handler
