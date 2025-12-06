"""
Misconception documentation and matching.

Faculty document common student misconceptions.
System uses these to:
- Identify misconceptions in student responses
- Generate diagnostic questions
- Apply appropriate correction strategies
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from mentor.core.tutor_runtime.llm_client import LLMClient


@dataclass
class Misconception:
    """A documented misconception for a concept."""

    id: str
    concept_id: str
    name: str
    description: str
    manifestation: str = ""  # How it appears in student work
    diagnostic_question: str = ""  # Question to confirm misconception
    correction_approach: str = ""  # Pedagogical strategy
    example_student_response: str | None = None
    example_tutor_response: str | None = None
    times_observed: int = 0
    times_resolved: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "concept_id": self.concept_id,
            "name": self.name,
            "description": self.description,
            "manifestation": self.manifestation,
            "diagnostic_question": self.diagnostic_question,
            "correction_approach": self.correction_approach,
            "example_student_response": self.example_student_response,
            "example_tutor_response": self.example_tutor_response,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Misconception":
        """Create from dictionary."""
        return cls(
            id=data.get("id", ""),
            concept_id=data.get("concept_id", ""),
            name=data["name"],
            description=data["description"],
            manifestation=data.get("manifestation", ""),
            diagnostic_question=data.get("diagnostic_question", ""),
            correction_approach=data.get("correction_approach", ""),
            example_student_response=data.get("example_student_response"),
            example_tutor_response=data.get("example_tutor_response"),
        )


class MisconceptionLibrary:
    """
    Library of misconceptions for a course.

    Provides functionality to:
    - Store and retrieve misconceptions by concept
    - Detect misconceptions in student responses using LLM
    - Generate correction prompts
    """

    def __init__(self, course_id: str):
        """Initialize an empty misconception library."""
        self.course_id = course_id
        self._misconceptions: dict[str, list[Misconception]] = {}  # concept_id -> list

    def add_misconception(self, misconception: Misconception) -> None:
        """Add a misconception to the library."""
        concept_id = misconception.concept_id
        if concept_id not in self._misconceptions:
            self._misconceptions[concept_id] = []
        self._misconceptions[concept_id].append(misconception)

    def remove_misconception(self, misconception_id: str) -> bool:
        """Remove a misconception by ID."""
        for concept_id, misconceptions in self._misconceptions.items():
            for i, m in enumerate(misconceptions):
                if m.id == misconception_id:
                    del misconceptions[i]
                    return True
        return False

    def get_misconception(self, misconception_id: str) -> Misconception | None:
        """Get a misconception by ID."""
        for misconceptions in self._misconceptions.values():
            for m in misconceptions:
                if m.id == misconception_id:
                    return m
        return None

    def get_for_concept(self, concept_id: str) -> list[Misconception]:
        """Get all misconceptions for a concept."""
        return self._misconceptions.get(concept_id, [])

    def get_all(self) -> list[Misconception]:
        """Get all misconceptions in the library."""
        all_misconceptions = []
        for misconceptions in self._misconceptions.values():
            all_misconceptions.extend(misconceptions)
        return all_misconceptions

    async def detect_misconception(
        self,
        student_response: str,
        concept_id: str,
        llm_client: "LLMClient",
        conversation_context: str = "",
    ) -> Misconception | None:
        """
        Use LLM to identify if response matches known misconception.

        Args:
            student_response: The student's message
            concept_id: The current concept being discussed
            llm_client: LLM client for detection
            conversation_context: Recent conversation for context

        Returns:
            The detected misconception, or None if no match
        """
        misconceptions = self.get_for_concept(concept_id)
        if not misconceptions:
            return None

        # Build prompt for misconception detection
        misconception_descriptions = "\n".join(
            [
                f"- {m.name}: {m.description}\n  Manifestation: {m.manifestation}"
                for m in misconceptions
            ]
        )

        prompt = f"""Analyze the student's response for potential misconceptions.

Context: {conversation_context}

Student response: "{student_response}"

Known misconceptions for this concept:
{misconception_descriptions}

Does the student's response indicate any of these misconceptions?
If yes, respond with ONLY the name of the misconception.
If no clear misconception is detected, respond with "NONE".
"""

        messages = [{"role": "user", "content": prompt}]
        response = await llm_client.generate(
            messages=messages,
            system_prompt="You are a misconception detection system. Be precise and conservative - only identify a misconception if there is clear evidence.",
            temperature=0.1,
            max_tokens=100,
        )

        # Parse response
        response_text = response.strip().upper() if isinstance(response, str) else ""
        if response_text == "NONE" or not response_text:
            return None

        # Find matching misconception
        for misconception in misconceptions:
            if misconception.name.upper() in response_text:
                return misconception

        return None

    def get_correction_prompt(self, misconception: Misconception) -> str:
        """
        Generate a prompt section for addressing this misconception.

        Returns text that can be included in the tutor's system prompt
        to guide the correction approach.
        """
        prompt_parts = [
            f"The student appears to have the '{misconception.name}' misconception.",
            f"\nDescription: {misconception.description}",
        ]

        if misconception.correction_approach:
            prompt_parts.append(f"\nRecommended approach: {misconception.correction_approach}")

        if misconception.diagnostic_question:
            prompt_parts.append(
                f"\nConsider asking this diagnostic question: {misconception.diagnostic_question}"
            )

        if misconception.example_tutor_response:
            prompt_parts.append(f"\nExample response: {misconception.example_tutor_response}")

        prompt_parts.append(
            "\nAddress this misconception gently without making the student feel bad. "
            "Guide them to discover the error themselves when possible."
        )

        return "\n".join(prompt_parts)

    def record_observation(self, misconception_id: str) -> None:
        """Record that a misconception was observed."""
        misconception = self.get_misconception(misconception_id)
        if misconception:
            misconception.times_observed += 1

    def record_resolution(self, misconception_id: str) -> None:
        """Record that a misconception was resolved."""
        misconception = self.get_misconception(misconception_id)
        if misconception:
            misconception.times_resolved += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about misconceptions."""
        all_misconceptions = self.get_all()
        total_observed = sum(m.times_observed for m in all_misconceptions)
        total_resolved = sum(m.times_resolved for m in all_misconceptions)

        return {
            "total_misconceptions": len(all_misconceptions),
            "concepts_with_misconceptions": len(self._misconceptions),
            "total_observations": total_observed,
            "total_resolutions": total_resolved,
            "resolution_rate": total_resolved / total_observed if total_observed > 0 else 0.0,
        }

    def to_yaml(self) -> str:
        """Export library as YAML."""
        data = {"misconceptions": [m.to_dict() for m in self.get_all()]}
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, course_id: str, yaml_content: str) -> "MisconceptionLibrary":
        """Import library from YAML."""
        data = yaml.safe_load(yaml_content)
        library = cls(course_id)

        for m_data in data.get("misconceptions", []):
            misconception = Misconception.from_dict(m_data)
            library.add_misconception(misconception)

        return library
