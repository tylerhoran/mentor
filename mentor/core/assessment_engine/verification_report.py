"""
Generate reports for human verification of learning.

Report includes:
- Summary statistics
- Mastery estimates with confidence
- Concerns and flags
- Recommended verification questions
- Key interaction excerpts
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import structlog

from mentor.core.assessment_engine.gaming_detector import GamingFlag
from mentor.core.student_state.mastery_tracker import MasteryEstimate

logger = structlog.get_logger()


@dataclass
class VerificationQuestion:
    """A question recommended for human verification."""

    concept_id: str
    concept_name: str
    question: str
    rationale: str  # Why this question
    look_for: str  # What indicates understanding
    difficulty: str = "medium"  # easy, medium, hard

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "concept_name": self.concept_name,
            "question": self.question,
            "rationale": self.rationale,
            "look_for": self.look_for,
            "difficulty": self.difficulty,
        }


@dataclass
class InteractionExcerpt:
    """Key interaction excerpt for verification report."""

    type: str  # 'breakthrough', 'struggle', 'gaming_flag'
    concept_id: str | None
    interactions: list[dict[str, Any]]
    note: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "concept_id": self.concept_id,
            "interactions": self.interactions,
            "note": self.note,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class VerificationReport:
    """Complete verification report for faculty review."""

    student_id: str
    course_id: str
    generated_at: datetime

    # Summary
    summary: dict[str, Any]

    # Detailed data
    mastery_by_concept: list[dict[str, Any]]
    concerns: list[GamingFlag]
    recommended_questions: list[VerificationQuestion]
    key_excerpts: list[InteractionExcerpt]

    def to_dict(self) -> dict[str, Any]:
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "generated_at": self.generated_at.isoformat(),
            "summary": self.summary,
            "mastery_by_concept": self.mastery_by_concept,
            "concerns": [c.to_dict() for c in self.concerns],
            "recommended_questions": [q.to_dict() for q in self.recommended_questions],
            "key_excerpts": [e.to_dict() for e in self.key_excerpts],
        }


class VerificationReportGenerator:
    """
    Generate comprehensive verification reports for human assessment.

    The report is designed to help faculty:
    1. Understand student's demonstrated mastery
    2. Identify areas of concern
    3. Prepare verification questions
    4. Review key moments in the learning trajectory
    """

    def __init__(
        self,
        course_name: str,
        concepts: dict[str, str],  # concept_id -> concept_name
    ):
        """
        Initialize the report generator.

        Args:
            course_name: Name of the course
            concepts: Mapping of concept IDs to names
        """
        self.course_name = course_name
        self.concepts = concepts

    async def generate_report(
        self,
        student_id: str,
        course_id: str,
        mastery_data: dict[str, MasteryEstimate],
        engagement_data: dict[str, Any],
        gaming_flags: list[GamingFlag],
        interactions: list[dict[str, Any]],
        max_questions: int = 10,
        include_excerpts: bool = True,
    ) -> VerificationReport:
        """
        Generate a comprehensive verification report.

        Args:
            student_id: Student ID
            course_id: Course ID
            mastery_data: Mastery estimates by concept
            engagement_data: Engagement metrics
            gaming_flags: Detected gaming flags
            interactions: Interaction history
            max_questions: Maximum verification questions to include
            include_excerpts: Whether to include interaction excerpts

        Returns:
            Complete VerificationReport
        """
        logger.info(
            "generating_verification_report",
            student_id=student_id,
            course_id=course_id,
        )

        # Build summary
        summary = self._build_summary(mastery_data, engagement_data, gaming_flags)

        # Build mastery breakdown
        mastery_by_concept = self._build_mastery_breakdown(mastery_data)

        # Get concerns (unresolved flags)
        concerns = [f for f in gaming_flags if not f.resolved]

        # Generate verification questions
        questions = self._generate_verification_questions(mastery_data, concerns, max_questions)

        # Select key excerpts
        excerpts = []
        if include_excerpts:
            excerpts = self._select_key_excerpts(interactions, gaming_flags)

        return VerificationReport(
            student_id=student_id,
            course_id=course_id,
            generated_at=datetime.now(UTC),
            summary=summary,
            mastery_by_concept=mastery_by_concept,
            concerns=concerns,
            recommended_questions=questions,
            key_excerpts=excerpts,
        )

    def _build_summary(
        self,
        mastery_data: dict[str, MasteryEstimate],
        engagement_data: dict[str, Any],
        gaming_flags: list[GamingFlag],
    ) -> dict[str, Any]:
        """Build summary statistics."""
        # Calculate overall mastery
        estimates = [m.estimate for m in mastery_data.values()]
        overall_mastery = sum(estimates) / len(estimates) if estimates else 0.0

        # Count concepts at various levels
        mastered = sum(1 for m in mastery_data.values() if m.estimate >= 0.8)
        developing = sum(1 for m in mastery_data.values() if 0.4 <= m.estimate < 0.8)
        struggling = sum(1 for m in mastery_data.values() if m.estimate < 0.4)

        # Count gaming concerns
        unresolved_flags = [f for f in gaming_flags if not f.resolved]
        high_severity = sum(1 for f in unresolved_flags if f.severity == "high")

        return {
            "overall_mastery": overall_mastery,
            "mastered_concepts": mastered,
            "developing_concepts": developing,
            "struggling_concepts": struggling,
            "total_concepts": len(mastery_data),
            "total_interactions": engagement_data.get("total_interactions", 0),
            "total_time_minutes": engagement_data.get("total_time_seconds", 0) / 60,
            "session_count": engagement_data.get("session_count", 0),
            "gaming_flags_count": len(unresolved_flags),
            "high_severity_flags": high_severity,
            "needs_attention": high_severity >= 2 or len(unresolved_flags) >= 5,
        }

    def _build_mastery_breakdown(
        self,
        mastery_data: dict[str, MasteryEstimate],
    ) -> list[dict[str, Any]]:
        """Build detailed mastery breakdown by concept."""
        breakdown = []

        for concept_id, mastery in mastery_data.items():
            concept_name = self.concepts.get(concept_id, f"Concept {concept_id}")

            # Determine status
            if mastery.estimate >= 0.8 and mastery.confidence >= 0.5:
                status = "mastered"
            elif mastery.estimate >= 0.6:
                status = "proficient"
            elif mastery.estimate >= 0.4:
                status = "developing"
            else:
                status = "struggling"

            breakdown.append(
                {
                    "concept_id": concept_id,
                    "concept_name": concept_name,
                    "estimate": mastery.estimate,
                    "confidence": mastery.confidence,
                    "interaction_count": mastery.interaction_count,
                    "status": status,
                    "last_updated": mastery.last_updated.isoformat(),
                }
            )

        # Sort by estimate (lowest first for attention)
        breakdown.sort(key=lambda x: x["estimate"])

        return breakdown

    def _generate_verification_questions(
        self,
        mastery_data: dict[str, MasteryEstimate],
        concerns: list[GamingFlag],
        max_questions: int,
    ) -> list[VerificationQuestion]:
        """
        Generate questions targeting:
        1. Uncertain mastery areas (0.4-0.7 estimate)
        2. Areas with gaming flags
        3. High mastery areas (test transfer - if they really understand)
        """
        questions = []

        # Priority 1: Concepts with gaming flags
        for flag in concerns:
            if hasattr(flag, "concept_id") and flag.interaction_id:
                # Would need to look up concept from interaction
                pass

        # Priority 2: Uncertain mastery (0.4-0.7)
        uncertain = [(cid, m) for cid, m in mastery_data.items() if 0.4 <= m.estimate < 0.7]
        for concept_id, mastery in uncertain:
            concept_name = self.concepts.get(concept_id, concept_id)
            questions.append(
                VerificationQuestion(
                    concept_id=concept_id,
                    concept_name=concept_name,
                    question=f"Can you explain {concept_name} in your own words?",
                    rationale=f"Mastery estimate ({mastery.estimate:.0%}) is uncertain",
                    look_for="Clear explanation demonstrating conceptual understanding, "
                    "not just memorized definitions",
                    difficulty="medium",
                )
            )
            questions.append(
                VerificationQuestion(
                    concept_id=concept_id,
                    concept_name=concept_name,
                    question=f"What's a common mistake people make with {concept_name}?",
                    rationale="Tests deeper understanding beyond surface knowledge",
                    look_for="Identification of genuine misconceptions, "
                    "understanding of why the mistake occurs",
                    difficulty="medium",
                )
            )

        # Priority 3: High mastery (test transfer)
        high_mastery = [(cid, m) for cid, m in mastery_data.items() if m.estimate >= 0.8]
        for concept_id, mastery in high_mastery[:3]:  # Limit to top 3
            concept_name = self.concepts.get(concept_id, concept_id)
            questions.append(
                VerificationQuestion(
                    concept_id=concept_id,
                    concept_name=concept_name,
                    question=f"How would you apply {concept_name} to a new problem "
                    f"you haven't seen before?",
                    rationale=f"High mastery ({mastery.estimate:.0%}) - verify transfer ability",
                    look_for="Ability to apply concept flexibly, "
                    "not just repeat practiced examples",
                    difficulty="hard",
                )
            )

        # Priority 4: Low mastery (understand the gap)
        low_mastery = [(cid, m) for cid, m in mastery_data.items() if m.estimate < 0.4]
        for concept_id, mastery in low_mastery:
            concept_name = self.concepts.get(concept_id, concept_id)
            questions.append(
                VerificationQuestion(
                    concept_id=concept_id,
                    concept_name=concept_name,
                    question=f"What part of {concept_name} do you find most confusing?",
                    rationale=f"Low mastery ({mastery.estimate:.0%}) - identify specific gaps",
                    look_for="Honest self-reflection about difficulties, "
                    "specific questions rather than vague confusion",
                    difficulty="easy",
                )
            )

        return questions[:max_questions]

    def _select_key_excerpts(
        self,
        interactions: list[dict[str, Any]],
        gaming_flags: list[GamingFlag],
    ) -> list[InteractionExcerpt]:
        """
        Select revealing interactions:
        - Breakthrough moments
        - Extended struggles
        - Gaming flag triggers
        """
        excerpts = []

        # Map flags to interactions
        flagged_interaction_ids = {f.interaction_id for f in gaming_flags if f.interaction_id}

        # Find interactions with flags
        for interaction in interactions:
            if interaction.get("id") in flagged_interaction_ids:
                flag = next(
                    (f for f in gaming_flags if f.interaction_id == interaction.get("id")),
                    None,
                )
                if flag:
                    excerpts.append(
                        InteractionExcerpt(
                            type="gaming_flag",
                            concept_id=interaction.get("concept_id"),
                            interactions=[
                                {
                                    "student_message": interaction.get("student_message", ""),
                                    "tutor_response": interaction.get("tutor_response", ""),
                                    "timestamp": interaction.get("timestamp", ""),
                                }
                            ],
                            note=f"Flagged for {flag.type}: {flag.evidence}",
                            timestamp=flag.timestamp,
                        )
                    )

        # Look for struggle patterns (multiple incorrect in a row)
        struggle_start = None
        struggle_interactions = []

        for i, interaction in enumerate(interactions):
            quality = interaction.get("response_quality")
            if quality in ("incorrect", "partial"):
                if struggle_start is None:
                    struggle_start = i
                struggle_interactions.append(interaction)
            else:
                if len(struggle_interactions) >= 3:
                    excerpts.append(
                        InteractionExcerpt(
                            type="struggle",
                            concept_id=struggle_interactions[0].get("concept_id"),
                            interactions=[
                                {
                                    "student_message": inter.get("student_message", ""),
                                    "tutor_response": inter.get("tutor_response", ""),
                                }
                                for inter in struggle_interactions[:5]
                            ],
                            note=f"Extended struggle ({len(struggle_interactions)} interactions)",
                        )
                    )
                struggle_start = None
                struggle_interactions = []

        # Limit excerpts
        return excerpts[:10]

    def format_for_display(self, report: VerificationReport) -> str:
        """Format report as readable text for display."""
        lines = [
            "# Verification Report",
            f"Student: {report.student_id}",
            f"Course: {self.course_name}",
            f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Summary",
            f"- Overall Mastery: {report.summary['overall_mastery']:.0%}",
            f"- Concepts Mastered: {report.summary['mastered_concepts']}/{report.summary['total_concepts']}",
            f"- Total Interactions: {report.summary['total_interactions']}",
            f"- Total Time: {report.summary['total_time_minutes']:.0f} minutes",
            f"- Gaming Flags: {report.summary['gaming_flags_count']} ({report.summary['high_severity_flags']} high severity)",
            "",
        ]

        if report.summary["needs_attention"]:
            lines.append("**ATTENTION NEEDED: Significant concerns detected**")
            lines.append("")

        lines.append("## Mastery by Concept")
        for m in report.mastery_by_concept:
            status_emoji = {
                "mastered": "V",
                "proficient": "~",
                "developing": "?",
                "struggling": "X",
            }.get(m["status"], "?")
            lines.append(
                f"[{status_emoji}] {m['concept_name']}: {m['estimate']:.0%} "
                f"(confidence: {m['confidence']:.0%})"
            )

        if report.concerns:
            lines.append("")
            lines.append("## Concerns")
            for concern in report.concerns:
                lines.append(f"- [{concern.severity.upper()}] {concern.type}: {concern.evidence}")

        lines.append("")
        lines.append("## Recommended Verification Questions")
        for i, q in enumerate(report.recommended_questions, 1):
            lines.append(f"{i}. [{q.difficulty}] {q.question}")
            lines.append(f"   Rationale: {q.rationale}")
            lines.append(f"   Look for: {q.look_for}")
            lines.append("")

        return "\n".join(lines)
