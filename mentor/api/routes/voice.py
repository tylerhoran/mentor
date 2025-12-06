"""Voice API routes for Mentor."""

import io
import logging
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket
from fastapi.responses import Response

from ...models.user import User
from ...voice.config import VoiceConfig, get_voice_config
from ...voice.gaming_detection import VoiceGamingDetector
from ...voice.session import get_session_manager
from ...voice.stt.whisper_service import get_whisper_stt
from ...voice.tts.hybrid import get_tts_service
from ...voice.websocket import get_voice_handler
from ..deps import get_current_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


async def get_tutor_response_stub(message: str, session_id: str) -> str:
    """
    Stub for tutor response - should be replaced with actual dialogue manager.

    In production, this would call the dialogue manager from tutor_runtime.
    """
    # Import here to avoid circular imports
    try:
        from ...core.tutor_runtime.dialogue_manager import DialogueManager
        # Would need to get the actual dialogue manager instance
        # For now, return a placeholder
    except ImportError:
        pass

    # Placeholder response for testing
    if "?" in message:
        return "That's an interesting question. Let me think about that with you. What aspects of this topic are you most curious about?"
    else:
        return "I see. Can you tell me more about your thinking here? What led you to that understanding?"


@router.websocket("/session/{course_id}")
async def voice_session(
    websocket: WebSocket,
    course_id: str,
    session_id: Optional[str] = Query(None),
):
    """
    WebSocket endpoint for voice tutoring sessions.

    Client protocol:
    1. Connect to this endpoint
    2. Wait for {"status": "ready"} message
    3. Send audio as binary frames (16kHz, mono, float32)
    4. Handle status messages and audio responses

    Control messages (JSON):
    - {"command": "reset"} - Reset VAD state
    - {"command": "ping"} - Check connection
    - {"command": "get_metrics"} - Get session metrics
    - {"command": "get_session"} - Get full session info
    - {"command": "end"} - End session

    Status messages from server:
    - ready: Connection established
    - listening: Receiving speech
    - processing: Transcribing audio
    - transcription: Speech transcribed (data.text)
    - response: Tutor response text (data.text)
    - speaking: Synthesizing speech
    - idle: Ready for next input
    - error: Error occurred (data.message)
    """
    voice_handler = get_voice_handler()

    # Generate IDs if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    if not student_id:
        student_id = "anonymous"

    # TODO: In production, validate student enrollment in course
    # and authenticate via token

    await voice_handler.handle_connection(
        websocket=websocket,
        session_id=session_id,
        student_id=student_id,
        course_id=course_id,
        get_tutor_response=get_tutor_response_stub,
    )


@router.get("/config")
async def get_voice_configuration():
    """Get current voice configuration."""
    config = get_voice_config()
    return {
        "stt_model": config.stt_model,
        "stt_device": config.stt_device,
        "tts_engine": config.tts_engine,
        "sample_rate": config.sample_rate,
        "has_voice_clone": config.voice_sample_path is not None
        and config.voice_sample_path.exists(),
        "vad_threshold": config.vad_threshold,
        "min_silence_duration_ms": config.min_silence_duration_ms,
    }


@router.post("/voice-sample")
async def upload_voice_sample(
    file: UploadFile = File(...),
    # current_user: User = Depends(get_current_user)  # Uncomment in production
):
    """
    Upload a voice sample for voice cloning (faculty only).

    Requirements:
    - Audio file (WAV, MP3, etc.)
    - 5-30 seconds of clear speech
    - Single speaker
    """
    # Validate file type
    content_type = file.content_type or ""
    if not content_type.startswith("audio/"):
        raise HTTPException(400, "File must be an audio file")

    # Check file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 10MB)")

    # Save file
    voice_samples_dir = Path("data/voice_samples")
    voice_samples_dir.mkdir(parents=True, exist_ok=True)

    # Use a unique filename
    sample_path = voice_samples_dir / f"voice_sample_{uuid.uuid4().hex[:8]}.wav"

    # Convert to WAV if needed (would need ffmpeg)
    # For now, assume WAV input
    with open(sample_path, "wb") as f:
        f.write(file_content)

    # Update config
    config = get_voice_config()
    config.voice_sample_path = sample_path

    return {
        "message": "Voice sample uploaded successfully",
        "path": str(sample_path),
        "size_bytes": len(file_content),
    }


@router.delete("/voice-sample")
async def delete_voice_sample(
    # current_user: User = Depends(get_current_user)  # Uncomment in production
):
    """Delete the current voice sample."""
    config = get_voice_config()

    if config.voice_sample_path and config.voice_sample_path.exists():
        config.voice_sample_path.unlink()
        config.voice_sample_path = None
        return {"message": "Voice sample deleted"}

    raise HTTPException(404, "No voice sample found")


@router.post("/test-tts")
async def test_tts(
    text: str = Query(..., min_length=1, max_length=1000),
    engine: Optional[str] = Query(None, description="Force specific engine: piper or xtts"),
):
    """
    Test TTS with given text.

    Returns audio file (WAV format).
    """
    try:
        tts = get_tts_service()
        audio = await tts.synthesize(text)

        return Response(
            content=audio,
            media_type="audio/wav",
            headers={
                "Content-Disposition": "attachment; filename=tts_output.wav",
                "X-TTS-Engine": type(tts).__name__,
            },
        )
    except Exception as e:
        logger.error(f"TTS test failed: {e}")
        raise HTTPException(500, f"TTS synthesis failed: {str(e)}")


@router.post("/test-stt")
async def test_stt(
    file: UploadFile = File(...),
    with_timestamps: bool = Query(False, description="Include word timestamps"),
):
    """
    Test STT with given audio file.

    Returns transcription and optionally word timestamps.
    """
    try:
        import numpy as np
        import soundfile as sf

        # Read audio file
        audio_bytes = await file.read()
        audio_data, sample_rate = sf.read(io.BytesIO(audio_bytes))

        # Convert to mono if stereo
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)

        # Resample to 16kHz if needed
        if sample_rate != 16000:
            import librosa

            audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=16000)

        audio_data = audio_data.astype(np.float32)

        stt = get_whisper_stt()

        if with_timestamps:
            words = stt.transcribe_with_timestamps(audio_data)
            transcription = " ".join(w["word"].strip() for w in words)
            features = stt.get_speech_features(audio_data, words)

            return {"transcription": transcription, "words": words, "features": features}
        else:
            transcription = stt.transcribe(audio_data)
            return {"transcription": transcription}

    except ImportError as e:
        raise HTTPException(500, f"Missing dependency: {str(e)}")
    except Exception as e:
        logger.error(f"STT test failed: {e}")
        raise HTTPException(500, f"STT transcription failed: {str(e)}")


@router.get("/sessions")
async def list_voice_sessions(
    course_id: Optional[str] = None,
    student_id: Optional[str] = None,
    # current_user: User = Depends(get_current_user)  # Uncomment in production
):
    """List active voice sessions."""
    manager = get_session_manager()

    if course_id:
        sessions = manager.get_course_sessions(course_id)
    elif student_id:
        sessions = manager.get_student_sessions(student_id)
    else:
        sessions = list(manager.sessions.values())

    return {"sessions": [s.to_dict() for s in sessions], "total": len(sessions)}


@router.get("/sessions/{session_id}")
async def get_voice_session(
    session_id: str,
    # current_user: User = Depends(get_current_user)  # Uncomment in production
):
    """Get details of a specific voice session."""
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(404, "Session not found")

    return {
        **session.to_dict(),
        "interactions": [
            {
                "id": i.id,
                "timestamp": i.timestamp.isoformat(),
                "transcription": i.transcription,
                "response": i.tutor_response_text,
                "audio_duration_ms": i.audio_duration_ms,
                "response_latency_ms": i.response_latency_ms,
                "gaming_confidence": i.gaming_confidence,
                "gaming_flags": i.gaming_flags,
            }
            for i in session.interactions
        ],
    }


@router.get("/sessions/{session_id}/gaming-analysis")
async def get_session_gaming_analysis(
    session_id: str,
    # current_user: User = Depends(get_current_user)  # Uncomment in production
):
    """Get gaming detection analysis for a voice session."""
    manager = get_session_manager()
    session = manager.get_session(session_id)

    if session is None:
        raise HTTPException(404, "Session not found")

    detector = VoiceGamingDetector()
    analysis = detector.get_session_analysis(session)

    return analysis


@router.post("/sessions/cleanup")
async def cleanup_stale_sessions(
    max_idle_seconds: int = Query(3600, ge=60, le=86400),
    # current_user: User = Depends(get_current_user)  # Uncomment in production
):
    """Clean up stale voice sessions."""
    manager = get_session_manager()
    removed = manager.cleanup_stale_sessions(max_idle_seconds)

    return {"removed": removed, "remaining": len(manager.sessions)}


@router.get("/health")
async def voice_health_check():
    """Check voice service health."""
    status = {
        "stt": False,
        "vad": False,
        "tts": False,
    }

    try:
        stt = get_whisper_stt()
        status["stt"] = stt.model is not None
    except Exception:
        pass

    try:
        from ...voice.stt.vad import get_vad

        vad = get_vad()
        status["vad"] = vad.model is not None
    except Exception:
        pass

    try:
        tts = get_tts_service()
        status["tts"] = True
    except Exception:
        pass

    all_healthy = all(status.values())

    return {
        "healthy": all_healthy,
        "services": status,
        "config": {
            "sample_rate": get_voice_config().sample_rate,
            "tts_engine": get_voice_config().tts_engine,
        },
    }
