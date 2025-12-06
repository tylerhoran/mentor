"""Voice-specific gaming detection signals."""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import numpy as np

from .session import VoiceInteraction, VoiceSession

logger = logging.getLogger(__name__)


class VoiceGamingSignal(str, Enum):
    """Types of gaming signals detectable in voice interaction."""

    # Response timing
    UNNATURALLY_FAST = "unnaturally_fast_response"
    UNNATURALLY_CONSISTENT = "unnaturally_consistent_timing"
    SUSPICIOUSLY_SLOW = "suspiciously_slow_response"

    # Speech patterns
    READING_DETECTED = "reading_detected"
    UNNATURAL_FLUENCY = "unnatural_fluency"
    NO_HESITATION = "no_natural_hesitation"
    MONOTONE_DELIVERY = "monotone_delivery"

    # Coherence
    VERBAL_MISMATCH = "verbal_competence_mismatch"
    VOCABULARY_SHIFT = "sudden_vocabulary_shift"
    COMPLEXITY_MISMATCH = "response_complexity_mismatch"


@dataclass
class GamingFlag:
    """A single gaming detection flag."""

    signal_type: VoiceGamingSignal
    severity: float  # 0-1, higher = more severe
    evidence: dict = field(default_factory=dict)
    explanation: str = ""


@dataclass
class VoiceGamingAnalysis:
    """Analysis of potential gaming in voice interaction."""

    flags: List[GamingFlag] = field(default_factory=list)
    confidence: float = 0.0  # 0-1, higher = more confident gaming is occurring
    details: dict = field(default_factory=dict)

    @property
    def has_flags(self) -> bool:
        return len(self.flags) > 0

    @property
    def high_severity_flags(self) -> List[GamingFlag]:
        return [f for f in self.flags if f.severity >= 0.7]


class VoiceGamingDetector:
    """Detect gaming patterns specific to voice interaction."""

    # Thresholds
    MIN_NATURAL_LATENCY_MS = 500  # Humans can't respond faster
    MAX_NATURAL_LATENCY_MS = 10000  # Too long suggests looking something up
    MIN_WPM_NATURAL = 100  # Below this might indicate reading slowly
    MAX_WPM_NATURAL = 180  # Above this suggests prepared/memorized/reading
    MIN_NATURAL_CV = 0.15  # Minimum coefficient of variation for natural timing

    def __init__(self):
        self.history: List[VoiceInteraction] = []

    def analyze_interaction(
        self,
        interaction: VoiceInteraction,
        session: VoiceSession,
        expected_difficulty: float = 0.5,  # 0-1, how hard the question was
    ) -> VoiceGamingAnalysis:
        """
        Analyze a single voice interaction for gaming signals.

        Args:
            interaction: The interaction to analyze
            session: Current session context
            expected_difficulty: How difficult the question was (affects expected latency)
        """
        flags = []
        details = {}

        # 1. Response latency analysis
        latency_flags = self._analyze_latency(interaction, session, expected_difficulty)
        flags.extend(latency_flags)

        # 2. Speech pattern analysis
        if interaction.speech_rate_wpm:
            speech_flags = self._analyze_speech_patterns(interaction)
            flags.extend(speech_flags)

        # 3. Timing consistency analysis
        if len(session.interactions) >= 3:
            consistency_flags = self._analyze_timing_consistency(session)
            flags.extend(consistency_flags)

        # 4. Response complexity analysis
        complexity_flags = self._analyze_response_complexity(interaction, expected_difficulty)
        flags.extend(complexity_flags)

        # Calculate overall confidence
        confidence = self._calculate_gaming_confidence(flags)

        return VoiceGamingAnalysis(flags=flags, confidence=confidence, details=details)

    def _analyze_latency(
        self, interaction: VoiceInteraction, session: VoiceSession, expected_difficulty: float
    ) -> List[GamingFlag]:
        """Analyze response latency for gaming signals."""
        flags = []
        latency = interaction.response_latency_ms

        if latency <= 0:
            return flags

        # Adjust expected latency based on difficulty
        min_expected = self.MIN_NATURAL_LATENCY_MS * (1 + expected_difficulty)

        if latency < min_expected:
            # Suspiciously fast
            word_count = len(interaction.transcription.split())
            if word_count > 20:  # Long response should take time
                flags.append(
                    GamingFlag(
                        signal_type=VoiceGamingSignal.UNNATURALLY_FAST,
                        severity=0.8,
                        evidence={
                            "latency_ms": latency,
                            "word_count": word_count,
                            "expected_min_ms": min_expected,
                        },
                        explanation=(
                            f"Response of {word_count} words delivered in {latency}ms, "
                            f"faster than natural speech generation allows"
                        ),
                    )
                )
            elif word_count > 10:
                flags.append(
                    GamingFlag(
                        signal_type=VoiceGamingSignal.UNNATURALLY_FAST,
                        severity=0.5,
                        evidence={
                            "latency_ms": latency,
                            "word_count": word_count,
                        },
                        explanation=f"Quick response of {word_count} words in {latency}ms",
                    )
                )

        elif latency > self.MAX_NATURAL_LATENCY_MS and expected_difficulty < 0.5:
            # Suspiciously slow for an easy question
            flags.append(
                GamingFlag(
                    signal_type=VoiceGamingSignal.SUSPICIOUSLY_SLOW,
                    severity=0.4,
                    evidence={"latency_ms": latency, "expected_difficulty": expected_difficulty},
                    explanation=(
                        f"Response took {latency}ms for a relatively simple question, "
                        f"possibly indicating lookup"
                    ),
                )
            )

        return flags

    def _analyze_speech_patterns(self, interaction: VoiceInteraction) -> List[GamingFlag]:
        """Analyze speech patterns for gaming signals."""
        flags = []

        wpm = interaction.speech_rate_wpm
        word_count = len(interaction.transcription.split())

        if wpm is None:
            return flags

        # Reading detection (too fast, too consistent, no pauses)
        if wpm > self.MAX_WPM_NATURAL:
            if interaction.pause_count < 2 and word_count > 30:
                flags.append(
                    GamingFlag(
                        signal_type=VoiceGamingSignal.READING_DETECTED,
                        severity=0.7,
                        evidence={
                            "wpm": wpm,
                            "pause_count": interaction.pause_count,
                            "word_count": word_count,
                        },
                        explanation=(
                            f"Speech rate of {wpm:.0f} WPM with minimal pauses "
                            f"suggests reading prepared text"
                        ),
                    )
                )
            else:
                flags.append(
                    GamingFlag(
                        signal_type=VoiceGamingSignal.UNNATURAL_FLUENCY,
                        severity=0.5,
                        evidence={"wpm": wpm},
                        explanation=f"Unusually fast speech rate: {wpm:.0f} WPM",
                    )
                )

        # Unnatural fluency (no hesitation on difficult concepts)
        if interaction.pause_count == 0 and word_count > 50:
            flags.append(
                GamingFlag(
                    signal_type=VoiceGamingSignal.NO_HESITATION,
                    severity=0.5,
                    evidence={"word_count": word_count, "pause_count": 0},
                    explanation=(
                        f"Long response ({word_count} words) with no natural hesitation or pauses"
                    ),
                )
            )

        return flags

    def _analyze_timing_consistency(self, session: VoiceSession) -> List[GamingFlag]:
        """Check if response timings are unnaturally consistent."""
        flags = []

        recent = session.get_recent_interactions(10)
        latencies = [i.response_latency_ms for i in recent if i.response_latency_ms > 0]

        if len(latencies) >= 5:
            # Calculate coefficient of variation
            mean_latency = np.mean(latencies)
            std_latency = np.std(latencies)
            cv = std_latency / mean_latency if mean_latency > 0 else 0

            # Humans have natural variation; too consistent is suspicious
            if cv < self.MIN_NATURAL_CV:
                flags.append(
                    GamingFlag(
                        signal_type=VoiceGamingSignal.UNNATURALLY_CONSISTENT,
                        severity=0.6,
                        evidence={
                            "coefficient_of_variation": float(cv),
                            "mean_latency_ms": float(mean_latency),
                            "std_latency_ms": float(std_latency),
                            "sample_size": len(latencies),
                        },
                        explanation=(
                            f"Response latencies are unusually consistent "
                            f"(CV={cv:.2f}), suggesting scripted or automated responses"
                        ),
                    )
                )

        return flags

    def _analyze_response_complexity(
        self, interaction: VoiceInteraction, expected_difficulty: float
    ) -> List[GamingFlag]:
        """Analyze if response complexity matches expected student level."""
        flags = []

        text = interaction.transcription
        if not text:
            return flags

        # Simple complexity heuristics
        words = text.split()
        word_count = len(words)

        # Average word length (indicator of vocabulary complexity)
        avg_word_length = sum(len(w) for w in words) / word_count if word_count > 0 else 0

        # Long words (>8 chars) ratio
        long_words = [w for w in words if len(w) > 8]
        long_word_ratio = len(long_words) / word_count if word_count > 0 else 0

        # If response is very sophisticated for a simple question
        if expected_difficulty < 0.3 and avg_word_length > 6 and long_word_ratio > 0.2:
            flags.append(
                GamingFlag(
                    signal_type=VoiceGamingSignal.COMPLEXITY_MISMATCH,
                    severity=0.4,
                    evidence={
                        "avg_word_length": avg_word_length,
                        "long_word_ratio": long_word_ratio,
                        "expected_difficulty": expected_difficulty,
                    },
                    explanation=(
                        f"Response vocabulary complexity seems high for the "
                        f"difficulty level of the question"
                    ),
                )
            )

        return flags

    def _calculate_gaming_confidence(self, flags: List[GamingFlag]) -> float:
        """Calculate overall confidence that gaming is occurring."""
        if not flags:
            return 0.0

        # Weight by severity
        total_severity = sum(f.severity for f in flags)

        # Multiple flags increase confidence
        flag_multiplier = min(1 + (len(flags) - 1) * 0.2, 2.0)

        # Normalize to 0-1 with diminishing returns
        raw_confidence = total_severity * flag_multiplier
        confidence = 1 - np.exp(-raw_confidence / 3)

        return min(float(confidence), 0.95)  # Never 100% confident

    def get_session_analysis(self, session: VoiceSession) -> dict:
        """Get aggregate gaming analysis for entire session."""
        all_flags = []
        total_confidence = 0.0

        for interaction in session.interactions:
            if interaction.gaming_confidence > 0:
                total_confidence += interaction.gaming_confidence
                all_flags.extend(interaction.gaming_flags)

        # Count flag types
        flag_counts = {}
        for flag_name in all_flags:
            flag_counts[flag_name] = flag_counts.get(flag_name, 0) + 1

        avg_confidence = total_confidence / len(session.interactions) if session.interactions else 0

        return {
            "total_interactions": len(session.interactions),
            "flagged_interactions": sum(
                1 for i in session.interactions if i.gaming_confidence > 0.5
            ),
            "average_gaming_confidence": avg_confidence,
            "flag_distribution": flag_counts,
            "high_risk": avg_confidence > 0.6,
        }
