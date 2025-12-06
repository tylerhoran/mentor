"""Tests for the gaming detector module."""


import pytest

from mentor.core.assessment_engine.gaming_detector import (
    GamingDetector,
    GamingFlag,
    GamingThresholds,
    TrajectoryAnalysis,
)


class TestGamingThresholds:
    """Tests for GamingThresholds dataclass."""

    def test_default_values(self):
        """Test default threshold values."""
        thresholds = GamingThresholds()
        assert thresholds.min_response_time_ms == 3000
        assert thresholds.min_coherence == 0.4
        assert thresholds.max_competence_jump == 0.4
        assert thresholds.ai_detection_threshold == 0.7
        assert thresholds.max_correct_streak_without_struggle == 10

    def test_custom_values(self):
        """Test custom threshold values."""
        thresholds = GamingThresholds(
            min_response_time_ms=5000,
            min_coherence=0.5,
            max_competence_jump=0.3,
            ai_detection_threshold=0.8,
            max_correct_streak_without_struggle=5,
        )
        assert thresholds.min_response_time_ms == 5000
        assert thresholds.min_coherence == 0.5
        assert thresholds.max_competence_jump == 0.3
        assert thresholds.ai_detection_threshold == 0.8
        assert thresholds.max_correct_streak_without_struggle == 5


class TestGamingFlag:
    """Tests for GamingFlag dataclass."""

    def test_creation(self):
        """Test creating a gaming flag."""
        flag = GamingFlag(
            type="too_fast",
            severity="medium",
            evidence="Response was very fast",
        )
        assert flag.type == "too_fast"
        assert flag.severity == "medium"
        assert flag.evidence == "Response was very fast"
        assert flag.resolved is False

    def test_default_values(self):
        """Test default values."""
        flag = GamingFlag(type="test", severity="low")
        assert flag.timestamp is not None
        assert flag.evidence == ""
        assert flag.interaction_id is None
        assert flag.resolved is False

    def test_to_dict(self):
        """Test serialization to dict."""
        flag = GamingFlag(
            type="too_fast",
            severity="high",
            evidence="Very fast response",
            interaction_id="i123",
        )
        d = flag.to_dict()
        assert d["type"] == "too_fast"
        assert d["severity"] == "high"
        assert d["evidence"] == "Very fast response"
        assert d["interaction_id"] == "i123"
        assert d["resolved"] is False
        assert "timestamp" in d

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "type": "coherence_break",
            "severity": "medium",
            "evidence": "Incoherent response",
            "timestamp": "2024-01-01T12:00:00+00:00",
            "interaction_id": "i456",
            "resolved": True,
        }
        flag = GamingFlag.from_dict(data)
        assert flag.type == "coherence_break"
        assert flag.severity == "medium"
        assert flag.evidence == "Incoherent response"
        assert flag.interaction_id == "i456"
        assert flag.resolved is True


class TestTrajectoryAnalysis:
    """Tests for TrajectoryAnalysis dataclass."""

    def test_creation(self):
        """Test creating trajectory analysis."""
        analysis = TrajectoryAnalysis(
            classification="genuine",
            confidence=0.85,
        )
        assert analysis.classification == "genuine"
        assert analysis.confidence == 0.85
        assert analysis.flags == []
        assert analysis.summary == ""

    def test_with_flags(self):
        """Test trajectory analysis with flags."""
        flags = [
            GamingFlag(type="too_fast", severity="low"),
            GamingFlag(type="coherence_break", severity="medium"),
        ]
        analysis = TrajectoryAnalysis(
            classification="unclear",
            confidence=0.5,
            flags=flags,
            summary="Some concerns detected",
        )
        assert len(analysis.flags) == 2
        assert analysis.summary == "Some concerns detected"


class TestGamingDetector:
    """Tests for GamingDetector class."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = GamingDetector()
        assert detector.thresholds is not None
        assert detector._correct_streak == 0
        assert detector._previous_mastery == {}

    def test_initialization_custom_thresholds(self):
        """Test initialization with custom thresholds."""
        thresholds = GamingThresholds(min_response_time_ms=5000)
        detector = GamingDetector(thresholds=thresholds)
        assert detector.thresholds.min_response_time_ms == 5000

    def test_check_response_time_normal(self):
        """Test normal response time."""
        detector = GamingDetector()
        # Normal response time (above threshold)
        flag = detector._check_response_time(5000, 50, "i1")
        assert flag is None

    def test_check_response_time_too_fast(self):
        """Test suspiciously fast response time."""
        detector = GamingDetector()
        # Very fast response
        flag = detector._check_response_time(500, 50, "i1")
        assert flag is not None
        assert flag.type == "too_fast"
        assert flag.interaction_id == "i1"

    def test_check_response_time_scales_with_length(self):
        """Test that threshold scales with message length."""
        detector = GamingDetector()
        # Longer message should require more time
        # 200 chars = 3000 base + (200-100)*20 = 5000ms expected
        flag = detector._check_response_time(4000, 200, "i1")
        assert flag is not None  # Still too fast for long message

    def test_check_correct_streak_normal(self):
        """Test normal correct streak."""
        detector = GamingDetector()
        # A few correct answers
        for _ in range(3):
            flag = detector.check_correct_streak(True)
        assert flag is None
        assert detector._correct_streak == 3

    def test_check_correct_streak_reset_on_incorrect(self):
        """Test streak resets on incorrect answer."""
        detector = GamingDetector()
        detector.check_correct_streak(True)
        detector.check_correct_streak(True)
        detector.check_correct_streak(False)
        assert detector._correct_streak == 0

    def test_check_correct_streak_suspicious(self):
        """Test suspicious correct streak."""
        detector = GamingDetector()
        flag = None
        # Many correct answers without struggle
        for _ in range(12):
            flag = detector.check_correct_streak(True)

        assert flag is not None
        assert flag.type == "suspicious_streak"

    def test_reset_streak(self):
        """Test resetting streak."""
        detector = GamingDetector()
        detector.check_correct_streak(True)
        detector.check_correct_streak(True)
        detector.reset_streak()
        assert detector._correct_streak == 0

    def test_check_competence_jump_normal(self):
        """Test normal competence progression."""
        detector = GamingDetector()
        # Set previous mastery
        detector._previous_mastery["c1"] = 0.3

        # Small improvement
        flag = detector._check_competence_jump("c1", 0.4, "i1")
        assert flag is None

    def test_check_competence_jump_suspicious(self):
        """Test suspicious competence jump."""
        detector = GamingDetector()
        # Set previous mastery
        detector._previous_mastery["c1"] = 0.2

        # Large jump
        flag = detector._check_competence_jump("c1", 0.8, "i1")
        assert flag is not None
        assert flag.type == "sudden_competence"

    def test_check_competence_jump_small_value(self):
        """Test competence check with small mastery value."""
        detector = GamingDetector()
        # Set previous mastery to 0
        detector._previous_mastery["c1"] = 0.0
        # Small jump within threshold (0.4)
        flag = detector._check_competence_jump("c1", 0.3, "i1")
        assert flag is None

    @pytest.mark.asyncio
    async def test_check_interaction_basic(self):
        """Test basic interaction check."""
        detector = GamingDetector()
        flags = await detector.check_interaction(
            student_message="This is a normal response.",
            response_time_ms=5000,
            current_mastery=0.5,
            concept_id="c1",
            conversation_history=[],
            interaction_id="i1",
        )
        # Normal interaction should have no flags
        assert len(flags) == 0

    @pytest.mark.asyncio
    async def test_check_interaction_fast_response(self):
        """Test interaction with fast response."""
        detector = GamingDetector()
        flags = await detector.check_interaction(
            student_message="Quick response",
            response_time_ms=100,  # Very fast
            current_mastery=0.5,
            concept_id="c1",
            conversation_history=[],
            interaction_id="i1",
        )
        # Should flag fast response
        assert any(f.type == "too_fast" for f in flags)

    @pytest.mark.asyncio
    async def test_analyze_trajectory_genuine(self):
        """Test trajectory analysis with no flags."""
        detector = GamingDetector()
        analysis = await detector.analyze_trajectory(
            interactions=[],
            gaming_flags=[],
        )
        assert analysis.classification == "genuine"
        assert analysis.confidence >= 0.7

    @pytest.mark.asyncio
    async def test_analyze_trajectory_suspected_gaming(self):
        """Test trajectory analysis with many flags."""
        detector = GamingDetector()
        flags = [
            GamingFlag(type="too_fast", severity="high"),
            GamingFlag(type="too_fast", severity="high"),
            GamingFlag(type="too_fast", severity="high"),
        ]
        analysis = await detector.analyze_trajectory(
            interactions=[],
            gaming_flags=flags,
        )
        assert analysis.classification == "suspected_gaming"

    @pytest.mark.asyncio
    async def test_analyze_trajectory_unclear(self):
        """Test trajectory analysis with moderate flags."""
        detector = GamingDetector()
        flags = [
            GamingFlag(type="too_fast", severity="medium"),
            GamingFlag(type="too_fast", severity="medium"),
            GamingFlag(type="too_fast", severity="low"),
        ]
        analysis = await detector.analyze_trajectory(
            interactions=[],
            gaming_flags=flags,
        )
        assert analysis.classification == "unclear"

    @pytest.mark.asyncio
    async def test_severity_weighting(self):
        """Test that severity affects classification."""
        detector = GamingDetector()

        # High severity flags have more weight
        high_flags = [GamingFlag(type="test", severity="high") for _ in range(3)]
        low_flags = [GamingFlag(type="test", severity="low") for _ in range(3)]

        high_analysis = await detector.analyze_trajectory([], high_flags)
        low_analysis = await detector.analyze_trajectory([], low_flags)

        # High severity should be more suspicious
        assert (
            high_analysis.classification != low_analysis.classification
            or high_analysis.confidence != low_analysis.confidence
        )

    @pytest.mark.asyncio
    async def test_resolved_flags_ignored(self):
        """Test that resolved flags are ignored."""
        detector = GamingDetector()
        flags = [
            GamingFlag(type="too_fast", severity="high", resolved=True),
            GamingFlag(type="too_fast", severity="high", resolved=True),
            GamingFlag(type="too_fast", severity="high", resolved=True),
        ]
        analysis = await detector.analyze_trajectory(
            interactions=[],
            gaming_flags=flags,
        )
        # Resolved flags should be ignored
        assert analysis.classification == "genuine"

    def test_flag_resolution(self):
        """Test marking a flag as resolved."""
        flag = GamingFlag(type="too_fast", severity="medium")
        assert flag.resolved is False
        flag.resolved = True
        assert flag.resolved is True
