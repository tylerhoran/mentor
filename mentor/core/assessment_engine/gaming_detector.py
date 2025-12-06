"""
Detect gaming attempts in student interactions.

Signals monitored:
- Response time (too fast = copy-paste)
- Coherence breaks (sudden competence jumps)
- AI-generated text patterns
- Pattern matching without understanding
- Inability to explain correct answers
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import structlog

from mentor.config import settings

if TYPE_CHECKING:
    from mentor.core.tutor_runtime.llm_client import LLMClient

logger = structlog.get_logger()


@dataclass
class GamingThresholds:
    """Configuration thresholds for gaming detection."""

    min_response_time_ms: int = 3000  # Faster = suspicious
    min_coherence: float = 0.4  # Below this is suspicious
    max_competence_jump: float = 0.4  # Sudden jump in competence
    ai_detection_threshold: float = 0.7  # AI-generated text detection
    max_correct_streak_without_struggle: int = 10  # Too many correct in a row


@dataclass
class GamingFlag:
    """A detected gaming signal."""

    type: str  # 'too_fast', 'coherence_break', 'sudden_competence', 'ai_generated', etc.
    severity: str  # 'low', 'medium', 'high'
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    evidence: str = ""
    interaction_id: str | None = None
    resolved: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat(),
            "evidence": self.evidence,
            "interaction_id": self.interaction_id,
            "resolved": self.resolved,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GamingFlag":
        """Create from dictionary."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(UTC)

        return cls(
            type=data.get("type", "unknown"),
            severity=data.get("severity", "low"),
            timestamp=timestamp,
            evidence=data.get("evidence", ""),
            interaction_id=data.get("interaction_id"),
            resolved=data.get("resolved", False),
        )


@dataclass
class TrajectoryAnalysis:
    """Result of analyzing a learning trajectory."""

    classification: str  # 'genuine', 'suspected_gaming', 'unclear'
    confidence: float  # 0.0 to 1.0
    flags: list[GamingFlag] = field(default_factory=list)
    summary: str = ""


class GamingDetector:
    """
    Detect gaming attempts in student interactions.

    Uses multiple signals:
    1. Response time analysis
    2. Coherence checking (does answer fit conversation?)
    3. Competence jump detection (sudden improvement without learning)
    4. AI-generated text detection
    5. Pattern analysis (always correct without struggle)
    """

    def __init__(
        self,
        thresholds: GamingThresholds | None = None,
        llm_client: "LLMClient | None" = None,
    ):
        """
        Initialize the gaming detector.

        Args:
            thresholds: Detection thresholds
            llm_client: LLM client for AI detection
        """
        self.thresholds = thresholds or GamingThresholds(
            min_response_time_ms=settings.gaming_min_response_time_ms,
            min_coherence=settings.gaming_min_coherence,
            max_competence_jump=settings.gaming_max_competence_jump,
            ai_detection_threshold=settings.gaming_ai_detection_threshold,
        )
        self.llm_client = llm_client

        # Tracking state for trajectory analysis
        self._correct_streak = 0
        self._previous_mastery: dict[str, float] = {}

    async def check_interaction(
        self,
        student_message: str,
        response_time_ms: int | None,
        current_mastery: float,
        concept_id: str,
        conversation_history: list[dict[str, str]],
        interaction_id: str | None = None,
    ) -> list[GamingFlag]:
        """
        Check a single interaction for gaming signals.

        Args:
            student_message: The student's message
            response_time_ms: Time taken to respond
            current_mastery: Current mastery estimate for concept
            concept_id: Concept being discussed
            conversation_history: Recent conversation
            interaction_id: Optional interaction ID for tracking

        Returns:
            List of gaming flags detected
        """
        flags = []

        # 1. Response time check
        if response_time_ms is not None:
            flag = self._check_response_time(response_time_ms, len(student_message), interaction_id)
            if flag:
                flags.append(flag)

        # 2. Coherence check
        if conversation_history:
            flag = await self._check_coherence(
                student_message, conversation_history, interaction_id
            )
            if flag:
                flags.append(flag)

        # 3. Competence jump check
        if concept_id in self._previous_mastery:
            flag = self._check_competence_jump(concept_id, current_mastery, interaction_id)
            if flag:
                flags.append(flag)

        # Update tracking
        self._previous_mastery[concept_id] = current_mastery

        # 4. AI detection (if LLM client available)
        if self.llm_client and len(student_message) > 50:
            flag = await self._check_ai_generated(student_message, interaction_id)
            if flag:
                flags.append(flag)

        logger.info(
            "gaming_check_complete",
            flags_count=len(flags),
            interaction_id=interaction_id,
        )

        return flags

    def _check_response_time(
        self,
        response_time_ms: int,
        message_length: int,
        interaction_id: str | None,
    ) -> GamingFlag | None:
        """Check if response time is suspiciously fast."""
        # Adjust threshold based on message length
        # Longer messages should take longer to type
        expected_min_time = self.thresholds.min_response_time_ms
        if message_length > 100:
            expected_min_time += (message_length - 100) * 20  # ~20ms per char over 100

        if response_time_ms < expected_min_time:
            # Determine severity based on how fast
            ratio = response_time_ms / expected_min_time
            if ratio < 0.2:
                severity = "high"
            elif ratio < 0.5:
                severity = "medium"
            else:
                severity = "low"

            return GamingFlag(
                type="too_fast",
                severity=severity,
                evidence=f"Response time {response_time_ms}ms for {message_length} char message "
                f"(expected min: {expected_min_time}ms)",
                interaction_id=interaction_id,
            )

        return None

    async def _check_coherence(
        self,
        student_message: str,
        conversation_history: list[dict[str, str]],
        interaction_id: str | None,
    ) -> GamingFlag | None:
        """Check if response is coherent with conversation context."""
        if not self.llm_client:
            return None

        # Get last few messages for context
        recent_history = conversation_history[-6:]  # Last 3 exchanges
        context = "\n".join(f"{msg['role']}: {msg['content'][:200]}" for msg in recent_history)

        prompt = f"""Analyze if the student's response is coherent with the conversation context.

Conversation:
{context}

Student's new response: "{student_message[:500]}"

Rate coherence from 0.0 (completely incoherent) to 1.0 (perfectly coherent).
Consider:
- Does it follow logically from the conversation?
- Does it address what was being discussed?
- Does it show understanding of previous context?

Respond with only a number between 0.0 and 1.0."""

        try:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are a coherence analyzer. Respond only with a number.",
                temperature=0.1,
                max_tokens=10,
            )

            coherence_score = float(response.strip())

            if coherence_score < self.thresholds.min_coherence:
                severity = "high" if coherence_score < 0.2 else "medium"
                return GamingFlag(
                    type="coherence_break",
                    severity=severity,
                    evidence=f"Coherence score: {coherence_score:.2f}",
                    interaction_id=interaction_id,
                )

        except (ValueError, Exception) as e:
            logger.warning("coherence_check_failed", error=str(e))

        return None

    def _check_competence_jump(
        self,
        concept_id: str,
        current_mastery: float,
        interaction_id: str | None,
    ) -> GamingFlag | None:
        """Check for sudden competence jumps."""
        previous = self._previous_mastery.get(concept_id, 0.0)
        jump = current_mastery - previous

        if jump > self.thresholds.max_competence_jump:
            severity = "high" if jump > 0.6 else "medium"
            return GamingFlag(
                type="sudden_competence",
                severity=severity,
                evidence=f"Mastery jumped from {previous:.2f} to {current_mastery:.2f} "
                f"(+{jump:.2f})",
                interaction_id=interaction_id,
            )

        return None

    async def _check_ai_generated(
        self,
        student_message: str,
        interaction_id: str | None,
    ) -> GamingFlag | None:
        """Check if text appears to be AI-generated."""
        if not self.llm_client:
            return None

        prompt = f"""Analyze if this text appears to be AI-generated rather than written by a student.

Text: "{student_message[:1000]}"

Consider:
- Writing style (too polished, too structured?)
- Vocabulary (unusually sophisticated?)
- Content (too comprehensive for a learning student?)
- Tone (robotic, lacks natural student hesitation?)

Rate the probability it's AI-generated from 0.0 to 1.0.
Respond with only a number."""

        try:
            response = await self.llm_client.generate(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You detect AI-generated text. Respond only with a probability.",
                temperature=0.1,
                max_tokens=10,
            )

            ai_probability = float(response.strip())

            if ai_probability >= self.thresholds.ai_detection_threshold:
                severity = "high" if ai_probability > 0.9 else "medium"
                return GamingFlag(
                    type="ai_generated",
                    severity=severity,
                    evidence=f"AI-generated probability: {ai_probability:.2f}",
                    interaction_id=interaction_id,
                )

        except (ValueError, Exception) as e:
            logger.warning("ai_detection_failed", error=str(e))

        return None

    def check_correct_streak(
        self,
        is_correct: bool,
        interaction_id: str | None = None,
    ) -> GamingFlag | None:
        """Track streak of correct answers without struggle."""
        if is_correct:
            self._correct_streak += 1
        else:
            self._correct_streak = 0

        if self._correct_streak >= self.thresholds.max_correct_streak_without_struggle:
            return GamingFlag(
                type="suspicious_streak",
                severity="medium",
                evidence=f"{self._correct_streak} correct answers without any struggle",
                interaction_id=interaction_id,
            )

        return None

    def reset_streak(self) -> None:
        """Reset the correct streak counter."""
        self._correct_streak = 0

    async def analyze_trajectory(
        self,
        interactions: list[dict[str, Any]],
        gaming_flags: list[GamingFlag],
    ) -> TrajectoryAnalysis:
        """
        Analyze full learning trajectory for gaming patterns.

        Args:
            interactions: List of interaction records
            gaming_flags: Previously detected gaming flags

        Returns:
            TrajectoryAnalysis with classification
        """
        # Count flags by severity
        high_count = sum(1 for f in gaming_flags if f.severity == "high" and not f.resolved)
        medium_count = sum(1 for f in gaming_flags if f.severity == "medium" and not f.resolved)
        low_count = sum(1 for f in gaming_flags if f.severity == "low" and not f.resolved)

        # Calculate weighted score
        score = high_count * 3 + medium_count * 2 + low_count * 1

        # Classify based on score
        if score >= 10 or high_count >= 3:
            classification = "suspected_gaming"
            confidence = min(0.95, 0.5 + score * 0.05)
        elif score >= 5 or high_count >= 1:
            classification = "unclear"
            confidence = 0.5
        else:
            classification = "genuine"
            confidence = min(0.9, 0.7 + (10 - score) * 0.02)

        # Build summary
        summary_parts = []
        if high_count > 0:
            summary_parts.append(f"{high_count} high-severity flags")
        if medium_count > 0:
            summary_parts.append(f"{medium_count} medium-severity flags")
        if low_count > 0:
            summary_parts.append(f"{low_count} low-severity flags")

        summary = f"Trajectory analysis: {', '.join(summary_parts) or 'No flags detected'}."

        return TrajectoryAnalysis(
            classification=classification,
            confidence=confidence,
            flags=gaming_flags,
            summary=summary,
        )
