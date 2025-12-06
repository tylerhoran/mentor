"""
Central student state management.

Coordinates:
- Mastery tracking
- Engagement metrics
- Gaming flags
- Progress tracking
"""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from mentor.core.course_definition.knowledge_graph import KnowledgeGraph
from mentor.core.student_state.engagement_metrics import EngagementTracker
from mentor.core.student_state.mastery_tracker import MasteryEstimate, MasteryTracker


class StudentStateManager:
    """
    Manages all aspects of student state within a course.

    Provides a unified interface for:
    - Tracking mastery across concepts
    - Recording engagement metrics
    - Managing gaming flags
    - Determining next steps
    """

    def __init__(
        self,
        student_id: str,
        course_id: str,
        knowledge_graph: KnowledgeGraph | None = None,
    ):
        """
        Initialize the state manager.

        Args:
            student_id: The student's ID
            course_id: The course ID
            knowledge_graph: Course knowledge graph for prerequisites
        """
        self.student_id = student_id
        self.course_id = course_id
        self.knowledge_graph = knowledge_graph

        # Component trackers
        self.mastery_tracker = MasteryTracker(knowledge_graph)
        self.engagement_tracker = EngagementTracker()

        # State
        self.current_concept_id: str | None = None
        self.concepts_completed: list[str] = []
        self.gaming_flags: list[dict[str, Any]] = []

    def load_state(self, state_data: dict[str, Any]) -> None:
        """
        Load state from database record.

        Args:
            state_data: State data from StudentState model
        """
        # Load mastery
        if "concept_mastery" in state_data:
            self.mastery_tracker.load_from_dict(state_data["concept_mastery"])

        # Load engagement
        if "engagement_metrics" in state_data:
            self.engagement_tracker.load_metrics(state_data["engagement_metrics"])

        # Load other state
        self.current_concept_id = state_data.get("current_concept_id")
        self.concepts_completed = state_data.get("concepts_completed", [])
        self.gaming_flags = state_data.get("gaming_flags", [])

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for storage."""
        return {
            "concept_mastery": self.mastery_tracker.to_dict(),
            "engagement_metrics": self.engagement_tracker.get_metrics().to_dict(),
            "current_concept_id": self.current_concept_id,
            "concepts_completed": self.concepts_completed,
            "gaming_flags": self.gaming_flags,
        }

    # Session management
    def start_session(self, session_id: str) -> None:
        """Start a new tutoring session."""
        self.engagement_tracker.start_session(session_id)

    def end_session(self) -> dict[str, Any]:
        """End the current session and return summary."""
        session = self.engagement_tracker.end_session()
        return {
            "duration_seconds": session.duration_seconds if session else 0,
            "interaction_count": session.interaction_count if session else 0,
            "concepts_covered": session.concepts_covered if session else [],
        }

    # Interaction recording
    def record_interaction(
        self,
        concept_id: str | None,
        interaction_quality: str,
        interaction_type: str = "practice",
        response_time_ms: int | None = None,
        gaming_signals: list[dict[str, Any]] | None = None,
    ) -> MasteryEstimate | None:
        """
        Record an interaction and update state.

        Args:
            concept_id: Concept being practiced
            interaction_quality: Quality of response (correct, partial, incorrect)
            interaction_type: Type of interaction (practice, probe, application)
            response_time_ms: Time student took to respond
            gaming_signals: Any gaming signals detected

        Returns:
            Updated mastery estimate if concept provided
        """
        # Record engagement
        self.engagement_tracker.record_interaction(
            response_time_ms=response_time_ms,
            concept_id=concept_id,
        )

        # Update mastery
        updated_mastery = None
        if concept_id:
            updated_mastery = self.mastery_tracker.update_mastery(
                concept_id,
                interaction_quality,
                interaction_type,
            )

            # Check if concept is now mastered
            if self.mastery_tracker.is_mastered(concept_id):
                if concept_id not in self.concepts_completed:
                    self.concepts_completed.append(concept_id)

        # Record gaming signals
        if gaming_signals:
            for signal in gaming_signals:
                self.add_gaming_flag(
                    flag_type=signal.get("type", "unknown"),
                    severity=signal.get("severity", "low"),
                    evidence=signal.get("evidence", ""),
                )

        return updated_mastery

    # Mastery queries
    def get_mastery(self, concept_id: str) -> MasteryEstimate:
        """Get mastery estimate for a concept."""
        return self.mastery_tracker.get_mastery(concept_id)

    def get_overall_mastery(self) -> float:
        """Get average mastery across all practiced concepts."""
        return self.mastery_tracker.get_overall_mastery()

    def get_ready_concepts(self) -> list[str]:
        """Get concepts ready to learn (prerequisites met)."""
        if not self.knowledge_graph:
            return []

        mastered = set(self.concepts_completed)
        return self.knowledge_graph.get_ready_concepts(mastered)

    def get_next_concept(self) -> str | None:
        """Get recommended next concept to study."""
        if not self.knowledge_graph:
            return None

        mastered = set(self.concepts_completed)
        return self.knowledge_graph.get_next_concept(mastered)

    # Current concept management
    def set_current_concept(self, concept_id: str) -> None:
        """Set the current concept being studied."""
        self.current_concept_id = concept_id

    def advance_to_next_concept(self) -> str | None:
        """Advance to the next recommended concept."""
        next_concept = self.get_next_concept()
        if next_concept:
            self.current_concept_id = next_concept
        return next_concept

    # Gaming flags
    def add_gaming_flag(
        self,
        flag_type: str,
        severity: str,
        evidence: str,
        interaction_id: str | None = None,
    ) -> None:
        """Add a gaming flag."""
        self.gaming_flags.append(
            {
                "type": flag_type,
                "severity": severity,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "evidence": evidence,
                "interaction_id": interaction_id,
                "resolved": False,
            }
        )

    def resolve_gaming_flag(self, index: int, resolution_note: str = "") -> bool:
        """Mark a gaming flag as resolved."""
        if 0 <= index < len(self.gaming_flags):
            self.gaming_flags[index]["resolved"] = True
            self.gaming_flags[index]["resolution_note"] = resolution_note
            self.gaming_flags[index]["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return True
        return False

    def get_unresolved_flags(self) -> list[dict[str, Any]]:
        """Get unresolved gaming flags."""
        return [f for f in self.gaming_flags if not f.get("resolved", False)]

    def get_high_severity_flags(self) -> list[dict[str, Any]]:
        """Get unresolved high severity flags."""
        return [
            f
            for f in self.gaming_flags
            if f.get("severity") == "high" and not f.get("resolved", False)
        ]

    @property
    def has_gaming_concerns(self) -> bool:
        """Check if student has significant gaming concerns."""
        unresolved = self.get_unresolved_flags()
        high_severity = self.get_high_severity_flags()
        return len(high_severity) >= 2 or len(unresolved) >= 5

    # Progress summary
    def get_progress_summary(self) -> dict[str, Any]:
        """Get a comprehensive progress summary."""
        metrics = self.engagement_tracker.get_metrics()
        total_concepts = len(self.knowledge_graph.get_all_concepts()) if self.knowledge_graph else 0

        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "overall_mastery": self.get_overall_mastery(),
            "concepts_completed": len(self.concepts_completed),
            "total_concepts": total_concepts,
            "completion_percentage": (
                (len(self.concepts_completed) / total_concepts * 100) if total_concepts > 0 else 0
            ),
            "current_concept_id": self.current_concept_id,
            "total_interactions": metrics.total_interactions,
            "total_time_minutes": metrics.total_time_minutes,
            "session_count": metrics.session_count,
            "engagement_score": self.engagement_tracker.get_engagement_score(),
            "gaming_flags_count": len(self.get_unresolved_flags()),
            "has_gaming_concerns": self.has_gaming_concerns,
            "last_active": metrics.last_session_at.isoformat() if metrics.last_session_at else None,
        }

    # Recommendations
    def get_recommendations(self) -> dict[str, Any]:
        """Get study recommendations based on current state."""
        recommendations = {
            "next_concept": self.get_next_concept(),
            "concepts_to_review": [],
            "weakest_concepts": [],
            "ready_to_advance": False,
        }

        # Get concepts needing review
        if self.mastery_tracker:
            recommendations["concepts_to_review"] = self.mastery_tracker.get_ready_for_review()
            recommendations["weakest_concepts"] = self.mastery_tracker.get_weakest_concepts(3)

        # Check if ready to advance
        if self.current_concept_id:
            if self.mastery_tracker.is_mastered(self.current_concept_id):
                recommendations["ready_to_advance"] = True

        return recommendations
