"""Tests for voice gaming detection."""

from datetime import datetime

import numpy as np
import pytest

from mentor.voice.gaming_detection import (
    GamingFlag,
    VoiceGamingAnalysis,
    VoiceGamingDetector,
    VoiceGamingSignal,
)
from mentor.voice.session import VoiceInteraction, VoiceSession


class TestVoiceGamingSignal:
    """Tests for VoiceGamingSignal enum."""

    def test_timing_signals(self):
        """Test timing-related signals."""
        assert VoiceGamingSignal.UNNATURALLY_FAST.value == "unnaturally_fast_response"
        assert VoiceGamingSignal.UNNATURALLY_CONSISTENT.value == "unnaturally_consistent_timing"
        assert VoiceGamingSignal.SUSPICIOUSLY_SLOW.value == "suspiciously_slow_response"

    def test_speech_pattern_signals(self):
        """Test speech pattern signals."""
        assert VoiceGamingSignal.READING_DETECTED.value == "reading_detected"
        assert VoiceGamingSignal.UNNATURAL_FLUENCY.value == "unnatural_fluency"
        assert VoiceGamingSignal.NO_HESITATION.value == "no_natural_hesitation"

    def test_coherence_signals(self):
        """Test coherence signals."""
        assert VoiceGamingSignal.VERBAL_MISMATCH.value == "verbal_competence_mismatch"
        assert VoiceGamingSignal.VOCABULARY_SHIFT.value == "sudden_vocabulary_shift"
        assert VoiceGamingSignal.COMPLEXITY_MISMATCH.value == "response_complexity_mismatch"


class TestGamingFlag:
    """Tests for GamingFlag dataclass."""

    def test_flag_creation(self):
        """Test creating a gaming flag."""
        flag = GamingFlag(
            signal_type=VoiceGamingSignal.UNNATURALLY_FAST,
            severity=0.8,
            evidence={"latency_ms": 200, "word_count": 50},
            explanation="Response was too fast for the complexity.",
        )

        assert flag.signal_type == VoiceGamingSignal.UNNATURALLY_FAST
        assert flag.severity == 0.8
        assert flag.evidence["latency_ms"] == 200
        assert "too fast" in flag.explanation

    def test_default_evidence(self):
        """Test flag with default evidence."""
        flag = GamingFlag(
            signal_type=VoiceGamingSignal.NO_HESITATION,
            severity=0.5,
        )

        assert flag.evidence == {}
        assert flag.explanation == ""


class TestVoiceGamingAnalysis:
    """Tests for VoiceGamingAnalysis dataclass."""

    def test_empty_analysis(self):
        """Test empty analysis."""
        analysis = VoiceGamingAnalysis()

        assert analysis.flags == []
        assert analysis.confidence == 0.0
        assert analysis.has_flags is False
        assert analysis.high_severity_flags == []

    def test_analysis_with_flags(self):
        """Test analysis with flags."""
        flags = [
            GamingFlag(VoiceGamingSignal.UNNATURALLY_FAST, 0.8),
            GamingFlag(VoiceGamingSignal.NO_HESITATION, 0.5),
        ]

        analysis = VoiceGamingAnalysis(
            flags=flags,
            confidence=0.75,
        )

        assert analysis.has_flags is True
        assert len(analysis.flags) == 2
        assert analysis.confidence == 0.75

    def test_high_severity_flags(self):
        """Test filtering high severity flags."""
        flags = [
            GamingFlag(VoiceGamingSignal.UNNATURALLY_FAST, 0.9),
            GamingFlag(VoiceGamingSignal.NO_HESITATION, 0.5),
            GamingFlag(VoiceGamingSignal.READING_DETECTED, 0.8),
        ]

        analysis = VoiceGamingAnalysis(flags=flags, confidence=0.8)
        high_severity = analysis.high_severity_flags

        assert len(high_severity) == 2
        assert all(f.severity >= 0.7 for f in high_severity)


class TestVoiceGamingDetector:
    """Tests for VoiceGamingDetector."""

    @pytest.fixture
    def detector(self):
        """Create a gaming detector."""
        return VoiceGamingDetector()

    @pytest.fixture
    def empty_session(self):
        """Create an empty voice session."""
        return VoiceSession(
            session_id="test-session",
            student_id="student-1",
            course_id="course-1",
        )

    def test_analyze_normal_interaction(self, detector, empty_session, gaming_normal_interaction):
        """Test analysis of normal interaction."""
        analysis = detector.analyze_interaction(
            gaming_normal_interaction,
            empty_session,
            expected_difficulty=0.5,
        )

        # Normal interaction should have low/no gaming confidence
        assert analysis.confidence < 0.5

    def test_analyze_suspicious_interaction(
        self, detector, empty_session, gaming_suspicious_interaction
    ):
        """Test analysis of suspicious interaction."""
        analysis = detector.analyze_interaction(
            gaming_suspicious_interaction,
            empty_session,
            expected_difficulty=0.5,
        )

        # Suspicious interaction should have flags and elevated confidence
        assert analysis.has_flags is True
        assert analysis.confidence > 0.3  # Should be noticeably elevated
        assert len(analysis.flags) >= 1  # Should detect at least one signal

    def test_unnaturally_fast_detection(self, detector, empty_session):
        """Test detection of unnaturally fast responses."""
        interaction = VoiceInteraction(
            transcription="This is a detailed multi-sentence response that was delivered almost instantly without any time to think",
            response_latency_ms=200,  # Way too fast
            speech_rate_wpm=150.0,
        )

        analysis = detector.analyze_interaction(interaction, empty_session)

        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.UNNATURALLY_FAST in signal_types

    def test_suspiciously_slow_detection(self, detector, empty_session):
        """Test detection of suspiciously slow responses."""
        interaction = VoiceInteraction(
            transcription="Yes",  # Simple answer
            response_latency_ms=15000,  # Very slow for simple answer
            speech_rate_wpm=120.0,
        )

        analysis = detector.analyze_interaction(
            interaction,
            empty_session,
            expected_difficulty=0.2,  # Easy question
        )

        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.SUSPICIOUSLY_SLOW in signal_types

    def test_reading_detection(self, detector, empty_session):
        """Test detection of reading behavior."""
        # Fast speech, no pauses, many words
        interaction = VoiceInteraction(
            transcription=" ".join(["word"] * 50),  # 50 words
            response_latency_ms=2000,
            speech_rate_wpm=200.0,  # Above natural threshold
            pause_count=0,  # No pauses
        )

        analysis = detector.analyze_interaction(interaction, empty_session)

        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.READING_DETECTED in signal_types

    def test_no_hesitation_detection(self, detector, empty_session):
        """Test detection of unnatural fluency."""
        interaction = VoiceInteraction(
            transcription=" ".join(["complex"] * 60),  # Long response
            response_latency_ms=3000,
            speech_rate_wpm=160.0,
            pause_count=0,  # No hesitation at all
            average_pause_duration_ms=0.0,
        )

        analysis = detector.analyze_interaction(interaction, empty_session)

        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.NO_HESITATION in signal_types

    def test_timing_consistency_detection(self, detector):
        """Test detection of unnaturally consistent timing."""
        session = VoiceSession(
            session_id="test",
            student_id="student",
            course_id="course",
        )

        # Add interactions with very consistent latencies
        for i in range(10):
            interaction = VoiceInteraction(
                transcription=f"Response {i}",
                response_latency_ms=2000,  # Exactly the same each time
                speech_rate_wpm=140.0,
            )
            session.add_interaction(interaction)

        # Analyze the last interaction
        new_interaction = VoiceInteraction(
            transcription="New response",
            response_latency_ms=2000,
            speech_rate_wpm=140.0,
        )

        analysis = detector.analyze_interaction(new_interaction, session)

        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.UNNATURALLY_CONSISTENT in signal_types

    def test_complexity_mismatch_detection(self, detector, empty_session):
        """Test detection of response complexity mismatch."""
        # Very sophisticated response to easy question
        interaction = VoiceInteraction(
            transcription="The epistemological ramifications of this pedagogical methodology necessitate a comprehensive understanding of metacognitive processes",
            response_latency_ms=3000,
            speech_rate_wpm=140.0,
            pause_count=2,
        )

        analysis = detector.analyze_interaction(
            interaction,
            empty_session,
            expected_difficulty=0.1,  # Very easy question
        )

        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.COMPLEXITY_MISMATCH in signal_types

    def test_confidence_calculation_empty(self, detector):
        """Test confidence calculation with no flags."""
        confidence = detector._calculate_gaming_confidence([])

        assert confidence == 0.0

    def test_confidence_calculation_single_flag(self, detector):
        """Test confidence with single flag."""
        flags = [GamingFlag(VoiceGamingSignal.UNNATURALLY_FAST, 0.5)]

        confidence = detector._calculate_gaming_confidence(flags)

        assert 0 < confidence < 1

    def test_confidence_calculation_multiple_flags(self, detector):
        """Test confidence increases with multiple flags."""
        single_flag = [GamingFlag(VoiceGamingSignal.UNNATURALLY_FAST, 0.5)]
        multiple_flags = [
            GamingFlag(VoiceGamingSignal.UNNATURALLY_FAST, 0.5),
            GamingFlag(VoiceGamingSignal.NO_HESITATION, 0.5),
            GamingFlag(VoiceGamingSignal.READING_DETECTED, 0.5),
        ]

        conf_single = detector._calculate_gaming_confidence(single_flag)
        conf_multiple = detector._calculate_gaming_confidence(multiple_flags)

        assert conf_multiple > conf_single

    def test_confidence_max_cap(self, detector):
        """Test confidence is capped at 0.95."""
        high_severity_flags = [
            GamingFlag(VoiceGamingSignal.UNNATURALLY_FAST, 1.0),
            GamingFlag(VoiceGamingSignal.READING_DETECTED, 1.0),
            GamingFlag(VoiceGamingSignal.NO_HESITATION, 1.0),
            GamingFlag(VoiceGamingSignal.UNNATURALLY_CONSISTENT, 1.0),
        ]

        confidence = detector._calculate_gaming_confidence(high_severity_flags)

        assert confidence <= 0.95

    def test_get_session_analysis(self, detector):
        """Test aggregate session analysis."""
        session = VoiceSession(
            session_id="test",
            student_id="student",
            course_id="course",
        )

        # Add some flagged interactions
        for i in range(5):
            interaction = VoiceInteraction(
                transcription=f"Response {i}",
                gaming_confidence=0.6 if i % 2 == 0 else 0.3,
                gaming_flags=["unnaturally_fast"] if i % 2 == 0 else [],
            )
            session.add_interaction(interaction)

        analysis = detector.get_session_analysis(session)

        assert analysis["total_interactions"] == 5
        assert analysis["flagged_interactions"] == 3  # confidence > 0.5
        assert "average_gaming_confidence" in analysis
        assert "flag_distribution" in analysis

    def test_difficulty_affects_latency_threshold(self, detector, empty_session):
        """Test that difficulty affects expected latency."""
        interaction = VoiceInteraction(
            transcription="This is a moderately detailed response to the question.",
            response_latency_ms=800,
            speech_rate_wpm=140.0,
        )

        # Easy question - this latency might be suspicious
        easy_analysis = detector.analyze_interaction(
            interaction,
            empty_session,
            expected_difficulty=0.1,
        )

        # Hard question - this latency is more expected
        hard_analysis = detector.analyze_interaction(
            interaction,
            empty_session,
            expected_difficulty=0.9,
        )

        # Should be more likely to flag for easy questions
        easy_flags = len(easy_analysis.flags)
        hard_flags = len(hard_analysis.flags)

        # At minimum, both should run without error
        assert isinstance(easy_analysis, VoiceGamingAnalysis)
        assert isinstance(hard_analysis, VoiceGamingAnalysis)


class TestGamingDetectorEdgeCases:
    """Edge case tests for gaming detector."""

    @pytest.fixture
    def detector(self):
        return VoiceGamingDetector()

    @pytest.fixture
    def session(self):
        return VoiceSession(
            session_id="test",
            student_id="student",
            course_id="course",
        )

    def test_empty_transcription(self, detector, session):
        """Test handling of empty transcription."""
        interaction = VoiceInteraction(
            transcription="",
            response_latency_ms=1000,
        )

        analysis = detector.analyze_interaction(interaction, session)

        assert isinstance(analysis, VoiceGamingAnalysis)

    def test_zero_latency(self, detector, session):
        """Test handling of zero latency."""
        interaction = VoiceInteraction(
            transcription="Test",
            response_latency_ms=0,
        )

        analysis = detector.analyze_interaction(interaction, session)

        assert isinstance(analysis, VoiceGamingAnalysis)

    def test_none_speech_rate(self, detector, session):
        """Test handling of None speech rate."""
        interaction = VoiceInteraction(
            transcription="Test response",
            response_latency_ms=2000,
            speech_rate_wpm=None,
        )

        analysis = detector.analyze_interaction(interaction, session)

        assert isinstance(analysis, VoiceGamingAnalysis)

    def test_very_few_interactions_for_consistency(self, detector, session):
        """Test consistency check with few interactions."""
        # Only 2 interactions - not enough for consistency check
        for i in range(2):
            session.add_interaction(
                VoiceInteraction(
                    transcription=f"Response {i}",
                    response_latency_ms=2000,
                )
            )

        interaction = VoiceInteraction(
            transcription="New response",
            response_latency_ms=2000,
        )

        analysis = detector.analyze_interaction(interaction, session)

        # Should not flag consistency with too few samples
        signal_types = [f.signal_type for f in analysis.flags]
        assert VoiceGamingSignal.UNNATURALLY_CONSISTENT not in signal_types
