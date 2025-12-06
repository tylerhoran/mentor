"""
Response generation with prompt assembly.

Generates system prompts from course configuration and
manages response generation with appropriate context.
"""

from typing import Any

from mentor.core.course_definition.misconceptions import MisconceptionLibrary
from mentor.core.course_definition.pedagogy_config import PedagogyConfig


class PromptAssembler:
    """
    Generate system prompts from course configuration.

    Assembles:
    - Role and persona
    - Pedagogical instructions
    - Domain knowledge summary
    - Misconception awareness
    - Boundaries and constraints
    """

    def __init__(
        self,
        course_name: str,
        course_description: str | None = None,
    ):
        """
        Initialize the prompt assembler.

        Args:
            course_name: Name of the course
            course_description: Optional course description
        """
        self.course_name = course_name
        self.course_description = course_description

    def build_system_prompt(
        self,
        pedagogy_config: PedagogyConfig,
        misconception_library: MisconceptionLibrary | None = None,
        current_concept_name: str | None = None,
        additional_context: str | None = None,
    ) -> str:
        """
        Generate complete system prompt from course config.

        Structure:
        1. Role definition
        2. Course context
        3. Pedagogical approach
        4. Response patterns for situations
        5. Misconception awareness
        6. Hard boundaries (never/always)
        7. Voice/tone

        Args:
            pedagogy_config: Pedagogical configuration
            misconception_library: Optional misconception library
            current_concept_name: Current concept being taught
            additional_context: Any additional context to include

        Returns:
            Complete system prompt string
        """
        sections = [
            self._build_role_section(),
            self._build_course_section(),
        ]

        if current_concept_name:
            sections.append(self._build_concept_section(current_concept_name))

        sections.append(pedagogy_config.to_system_prompt_section())

        if misconception_library:
            misconception_section = self._build_misconception_section(
                misconception_library, current_concept_name
            )
            if misconception_section:
                sections.append(misconception_section)

        if additional_context:
            sections.append(f"## Additional Context\n{additional_context}")

        return "\n\n".join(sections)

    def _build_role_section(self) -> str:
        """Build the role definition section."""
        return f"""# Role

You are an AI tutor for the course "{self.course_name}". Your purpose is to help students learn and understand the course material through guided interaction.

You are NOT:
- A homework solver
- An answer provider
- A replacement for actual learning

You ARE:
- A patient guide
- A Socratic questioner
- A scaffold builder
- An encourager of deep understanding"""

    def _build_course_section(self) -> str:
        """Build the course context section."""
        section = f"## Course Context\n\nCourse: {self.course_name}"
        if self.course_description:
            section += f"\n\n{self.course_description}"
        return section

    def _build_concept_section(self, concept_name: str) -> str:
        """Build section for current concept focus."""
        return f"""## Current Focus

The student is currently working on: **{concept_name}**

Focus your responses on this concept and its prerequisites. If the student asks about unrelated topics, gently redirect them back to the current learning objective."""

    def _build_misconception_section(
        self,
        library: MisconceptionLibrary,
        concept_id: str | None,
    ) -> str | None:
        """Build misconception awareness section."""
        if not concept_id:
            return None

        misconceptions = library.get_for_concept(concept_id)
        if not misconceptions:
            return None

        lines = [
            "## Common Misconceptions",
            "",
            "Be aware of these common misconceptions for this topic:",
            "",
        ]

        for m in misconceptions:
            lines.append(f"### {m.name}")
            lines.append(f"{m.description}")
            if m.manifestation:
                lines.append(f"\nHow it appears: {m.manifestation}")
            if m.correction_approach:
                lines.append(f"\nHow to address: {m.correction_approach}")
            lines.append("")

        return "\n".join(lines)


class ResponseGenerator:
    """
    High-level response generation coordinating all components.
    """

    def __init__(
        self,
        course_name: str,
        course_description: str | None,
        pedagogy_config: PedagogyConfig,
        misconception_library: MisconceptionLibrary | None = None,
    ):
        """
        Initialize the response generator.

        Args:
            course_name: Course name
            course_description: Course description
            pedagogy_config: Pedagogical configuration
            misconception_library: Optional misconception library
        """
        self.prompt_assembler = PromptAssembler(course_name, course_description)
        self.pedagogy_config = pedagogy_config
        self.misconception_library = misconception_library

    def get_system_prompt(
        self,
        current_concept_name: str | None = None,
        additional_context: str | None = None,
    ) -> str:
        """
        Get the system prompt for the current tutoring context.

        Args:
            current_concept_name: Current concept being taught
            additional_context: Any additional context

        Returns:
            Complete system prompt
        """
        return self.prompt_assembler.build_system_prompt(
            pedagogy_config=self.pedagogy_config,
            misconception_library=self.misconception_library,
            current_concept_name=current_concept_name,
            additional_context=additional_context,
        )

    def format_response_with_metadata(
        self,
        response: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Format response with associated metadata.

        Args:
            response: The tutor's response text
            metadata: Response metadata (move, concept, etc.)

        Returns:
            Formatted response dict
        """
        return {
            "response": response,
            "metadata": metadata,
        }
