"""
Track and estimate student mastery per concept.

Uses Bayesian Knowledge Tracing variant:
- Prior from prerequisites
- Updates based on interaction quality
- Confidence increases with more data
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from mentor.core.course_definition.knowledge_graph import KnowledgeGraph


@dataclass
class MasteryEstimate:
    """Estimate of mastery for a single concept."""

    estimate: float = 0.0  # 0.0 to 1.0
    confidence: float = 0.0  # 0.0 to 1.0
    interaction_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "estimate": self.estimate,
            "confidence": self.confidence,
            "interactions": self.interaction_count,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MasteryEstimate":
        """Create from dictionary."""
        last_updated = data.get("last_updated")
        if isinstance(last_updated, str):
            last_updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        elif last_updated is None:
            last_updated = datetime.now(timezone.utc)

        return cls(
            estimate=data.get("estimate", 0.0),
            confidence=data.get("confidence", 0.0),
            interaction_count=data.get("interactions", 0),
            last_updated=last_updated,
        )


class MasteryTracker:
    """
    Track student mastery across concepts using Bayesian Knowledge Tracing.

    The tracker maintains probability estimates of mastery for each concept
    and updates them based on student performance on interactions.
    """

    # Bayesian Knowledge Tracing parameters
    P_INIT = 0.1  # Initial probability of mastery
    P_LEARN = 0.3  # Probability of learning on each opportunity
    P_FORGET = 0.01  # Probability of forgetting
    P_SLIP = 0.1  # Probability of slipping (correct -> incorrect)
    P_GUESS = 0.2  # Probability of guessing correctly

    def __init__(self, knowledge_graph: KnowledgeGraph | None = None):
        """
        Initialize the mastery tracker.

        Args:
            knowledge_graph: Knowledge graph for prerequisite relationships
        """
        self.graph = knowledge_graph
        self._mastery: dict[str, MasteryEstimate] = {}

    def get_mastery(self, concept_id: str) -> MasteryEstimate:
        """Get mastery estimate for a concept."""
        if concept_id not in self._mastery:
            # Initialize with prior from prerequisites
            prior = self._calculate_prior(concept_id)
            self._mastery[concept_id] = MasteryEstimate(
                estimate=prior,
                confidence=0.1,  # Low confidence initially
            )
        return self._mastery[concept_id]

    def _calculate_prior(self, concept_id: str) -> float:
        """
        Calculate prior probability of mastery based on prerequisites.

        If all prerequisites are mastered, prior is higher.
        """
        if not self.graph:
            return self.P_INIT

        concept = self.graph.get_concept(concept_id)
        if not concept or not concept.prerequisites:
            return self.P_INIT

        # Average mastery of prerequisites
        prereq_mastery = []
        for prereq_id in concept.prerequisites:
            if prereq_id in self._mastery:
                prereq_mastery.append(self._mastery[prereq_id].estimate)

        if not prereq_mastery:
            return self.P_INIT

        avg_prereq = sum(prereq_mastery) / len(prereq_mastery)
        # Prior is influenced by prerequisite mastery
        return self.P_INIT + (avg_prereq * 0.3)

    def update_mastery(
        self,
        concept_id: str,
        interaction_quality: str,  # 'correct', 'partial', 'incorrect'
        interaction_type: str = "practice",  # 'practice', 'probe', 'application'
    ) -> MasteryEstimate:
        """
        Bayesian update of mastery estimate.

        Args:
            concept_id: The concept being practiced
            interaction_quality: Quality of student response
            interaction_type: Type of interaction (probes weight more)

        Returns:
            Updated mastery estimate
        """
        current = self.get_mastery(concept_id)
        p_mastery = current.estimate

        # Determine if "correct"
        is_correct = interaction_quality in ("correct", "partial")

        # Weight multiplier for interaction type
        weight = 1.0
        if interaction_type == "probe":
            weight = 1.5  # Probes are more indicative
        elif interaction_type == "application":
            weight = 2.0  # Application/transfer is most indicative

        # Bayesian update
        if is_correct:
            # P(mastery | correct) using Bayes' rule
            p_correct_given_mastery = 1 - self.P_SLIP
            p_correct_given_no_mastery = self.P_GUESS
            p_correct = p_correct_given_mastery * p_mastery + p_correct_given_no_mastery * (
                1 - p_mastery
            )
            new_mastery = (p_correct_given_mastery * p_mastery) / p_correct

            # Apply learning update
            new_mastery = new_mastery + (1 - new_mastery) * self.P_LEARN * weight

            # Partial credit adjustment
            if interaction_quality == "partial":
                new_mastery *= 0.8
        else:
            # P(mastery | incorrect)
            p_incorrect_given_mastery = self.P_SLIP
            p_incorrect_given_no_mastery = 1 - self.P_GUESS
            p_incorrect = p_incorrect_given_mastery * p_mastery + p_incorrect_given_no_mastery * (
                1 - p_mastery
            )
            new_mastery = (p_incorrect_given_mastery * p_mastery) / p_incorrect

        # Clamp to valid range
        new_mastery = max(0.0, min(1.0, new_mastery))

        # Update confidence based on interaction count
        new_interaction_count = current.interaction_count + 1
        # Confidence increases with more data, asymptoting to 1
        new_confidence = 1 - (1 / (1 + new_interaction_count * 0.2))

        # Create updated estimate
        updated = MasteryEstimate(
            estimate=new_mastery,
            confidence=new_confidence,
            interaction_count=new_interaction_count,
            last_updated=datetime.now(timezone.utc),
        )

        self._mastery[concept_id] = updated
        return updated

    def apply_decay(self, concept_id: str, days_since_practice: int) -> MasteryEstimate:
        """
        Apply forgetting decay to mastery estimate.

        Args:
            concept_id: The concept
            days_since_practice: Days since last practice

        Returns:
            Decayed mastery estimate
        """
        current = self.get_mastery(concept_id)

        # Apply exponential decay
        decay_rate = self.P_FORGET * days_since_practice
        new_mastery = current.estimate * (1 - decay_rate)
        new_mastery = max(self.P_INIT, new_mastery)  # Don't decay below initial

        updated = MasteryEstimate(
            estimate=new_mastery,
            confidence=current.confidence * 0.95,  # Confidence also decays slightly
            interaction_count=current.interaction_count,
            last_updated=current.last_updated,
        )

        self._mastery[concept_id] = updated
        return updated

    def is_mastered(self, concept_id: str, threshold: float = 0.8) -> bool:
        """Check if a concept is considered mastered."""
        mastery = self.get_mastery(concept_id)
        return mastery.estimate >= threshold and mastery.confidence >= 0.5

    def get_all_mastery(self) -> dict[str, MasteryEstimate]:
        """Get all mastery estimates."""
        return self._mastery.copy()

    def load_from_dict(self, data: dict[str, dict[str, Any]]) -> None:
        """Load mastery data from dictionary (from database)."""
        for concept_id, mastery_data in data.items():
            self._mastery[concept_id] = MasteryEstimate.from_dict(mastery_data)

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Convert all mastery data to dictionary for storage."""
        return {cid: m.to_dict() for cid, m in self._mastery.items()}

    def get_overall_mastery(self) -> float:
        """Get average mastery across all concepts."""
        if not self._mastery:
            return 0.0
        estimates = [m.estimate for m in self._mastery.values()]
        return sum(estimates) / len(estimates)

    def get_weakest_concepts(self, n: int = 5) -> list[str]:
        """Get the n concepts with lowest mastery."""
        sorted_concepts = sorted(
            self._mastery.items(),
            key=lambda x: x[1].estimate,
        )
        return [cid for cid, _ in sorted_concepts[:n]]

    def get_ready_for_review(self, days_threshold: int = 7) -> list[str]:
        """Get concepts that haven't been practiced recently."""
        now = datetime.now(timezone.utc)
        ready = []

        for concept_id, mastery in self._mastery.items():
            days_since = (now - mastery.last_updated).days
            if days_since >= days_threshold and mastery.estimate < 0.95:
                ready.append(concept_id)

        return ready
