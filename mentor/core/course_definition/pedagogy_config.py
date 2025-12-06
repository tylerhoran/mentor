"""
Faculty pedagogical preferences and constraints.

Configures:
- Teaching style (Socratic, guided discovery, direct instruction)
- Response patterns for different situations
- Hard boundaries (never give direct answers, etc.)
- Voice and tone
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import yaml


class TeachingStyle(str, Enum):
    """Available teaching styles."""

    SOCRATIC = "socratic"
    GUIDED_DISCOVERY = "guided_discovery"
    DIRECT_INSTRUCTION = "direct_instruction"
    WORKED_EXAMPLES = "worked_examples"


@dataclass
class ResponsePattern:
    """Pattern for responding to specific situations."""

    situation: str  # e.g., "student_stuck", "student_wrong", "asks_for_answer"
    strategies: list[str] = field(default_factory=list)  # Ordered list of approaches

    def to_dict(self) -> dict[str, Any]:
        return {"situation": self.situation, "strategies": self.strategies}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResponsePattern":
        return cls(
            situation=data["situation"],
            strategies=data.get("strategies", []),
        )


@dataclass
class PedagogyConfig:
    """
    Pedagogical configuration for a course.

    This configuration determines how the AI tutor behaves,
    what teaching strategies it uses, and what boundaries it respects.
    """

    style: TeachingStyle = TeachingStyle.SOCRATIC
    response_patterns: list[ResponsePattern] = field(default_factory=list)
    never_do: list[str] = field(default_factory=list)  # Hard constraints
    always_do: list[str] = field(default_factory=list)  # Required behaviors
    voice_description: str | None = None  # Tone/personality

    # Tuning parameters
    hint_progression: list[str] = field(default_factory=list)  # How hints escalate
    max_hints_before_direct: int = 5
    probe_on_correct: bool = True  # Verify understanding even when right
    encourage_after_struggle: bool = True
    max_response_length: int = 500  # Approximate word limit

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "style": self.style.value,
            "response_patterns": [p.to_dict() for p in self.response_patterns],
            "never_do": self.never_do,
            "always_do": self.always_do,
            "voice_description": self.voice_description,
            "hint_progression": self.hint_progression,
            "max_hints_before_direct": self.max_hints_before_direct,
            "probe_on_correct": self.probe_on_correct,
            "encourage_after_struggle": self.encourage_after_struggle,
            "max_response_length": self.max_response_length,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PedagogyConfig":
        """Create from dictionary."""
        style = data.get("style", "socratic")
        if isinstance(style, str):
            style = TeachingStyle(style)

        return cls(
            style=style,
            response_patterns=[
                ResponsePattern.from_dict(p) for p in data.get("response_patterns", [])
            ],
            never_do=data.get("never_do", []),
            always_do=data.get("always_do", []),
            voice_description=data.get("voice_description"),
            hint_progression=data.get("hint_progression", []),
            max_hints_before_direct=data.get("max_hints_before_direct", 5),
            probe_on_correct=data.get("probe_on_correct", True),
            encourage_after_struggle=data.get("encourage_after_struggle", True),
            max_response_length=data.get("max_response_length", 500),
        )

    def get_pattern_for_situation(self, situation: str) -> ResponsePattern | None:
        """Get the response pattern for a specific situation."""
        for pattern in self.response_patterns:
            if pattern.situation == situation:
                return pattern
        return None

    def to_system_prompt_section(self) -> str:
        """Convert config to system prompt text."""
        sections = []

        # Teaching style
        style_descriptions = {
            TeachingStyle.SOCRATIC: (
                "Use the Socratic method. Ask guiding questions rather than giving direct answers. "
                "Help students discover insights themselves through carefully crafted questions."
            ),
            TeachingStyle.GUIDED_DISCOVERY: (
                "Guide students through discovery. Provide hints and scaffolding while letting "
                "students work through problems. Balance guidance with student autonomy."
            ),
            TeachingStyle.DIRECT_INSTRUCTION: (
                "Provide clear, direct explanations when needed. Focus on clarity and "
                "comprehensiveness while still checking for understanding."
            ),
            TeachingStyle.WORKED_EXAMPLES: (
                "Use worked examples extensively. Walk through similar problems step by step, "
                "then have students try variations with decreasing guidance."
            ),
        }
        sections.append(f"## Teaching Approach\n{style_descriptions[self.style]}")

        # Response patterns
        if self.response_patterns:
            patterns_text = ["## Response Patterns"]
            for pattern in self.response_patterns:
                patterns_text.append(f"\nWhen {pattern.situation}:")
                for i, strategy in enumerate(pattern.strategies, 1):
                    patterns_text.append(f"  {i}. {strategy}")
            sections.append("\n".join(patterns_text))

        # Boundaries - Never do
        if self.never_do:
            never_text = ["## Boundaries - NEVER do the following:"]
            for item in self.never_do:
                never_text.append(f"- {item}")
            sections.append("\n".join(never_text))

        # Boundaries - Always do
        if self.always_do:
            always_text = ["## Required Behaviors - ALWAYS:"]
            for item in self.always_do:
                always_text.append(f"- {item}")
            sections.append("\n".join(always_text))

        # Hint progression
        if self.hint_progression:
            hints_text = [
                "## Hint Progression",
                "When a student is stuck, progress through hints in this order:",
            ]
            for i, hint in enumerate(self.hint_progression, 1):
                hints_text.append(f"  {i}. {hint}")
            hints_text.append(
                f"\nAfter {self.max_hints_before_direct} unsuccessful hints, "
                "you may provide more direct guidance."
            )
            sections.append("\n".join(hints_text))

        # Probing
        if self.probe_on_correct:
            sections.append(
                "## Verification\n"
                "When a student gives a correct answer, ask follow-up questions to verify "
                "genuine understanding. Don't just accept correct answers at face value."
            )

        # Voice/Tone
        if self.voice_description:
            sections.append(f"## Voice and Tone\n{self.voice_description}")

        return "\n\n".join(sections)

    def to_yaml(self) -> str:
        """Export as YAML."""
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "PedagogyConfig":
        """Import from YAML."""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data)

    @classmethod
    def default_socratic(cls) -> "PedagogyConfig":
        """Create a default Socratic configuration."""
        return cls(
            style=TeachingStyle.SOCRATIC,
            response_patterns=[
                ResponsePattern(
                    situation="student_stuck",
                    strategies=[
                        "Ask what they've tried so far",
                        "Break the problem into smaller steps",
                        "Provide a simpler analogous example",
                        "Ask about specific concepts involved",
                    ],
                ),
                ResponsePattern(
                    situation="student_wrong",
                    strategies=[
                        "Ask them to explain their reasoning",
                        "Identify the specific misconception",
                        "Guide toward contradiction rather than stating error",
                        "Provide a counterexample to consider",
                    ],
                ),
                ResponsePattern(
                    situation="asks_for_answer",
                    strategies=[
                        "Redirect: 'Let's work through it together'",
                        "Ask what specific part is confusing",
                        "Provide a hint rather than the solution",
                        "Offer to solve a similar but different problem first",
                    ],
                ),
                ResponsePattern(
                    situation="correct_answer",
                    strategies=[
                        "Acknowledge the correct answer",
                        "Ask them to explain why it's correct",
                        "Pose a follow-up question to deepen understanding",
                        "Connect to related concepts",
                    ],
                ),
            ],
            never_do=[
                "Provide complete solutions to assigned problems",
                "Write code the student should write themselves",
                "Skip steps in explanations",
                "Give up on a student",
                "Be condescending or dismissive",
                "Reveal answers when student asks directly",
            ],
            always_do=[
                "Require student to articulate understanding",
                "Check for understanding before advancing",
                "Connect new concepts to previously mastered ones",
                "Acknowledge good reasoning even in wrong answers",
                "Be patient and encouraging",
                "Adapt explanations to student's level",
            ],
            voice_description=(
                "Warm, patient, intellectually curious. You genuinely enjoy helping "
                "students understand. You believe every student can master this material "
                "with the right support. You celebrate small wins and maintain optimism "
                "even when students struggle."
            ),
            hint_progression=[
                "Ask a clarifying question about their understanding",
                "Point them to a relevant concept or formula",
                "Provide a small hint about the first step",
                "Work through a simpler example together",
                "Provide more direct guidance on approach",
            ],
            max_hints_before_direct=5,
            probe_on_correct=True,
        )
