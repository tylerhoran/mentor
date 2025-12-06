"""
Core tutoring dialogue logic.

Manages:
- Conversation state
- Pedagogical move selection
- Response generation
- Interaction logging
- Gaming signal detection
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import structlog

from mentor.core.course_definition.pedagogy_config import PedagogyConfig

if TYPE_CHECKING:
    from mentor.core.assessment_engine.gaming_detector import GamingDetector
    from mentor.core.student_state.state_manager import StudentStateManager
    from mentor.core.tutor_runtime.llm_client import LLMClient
    from mentor.core.tutor_runtime.retriever import Retriever

logger = structlog.get_logger()


class PedagogicalMove(str, Enum):
    """Types of pedagogical moves the tutor can make."""

    SCAFFOLD = "scaffold"  # Break down problem
    PROBE = "probe"  # Verify understanding
    CORRECT = "correct"  # Address error
    EXPLAIN = "explain"  # Provide information
    REDIRECT = "redirect"  # Refuse to give answer
    ENCOURAGE = "encourage"  # Positive reinforcement
    ADVANCE = "advance"  # Move to next topic
    CLARIFY = "clarify"  # Ask for clarification
    EXAMPLE = "example"  # Provide an example
    HINT = "hint"  # Give a hint


class StudentMessageType(str, Enum):
    """Classification of student messages."""

    QUESTION = "question"
    ANSWER = "answer"
    CONFUSION = "confusion"
    REQUEST_ANSWER = "request_answer"
    ACKNOWLEDGMENT = "acknowledgment"
    OFF_TOPIC = "off_topic"


class DialogueManager:
    """
    Manages tutoring dialogue for a student session.

    Responsibilities:
    - Classify student messages
    - Select appropriate pedagogical moves
    - Generate contextual responses
    - Track conversation state
    - Log interactions for analysis
    """

    def __init__(
        self,
        course_id: str,
        student_id: str,
        session_id: str,
        llm_client: "LLMClient",
        retriever: "Retriever",
        state_manager: "StudentStateManager",
        gaming_detector: "GamingDetector | None",
        pedagogy_config: PedagogyConfig,
        system_prompt: str,
    ):
        """
        Initialize the dialogue manager.

        Args:
            course_id: Course ID
            student_id: Student ID
            session_id: Current session ID
            llm_client: LLM client for generation
            retriever: Retriever for course materials
            state_manager: Student state manager
            gaming_detector: Optional gaming detector
            pedagogy_config: Pedagogical configuration
            system_prompt: Base system prompt for the tutor
        """
        self.course_id = course_id
        self.student_id = student_id
        self.session_id = session_id
        self.llm_client = llm_client
        self.retriever = retriever
        self.state_manager = state_manager
        self.gaming_detector = gaming_detector
        self.pedagogy_config = pedagogy_config
        self.system_prompt = system_prompt

        # Conversation state
        self.conversation_history: list[dict[str, str]] = []
        self.current_concept_id: str | None = None
        self.hint_count: int = 0
        self.last_interaction_time: datetime | None = None

    async def respond(
        self,
        student_message: str,
        response_time_ms: int | None = None,
        stream: bool = False,
    ) -> str | AsyncGenerator[str, None]:
        """
        Generate tutoring response to student message.

        Steps:
        1. Log incoming message with timestamp
        2. Check for gaming signals
        3. Classify student message
        4. Determine pedagogical move
        5. Retrieve relevant context
        6. Generate response
        7. Update student state
        8. Log complete interaction

        Args:
            student_message: The student's message
            response_time_ms: Time student took to respond (for gaming detection)
            stream: Whether to stream the response

        Returns:
            Tutor response (string or async generator if streaming)
        """
        interaction_id = str(uuid4())
        timestamp = datetime.now(UTC)

        logger.info(
            "processing_student_message",
            session_id=self.session_id,
            interaction_id=interaction_id,
            message_length=len(student_message),
        )

        # Check for gaming signals
        gaming_flags = []
        if self.gaming_detector and response_time_ms:
            gaming_flags = await self._check_gaming_signals(student_message, response_time_ms)

        # Classify student message
        message_type = await self._classify_message(student_message)

        # Determine pedagogical move
        move = await self._determine_move(student_message, message_type, gaming_flags)

        # Retrieve relevant context
        context = await self.retriever.get_context_for_response(
            student_message,
            self.current_concept_id,
            self.conversation_history,
        )

        # Build prompt and generate response
        messages = self._build_messages(student_message, context, move, message_type)

        if stream:
            return self._stream_and_log(
                messages,
                interaction_id,
                student_message,
                move,
                message_type,
                gaming_flags,
                timestamp,
            )
        else:
            response = await self.llm_client.generate(
                messages=messages,
                system_prompt=self._build_system_prompt(move),
                temperature=0.7,
                max_tokens=1024,
            )

            # Update state and log
            await self._post_response_processing(
                interaction_id,
                student_message,
                response,
                move,
                message_type,
                gaming_flags,
                timestamp,
            )

            return response

    async def _stream_and_log(
        self,
        messages: list[dict[str, str]],
        interaction_id: str,
        student_message: str,
        move: PedagogicalMove,
        message_type: StudentMessageType,
        gaming_flags: list[dict],
        timestamp: datetime,
    ) -> AsyncGenerator[str, None]:
        """Stream response and log after completion."""
        full_response = ""

        async for chunk in await self.llm_client.generate(
            messages=messages,
            system_prompt=self._build_system_prompt(move),
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        ):
            full_response += chunk
            yield chunk

        # Log after streaming completes
        await self._post_response_processing(
            interaction_id,
            student_message,
            full_response,
            move,
            message_type,
            gaming_flags,
            timestamp,
        )

    async def _check_gaming_signals(
        self,
        student_message: str,
        response_time_ms: int,
    ) -> list[dict[str, Any]]:
        """Check for gaming signals in the interaction."""
        if not self.gaming_detector:
            return []

        # Simplified gaming check - full implementation in gaming_detector
        flags = []

        # Too fast response
        from mentor.config import settings

        if response_time_ms < settings.gaming_min_response_time_ms:
            flags.append(
                {
                    "type": "too_fast",
                    "severity": "medium",
                    "evidence": f"Response time: {response_time_ms}ms",
                }
            )

        return flags

    async def _classify_message(self, message: str) -> StudentMessageType:
        """Classify the type of student message."""
        message_lower = message.lower()

        # Check for explicit requests for answers
        answer_phrases = [
            "give me the answer",
            "just tell me",
            "what's the answer",
            "what is the answer",
            "can you just solve",
        ]
        if any(phrase in message_lower for phrase in answer_phrases):
            return StudentMessageType.REQUEST_ANSWER

        # Check for questions
        if "?" in message or any(
            message_lower.startswith(w)
            for w in [
                "what",
                "why",
                "how",
                "when",
                "where",
                "can",
                "could",
                "would",
                "is",
                "are",
                "do",
                "does",
            ]
        ):
            return StudentMessageType.QUESTION

        # Check for confusion
        confusion_phrases = [
            "i don't understand",
            "i'm confused",
            "i don't get",
            "this doesn't make sense",
            "lost",
            "help",
        ]
        if any(phrase in message_lower for phrase in confusion_phrases):
            return StudentMessageType.CONFUSION

        # Check for acknowledgment
        ack_phrases = ["ok", "okay", "i see", "got it", "thanks", "thank you", "makes sense"]
        if any(phrase in message_lower for phrase in ack_phrases):
            return StudentMessageType.ACKNOWLEDGMENT

        # Default to answer (student attempting to answer/work through problem)
        return StudentMessageType.ANSWER

    async def _determine_move(
        self,
        student_message: str,
        message_type: StudentMessageType,
        gaming_flags: list[dict],
    ) -> PedagogicalMove:
        """Select appropriate pedagogical move based on context."""
        # If student is asking for answer directly, redirect
        if message_type == StudentMessageType.REQUEST_ANSWER:
            return PedagogicalMove.REDIRECT

        # If student is confused, scaffold
        if message_type == StudentMessageType.CONFUSION:
            return PedagogicalMove.SCAFFOLD

        # If student is asking a question
        if message_type == StudentMessageType.QUESTION:
            # Could be scaffold, explain, or hint depending on question type
            if any(
                phrase in student_message.lower() for phrase in ["what is", "define", "explain"]
            ):
                return PedagogicalMove.EXPLAIN
            return PedagogicalMove.SCAFFOLD

        # If student gave an answer
        if message_type == StudentMessageType.ANSWER:
            # After a correct answer, probe or advance
            if self.pedagogy_config.probe_on_correct:
                return PedagogicalMove.PROBE
            return PedagogicalMove.ADVANCE

        # If gaming detected, probe more aggressively
        if gaming_flags and any(f["severity"] == "high" for f in gaming_flags):
            return PedagogicalMove.PROBE

        # If acknowledgment, advance
        if message_type == StudentMessageType.ACKNOWLEDGMENT:
            return PedagogicalMove.ADVANCE

        # Default to scaffold
        return PedagogicalMove.SCAFFOLD

    def _build_system_prompt(self, move: PedagogicalMove) -> str:
        """Build system prompt including pedagogical context."""
        parts = [self.system_prompt]

        # Add move-specific instructions
        move_instructions = {
            PedagogicalMove.SCAFFOLD: (
                "\n\nCurrent approach: Break down the problem into smaller, "
                "manageable steps. Guide the student through each step."
            ),
            PedagogicalMove.PROBE: (
                "\n\nCurrent approach: Ask follow-up questions to verify "
                "understanding. Don't assume the student understands just "
                "because they gave a correct answer."
            ),
            PedagogicalMove.CORRECT: (
                "\n\nCurrent approach: The student made an error. Help them "
                "identify and correct it without directly stating what's wrong. "
                "Guide them to discover the mistake themselves."
            ),
            PedagogicalMove.REDIRECT: (
                "\n\nCurrent approach: The student is asking for a direct answer. "
                "Redirect them to work through the problem. Offer to help them "
                "understand, not to do it for them."
            ),
            PedagogicalMove.EXPLAIN: (
                "\n\nCurrent approach: Provide a clear explanation of the concept. "
                "Use examples and analogies. Check for understanding afterward."
            ),
            PedagogicalMove.HINT: (
                "\n\nCurrent approach: Provide a helpful hint without giving away "
                "the answer. Point them in the right direction."
            ),
        }

        if move in move_instructions:
            parts.append(move_instructions[move])

        # Add pedagogy config section
        parts.append("\n\n" + self.pedagogy_config.to_system_prompt_section())

        return "".join(parts)

    def _build_messages(
        self,
        student_message: str,
        context: str,
        move: PedagogicalMove,
        message_type: StudentMessageType,
    ) -> list[dict[str, str]]:
        """Build message list for LLM."""
        messages = []

        # Add conversation history (limited to recent messages)
        history_limit = 10
        for msg in self.conversation_history[-history_limit:]:
            messages.append(msg)

        # Add context as a system-like message if available
        if context:
            messages.append(
                {
                    "role": "user",
                    "content": f"[Context from course materials]\n{context}\n\n[Student message]\n{student_message}",
                }
            )
        else:
            messages.append(
                {
                    "role": "user",
                    "content": student_message,
                }
            )

        return messages

    async def _post_response_processing(
        self,
        interaction_id: str,
        student_message: str,
        tutor_response: str,
        move: PedagogicalMove,
        message_type: StudentMessageType,
        gaming_flags: list[dict],
        timestamp: datetime,
    ) -> None:
        """Process after response generation."""
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": student_message})
        self.conversation_history.append({"role": "assistant", "content": tutor_response})

        # Update hint count if we gave a hint
        if move in (PedagogicalMove.HINT, PedagogicalMove.SCAFFOLD):
            self.hint_count += 1

        # Update last interaction time
        self.last_interaction_time = timestamp

        # Log interaction (would save to database in full implementation)
        logger.info(
            "interaction_complete",
            interaction_id=interaction_id,
            session_id=self.session_id,
            move=move.value,
            message_type=message_type.value,
            gaming_flags_count=len(gaming_flags),
            response_length=len(tutor_response),
        )

    def reset_hint_count(self) -> None:
        """Reset hint count (e.g., when moving to new topic)."""
        self.hint_count = 0

    def set_current_concept(self, concept_id: str) -> None:
        """Set the current concept being discussed."""
        self.current_concept_id = concept_id
        self.reset_hint_count()

    def get_conversation_summary(self) -> dict[str, Any]:
        """Get summary of current conversation state."""
        return {
            "session_id": self.session_id,
            "message_count": len(self.conversation_history),
            "current_concept_id": self.current_concept_id,
            "hint_count": self.hint_count,
            "last_interaction": self.last_interaction_time.isoformat()
            if self.last_interaction_time
            else None,
        }
