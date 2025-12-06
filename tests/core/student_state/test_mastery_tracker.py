"""Tests for the mastery tracker module."""

from datetime import UTC, datetime, timedelta

import pytest

from mentor.core.student_state.mastery_tracker import MasteryEstimate, MasteryTracker


class TestMasteryEstimate:
    """Tests for MasteryEstimate dataclass."""

    def test_creation(self):
        """Test creating a mastery estimate."""
        estimate = MasteryEstimate(
            estimate=0.7,
            confidence=0.8,
            interaction_count=5,
        )
        assert estimate.estimate == 0.7
        assert estimate.confidence == 0.8
        assert estimate.interaction_count == 5

    def test_default_values(self):
        """Test default values."""
        estimate = MasteryEstimate()
        assert estimate.estimate == 0.0
        assert estimate.confidence == 0.0
        assert estimate.interaction_count == 0
        assert estimate.last_updated is not None

    def test_to_dict(self):
        """Test serialization to dict."""
        now = datetime.now(UTC)
        estimate = MasteryEstimate(
            estimate=0.5,
            confidence=0.6,
            interaction_count=3,
            last_updated=now,
        )
        d = estimate.to_dict()
        assert d["estimate"] == 0.5
        assert d["confidence"] == 0.6
        assert d["interactions"] == 3
        assert "last_updated" in d

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "estimate": 0.75,
            "confidence": 0.85,
            "interactions": 10,
            "last_updated": "2024-01-01T12:00:00+00:00",
        }
        estimate = MasteryEstimate.from_dict(data)
        assert estimate.estimate == 0.75
        assert estimate.confidence == 0.85
        assert estimate.interaction_count == 10


class TestMasteryTracker:
    """Tests for MasteryTracker class."""

    def test_initialization(self):
        """Test tracker initialization."""
        tracker = MasteryTracker()
        assert tracker._mastery == {}
        assert tracker.graph is None

    def test_get_mastery_new_concept(self):
        """Test getting mastery for a new concept."""
        tracker = MasteryTracker()
        mastery = tracker.get_mastery("concept-1")
        # Should return default estimate
        assert mastery.estimate == tracker.P_INIT  # 0.1
        assert mastery.confidence == 0.1
        assert mastery.interaction_count == 0

    def test_get_mastery_existing(self):
        """Test getting mastery for an existing concept."""
        tracker = MasteryTracker()
        # First call creates it
        tracker.get_mastery("concept-1")
        # Update it
        tracker.update_mastery("concept-1", "correct")
        # Get again
        mastery = tracker.get_mastery("concept-1")
        assert mastery.interaction_count == 1

    def test_update_mastery_correct_answer(self):
        """Test updating mastery with correct answer."""
        tracker = MasteryTracker()
        initial = tracker.get_mastery("concept-1")
        initial_estimate = initial.estimate

        updated = tracker.update_mastery("concept-1", "correct")
        assert updated.estimate > initial_estimate
        assert updated.interaction_count == 1

    def test_update_mastery_incorrect_answer(self):
        """Test updating mastery with incorrect answer."""
        tracker = MasteryTracker()
        # First build up some mastery
        tracker.update_mastery("concept-1", "correct")
        tracker.update_mastery("concept-1", "correct")
        after_correct = tracker.get_mastery("concept-1").estimate

        # Now get it wrong
        updated = tracker.update_mastery("concept-1", "incorrect")
        assert updated.estimate < after_correct

    def test_update_mastery_partial_credit(self):
        """Test updating mastery with partial credit."""
        tracker = MasteryTracker()
        initial = tracker.get_mastery("concept-1")
        initial_estimate = initial.estimate

        updated = tracker.update_mastery("concept-1", "partial")
        # Partial still increases but less than correct
        assert updated.estimate > initial_estimate
        assert updated.interaction_count == 1

    def test_confidence_increases_with_interactions(self):
        """Test that confidence increases with more interactions."""
        tracker = MasteryTracker()
        mastery1 = tracker.get_mastery("concept-1")
        conf1 = mastery1.confidence

        tracker.update_mastery("concept-1", "correct")
        mastery2 = tracker.get_mastery("concept-1")
        conf2 = mastery2.confidence

        tracker.update_mastery("concept-1", "correct")
        mastery3 = tracker.get_mastery("concept-1")
        conf3 = mastery3.confidence

        assert conf2 > conf1
        assert conf3 > conf2

    def test_mastery_bounded(self):
        """Test that mastery stays between 0 and 1."""
        tracker = MasteryTracker()

        # Many correct answers
        for _ in range(20):
            tracker.update_mastery("concept-1", "correct")

        mastery = tracker.get_mastery("concept-1")
        assert 0.0 <= mastery.estimate <= 1.0

    def test_is_mastered(self):
        """Test is_mastered check."""
        tracker = MasteryTracker()
        # Initialize with high mastery
        tracker._mastery["concept-1"] = MasteryEstimate(
            estimate=0.85,
            confidence=0.6,
            interaction_count=10,
        )
        assert tracker.is_mastered("concept-1") is True

        # Low estimate
        tracker._mastery["concept-2"] = MasteryEstimate(
            estimate=0.5,
            confidence=0.6,
            interaction_count=10,
        )
        assert tracker.is_mastered("concept-2") is False

    def test_is_mastered_custom_threshold(self):
        """Test is_mastered with custom threshold."""
        tracker = MasteryTracker()
        tracker._mastery["concept-1"] = MasteryEstimate(
            estimate=0.7,
            confidence=0.6,
            interaction_count=10,
        )
        assert tracker.is_mastered("concept-1", threshold=0.6) is True
        assert tracker.is_mastered("concept-1", threshold=0.8) is False

    def test_get_all_mastery(self):
        """Test getting all mastery estimates."""
        tracker = MasteryTracker()
        tracker.get_mastery("concept-1")
        tracker.get_mastery("concept-2")

        all_mastery = tracker.get_all_mastery()
        assert "concept-1" in all_mastery
        assert "concept-2" in all_mastery

    def test_get_overall_mastery(self):
        """Test calculating overall mastery."""
        tracker = MasteryTracker()
        tracker._mastery["c1"] = MasteryEstimate(estimate=0.8, confidence=0.5)
        tracker._mastery["c2"] = MasteryEstimate(estimate=0.6, confidence=0.5)

        overall = tracker.get_overall_mastery()
        assert overall == pytest.approx(0.7, abs=0.01)

    def test_get_overall_mastery_empty(self):
        """Test overall mastery with no concepts."""
        tracker = MasteryTracker()
        assert tracker.get_overall_mastery() == 0.0

    def test_get_weakest_concepts(self):
        """Test getting weakest concepts."""
        tracker = MasteryTracker()
        tracker._mastery["c1"] = MasteryEstimate(estimate=0.9, confidence=0.5)
        tracker._mastery["c2"] = MasteryEstimate(estimate=0.3, confidence=0.5)
        tracker._mastery["c3"] = MasteryEstimate(estimate=0.5, confidence=0.5)

        weakest = tracker.get_weakest_concepts(n=2)
        assert weakest[0] == "c2"  # Lowest
        assert weakest[1] == "c3"  # Second lowest

    def test_apply_decay(self):
        """Test applying forgetting decay."""
        tracker = MasteryTracker()
        tracker._mastery["concept-1"] = MasteryEstimate(
            estimate=0.8,
            confidence=0.9,
            interaction_count=10,
        )

        decayed = tracker.apply_decay("concept-1", days_since_practice=30)
        assert decayed.estimate < 0.8
        assert decayed.confidence < 0.9

    def test_get_ready_for_review(self):
        """Test getting concepts ready for review."""
        tracker = MasteryTracker()
        now = datetime.now(UTC)
        old_date = now - timedelta(days=10)

        tracker._mastery["c1"] = MasteryEstimate(
            estimate=0.7,
            confidence=0.5,
            last_updated=old_date,
        )
        tracker._mastery["c2"] = MasteryEstimate(
            estimate=0.7,
            confidence=0.5,
            last_updated=now,
        )

        ready = tracker.get_ready_for_review(days_threshold=7)
        assert "c1" in ready
        assert "c2" not in ready

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization."""
        tracker = MasteryTracker()
        tracker.update_mastery("c1", "correct")
        tracker.update_mastery("c2", "partial")

        # Serialize
        data = tracker.to_dict()

        # Create new tracker and load
        tracker2 = MasteryTracker()
        tracker2.load_from_dict(data)

        assert "c1" in tracker2._mastery
        assert "c2" in tracker2._mastery

    def test_interaction_type_weight(self):
        """Test that different interaction types have different weights."""
        # Practice interaction
        tracker1 = MasteryTracker()
        tracker1.update_mastery("c1", "correct", interaction_type="practice")
        practice_result = tracker1.get_mastery("c1").estimate

        # Probe interaction (should weight more)
        tracker2 = MasteryTracker()
        tracker2.update_mastery("c1", "correct", interaction_type="probe")
        probe_result = tracker2.get_mastery("c1").estimate

        # Application interaction (should weight most)
        tracker3 = MasteryTracker()
        tracker3.update_mastery("c1", "correct", interaction_type="application")
        app_result = tracker3.get_mastery("c1").estimate

        assert probe_result > practice_result
        assert app_result > probe_result
