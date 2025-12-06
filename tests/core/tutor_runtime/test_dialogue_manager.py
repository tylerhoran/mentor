"""Tests for DialogueManager."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock

import pytest

from mentor.core.tutor_runtime.dialogue_manager import (
    DialogueManager,
    PedagogicalMove,
    StudentMessageType,
)


class TestStudentMessageType:
    """Tests for StudentMessageType enum."""

    def test_all_types(self):
        """Test all message types exist."""
        assert StudentMessageType.QUESTION is not None
        assert StudentMessageType.ANSWER is not None
        assert StudentMessageType.CONFUSION is not None
        assert StudentMessageType.REQUEST_ANSWER is not None
        assert StudentMessageType.ACKNOWLEDGMENT is not None
        assert StudentMessageType.OFF_TOPIC is not None

    def test_message_type_values(self):
        """Test message type string values."""
        assert StudentMessageType.QUESTION.value == "question"
        assert StudentMessageType.ANSWER.value == "answer"
        assert StudentMessageType.CONFUSION.value == "confusion"


class TestPedagogicalMove:
    """Tests for PedagogicalMove enum."""

    def test_all_moves(self):
        """Test all pedagogical moves exist."""
        assert PedagogicalMove.SCAFFOLD is not None
        assert PedagogicalMove.PROBE is not None
        assert PedagogicalMove.CORRECT is not None
        assert PedagogicalMove.EXPLAIN is not None
        assert PedagogicalMove.REDIRECT is not None
        assert PedagogicalMove.ENCOURAGE is not None
        assert PedagogicalMove.ADVANCE is not None
        assert PedagogicalMove.CLARIFY is not None
        assert PedagogicalMove.EXAMPLE is not None
        assert PedagogicalMove.HINT is not None

    def test_move_values(self):
        """Test move string values."""
        assert PedagogicalMove.SCAFFOLD.value == "scaffold"
        assert PedagogicalMove.PROBE.value == "probe"
        assert PedagogicalMove.REDIRECT.value == "redirect"


class TestDialogueManager:
    """Tests for DialogueManager class."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = AsyncMock()
        client.generate = AsyncMock(return_value="This is a tutor response.")
        return client

    @pytest.fixture
    def mock_retriever(self):
        """Create a mock retriever."""
        retriever = AsyncMock()
        retriever.get_context_for_response = AsyncMock(return_value="Relevant context here.")
        return retriever

    @pytest.fixture
    def mock_state_manager(self):
        """Create a mock state manager."""
        return AsyncMock()

    @pytest.fixture
    def mock_gaming_detector(self):
        """Create a mock gaming detector."""
        return None  # Optional in the API

    @pytest.fixture
    def mock_pedagogy_config(self):
        """Create a mock pedagogy config."""
        config = Mock()
        config.probe_on_correct = True
        config.to_system_prompt_section = Mock(return_value="Pedagogy section.")
        return config

    @pytest.fixture
    def dialogue_manager(
        self,
        mock_llm_client,
        mock_retriever,
        mock_state_manager,
        mock_gaming_detector,
        mock_pedagogy_config,
    ):
        """Create a dialogue manager with mocks."""
        return DialogueManager(
            course_id="course-123",
            student_id="student-456",
            session_id="session-789",
            llm_client=mock_llm_client,
            retriever=mock_retriever,
            state_manager=mock_state_manager,
            gaming_detector=mock_gaming_detector,
            pedagogy_config=mock_pedagogy_config,
            system_prompt="You are a helpful tutor.",
        )

    def test_initialization(self, dialogue_manager):
        """Test dialogue manager initialization."""
        assert dialogue_manager.course_id == "course-123"
        assert dialogue_manager.student_id == "student-456"
        assert dialogue_manager.session_id == "session-789"
        assert dialogue_manager.conversation_history == []
        assert dialogue_manager.hint_count == 0
        assert dialogue_manager.current_concept_id is None

    @pytest.mark.asyncio
    async def test_classify_message_question(self, dialogue_manager):
        """Test classifying a question."""
        msg_type = await dialogue_manager._classify_message("What is a variable?")
        assert msg_type == StudentMessageType.QUESTION

    @pytest.mark.asyncio
    async def test_classify_message_question_how(self, dialogue_manager):
        """Test classifying how questions."""
        msg_type = await dialogue_manager._classify_message("How do I create a list?")
        assert msg_type == StudentMessageType.QUESTION

    @pytest.mark.asyncio
    async def test_classify_message_confusion(self, dialogue_manager):
        """Test classifying confusion."""
        msg_type = await dialogue_manager._classify_message("I don't understand this")
        assert msg_type == StudentMessageType.CONFUSION

    @pytest.mark.asyncio
    async def test_classify_message_confusion_lost(self, dialogue_manager):
        """Test classifying being lost."""
        msg_type = await dialogue_manager._classify_message("I'm confused about loops")
        assert msg_type == StudentMessageType.CONFUSION

    @pytest.mark.asyncio
    async def test_classify_message_request_answer(self, dialogue_manager):
        """Test classifying requests for answers."""
        msg_type = await dialogue_manager._classify_message("Just tell me the answer")
        assert msg_type == StudentMessageType.REQUEST_ANSWER

    @pytest.mark.asyncio
    async def test_classify_message_acknowledgment(self, dialogue_manager):
        """Test classifying acknowledgments."""
        msg_type = await dialogue_manager._classify_message("Ok, I got it")
        assert msg_type == StudentMessageType.ACKNOWLEDGMENT

    @pytest.mark.asyncio
    async def test_classify_message_answer(self, dialogue_manager):
        """Test classifying answers (default)."""
        msg_type = await dialogue_manager._classify_message("I think the answer is 42")
        assert msg_type == StudentMessageType.ANSWER

    @pytest.mark.asyncio
    async def test_determine_move_for_question(self, dialogue_manager):
        """Test move selection for questions."""
        move = await dialogue_manager._determine_move(
            "What is a variable?",
            StudentMessageType.QUESTION,
            [],
        )
        assert move in [PedagogicalMove.EXPLAIN, PedagogicalMove.SCAFFOLD]

    @pytest.mark.asyncio
    async def test_determine_move_for_confusion(self, dialogue_manager):
        """Test move selection for confusion."""
        move = await dialogue_manager._determine_move(
            "I don't understand",
            StudentMessageType.CONFUSION,
            [],
        )
        assert move == PedagogicalMove.SCAFFOLD

    @pytest.mark.asyncio
    async def test_determine_move_for_answer(self, dialogue_manager):
        """Test move selection for answers."""
        move = await dialogue_manager._determine_move(
            "The answer is 42",
            StudentMessageType.ANSWER,
            [],
        )
        assert move in [PedagogicalMove.PROBE, PedagogicalMove.ADVANCE]

    @pytest.mark.asyncio
    async def test_determine_move_for_request_answer(self, dialogue_manager):
        """Test move selection for answer requests redirects."""
        move = await dialogue_manager._determine_move(
            "Just give me the answer",
            StudentMessageType.REQUEST_ANSWER,
            [],
        )
        assert move == PedagogicalMove.REDIRECT

    def test_build_system_prompt(self, dialogue_manager):
        """Test system prompt building."""
        prompt = dialogue_manager._build_system_prompt(PedagogicalMove.EXPLAIN)

        assert "You are a helpful tutor" in prompt
        assert len(prompt) > 50

    def test_build_system_prompt_scaffold(self, dialogue_manager):
        """Test system prompt for scaffold move."""
        prompt = dialogue_manager._build_system_prompt(PedagogicalMove.SCAFFOLD)

        assert "Break down the problem" in prompt

    def test_build_system_prompt_redirect(self, dialogue_manager):
        """Test system prompt for redirect move."""
        prompt = dialogue_manager._build_system_prompt(PedagogicalMove.REDIRECT)

        assert "asking for a direct answer" in prompt

    def test_build_messages(self, dialogue_manager):
        """Test building message history."""
        dialogue_manager.conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        messages = dialogue_manager._build_messages(
            student_message="What is a variable?",
            context="Variables store data.",
            move=PedagogicalMove.EXPLAIN,
            message_type=StudentMessageType.QUESTION,
        )

        assert len(messages) >= 3
        assert messages[-1]["role"] == "user"
        assert "Variable" in messages[-1]["content"] or "variable" in messages[-1]["content"]

    def test_build_messages_with_context(self, dialogue_manager):
        """Test that context is included in messages."""
        messages = dialogue_manager._build_messages(
            student_message="What is recursion?",
            context="Recursion is when a function calls itself.",
            move=PedagogicalMove.EXPLAIN,
            message_type=StudentMessageType.QUESTION,
        )

        # Context should be in the user message
        assert any("Context" in msg["content"] for msg in messages)

    def test_build_messages_truncates_history(self, dialogue_manager):
        """Test that long history is truncated."""
        # Add many messages
        for i in range(50):
            dialogue_manager.conversation_history.append(
                {"role": "user", "content": f"Message {i}"}
            )
            dialogue_manager.conversation_history.append(
                {"role": "assistant", "content": f"Response {i}"}
            )

        messages = dialogue_manager._build_messages(
            student_message="Current message",
            context="",
            move=PedagogicalMove.SCAFFOLD,
            message_type=StudentMessageType.QUESTION,
        )

        # Should be limited to 10 history messages + 1 current
        assert len(messages) <= 11

    @pytest.mark.asyncio
    async def test_respond_basic(self, dialogue_manager, mock_llm_client):
        """Test basic response generation."""
        response = await dialogue_manager.respond("What is a variable?")

        assert response is not None
        assert len(response) > 0
        mock_llm_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_respond_updates_history(self, dialogue_manager):
        """Test that respond updates conversation history."""
        initial_len = len(dialogue_manager.conversation_history)

        await dialogue_manager.respond("Hello")

        # Should add user message and assistant response
        assert len(dialogue_manager.conversation_history) == initial_len + 2

    @pytest.mark.asyncio
    async def test_respond_retrieves_context(self, dialogue_manager, mock_retriever):
        """Test that respond retrieves relevant context."""
        await dialogue_manager.respond("Explain recursion")

        mock_retriever.get_context_for_response.assert_called()

    def test_set_current_concept(self, dialogue_manager):
        """Test setting current concept."""
        dialogue_manager.hint_count = 5  # Set some hints

        dialogue_manager.set_current_concept("new-concept-id")

        assert dialogue_manager.current_concept_id == "new-concept-id"
        assert dialogue_manager.hint_count == 0  # Should reset

    def test_reset_hint_count(self, dialogue_manager):
        """Test resetting hint count."""
        dialogue_manager.hint_count = 5

        dialogue_manager.reset_hint_count()

        assert dialogue_manager.hint_count == 0

    def test_get_conversation_summary(self, dialogue_manager):
        """Test getting conversation summary."""
        dialogue_manager.conversation_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"},
        ]
        dialogue_manager.current_concept_id = "concept-1"
        dialogue_manager.hint_count = 3

        summary = dialogue_manager.get_conversation_summary()

        assert summary["session_id"] == "session-789"
        assert summary["message_count"] == 2
        assert summary["current_concept_id"] == "concept-1"
        assert summary["hint_count"] == 3

    @pytest.mark.asyncio
    async def test_respond_handles_llm_error(self, dialogue_manager, mock_llm_client):
        """Test graceful handling of LLM errors."""
        mock_llm_client.generate = AsyncMock(side_effect=Exception("LLM Error"))

        with pytest.raises(Exception, match="LLM Error"):
            await dialogue_manager.respond("Hello")

    @pytest.mark.asyncio
    async def test_post_response_updates_hint_count(self, dialogue_manager):
        """Test that hints increment hint count."""
        initial_count = dialogue_manager.hint_count

        await dialogue_manager._post_response_processing(
            interaction_id="test-id",
            student_message="Help me",
            tutor_response="Here's a hint...",
            move=PedagogicalMove.HINT,
            message_type=StudentMessageType.CONFUSION,
            gaming_flags=[],
            timestamp=datetime.now(UTC),
        )

        assert dialogue_manager.hint_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_post_response_updates_last_interaction_time(self, dialogue_manager):
        """Test that last interaction time is updated."""
        assert dialogue_manager.last_interaction_time is None

        timestamp = datetime.now(UTC)
        await dialogue_manager._post_response_processing(
            interaction_id="test-id",
            student_message="Hello",
            tutor_response="Hi!",
            move=PedagogicalMove.ENCOURAGE,
            message_type=StudentMessageType.ACKNOWLEDGMENT,
            gaming_flags=[],
            timestamp=timestamp,
        )

        assert dialogue_manager.last_interaction_time == timestamp
