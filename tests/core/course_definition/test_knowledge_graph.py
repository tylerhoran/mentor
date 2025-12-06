"""Tests for the knowledge graph module."""

import pytest

from mentor.core.course_definition.knowledge_graph import Concept, KnowledgeGraph


class TestConcept:
    """Tests for Concept dataclass."""

    def test_creation(self):
        """Test creating a concept."""
        concept = Concept(
            id="c1",
            name="Test Concept",
            description="A test concept",
        )
        assert concept.id == "c1"
        assert concept.name == "Test Concept"
        assert concept.description == "A test concept"
        assert concept.prerequisites == []

    def test_with_prerequisites(self):
        """Test concept with prerequisites."""
        concept = Concept(
            id="c2",
            name="Advanced Concept",
            description="Requires c1",
            prerequisites=["c1"],
        )
        assert concept.prerequisites == ["c1"]

    def test_default_values(self):
        """Test default values."""
        concept = Concept(id="c1", name="Test", description="Desc")
        assert concept.learning_objectives == []
        assert concept.estimated_time_minutes == 60
        assert concept.difficulty_level == 1

    def test_to_dict(self):
        """Test serialization to dict."""
        concept = Concept(
            id="c1",
            name="Test",
            description="Desc",
            prerequisites=["c0"],
            difficulty_level=3,
        )
        d = concept.to_dict()
        assert d["id"] == "c1"
        assert d["name"] == "Test"
        assert d["prerequisites"] == ["c0"]
        assert d["difficulty_level"] == 3

    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "id": "c1",
            "name": "Test",
            "description": "Desc",
            "prerequisites": ["c0"],
            "difficulty_level": 2,
        }
        concept = Concept.from_dict(data)
        assert concept.id == "c1"
        assert concept.name == "Test"
        assert concept.prerequisites == ["c0"]
        assert concept.difficulty_level == 2


class TestKnowledgeGraph:
    """Tests for KnowledgeGraph class."""

    def test_initialization(self):
        """Test graph initialization."""
        graph = KnowledgeGraph(course_id="course-1")
        assert graph.course_id == "course-1"
        assert len(graph._concepts) == 0

    def test_add_concept(self):
        """Test adding a concept."""
        graph = KnowledgeGraph(course_id="course-1")
        concept = Concept(id="c1", name="Concept 1", description="First")
        graph.add_concept(concept)

        assert "c1" in graph._concepts
        assert graph.get_concept("c1") == concept

    def test_add_concept_with_prerequisites(self):
        """Test adding concept with prerequisites."""
        graph = KnowledgeGraph(course_id="course-1")
        c1 = Concept(id="c1", name="Concept 1", description="First")
        c2 = Concept(id="c2", name="Concept 2", description="Second", prerequisites=["c1"])

        graph.add_concept(c1)
        graph.add_concept(c2)

        assert graph.graph.has_edge("c1", "c2")

    def test_add_concept_cycle_detection(self):
        """Test that cycles are detected."""
        graph = KnowledgeGraph(course_id="course-1")
        c1 = Concept(id="c1", name="C1", description="", prerequisites=["c2"])
        c2 = Concept(id="c2", name="C2", description="", prerequisites=["c1"])

        graph.add_concept(c1)
        with pytest.raises(ValueError, match="cycle"):
            graph.add_concept(c2)

    def test_remove_concept(self):
        """Test removing a concept."""
        graph = KnowledgeGraph(course_id="course-1")
        concept = Concept(id="c1", name="C1", description="")
        graph.add_concept(concept)

        graph.remove_concept("c1")
        assert "c1" not in graph._concepts

    def test_remove_concept_not_found(self):
        """Test removing non-existent concept."""
        graph = KnowledgeGraph(course_id="course-1")
        # Should not raise
        graph.remove_concept("nonexistent")

    def test_get_concept(self):
        """Test getting a concept."""
        graph = KnowledgeGraph(course_id="course-1")
        concept = Concept(id="c1", name="C1", description="")
        graph.add_concept(concept)

        result = graph.get_concept("c1")
        assert result == concept

    def test_get_concept_not_found(self):
        """Test getting non-existent concept."""
        graph = KnowledgeGraph(course_id="course-1")
        result = graph.get_concept("nonexistent")
        assert result is None

    def test_linear_chain(self):
        """Test a linear chain of prerequisites."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c2"]))

        path = graph.get_learning_path("c3")
        assert path == ["c1", "c2", "c3"]

    def test_diamond_dependency(self):
        """Test diamond-shaped dependencies."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c1"]))
        graph.add_concept(Concept(id="c4", name="C4", description="", prerequisites=["c2", "c3"]))

        path = graph.get_learning_path("c4")
        # c1 must come before c2 and c3, and both must come before c4
        assert path.index("c1") < path.index("c2")
        assert path.index("c1") < path.index("c3")
        assert path.index("c2") < path.index("c4")
        assert path.index("c3") < path.index("c4")

    def test_get_learning_path(self):
        """Test getting learning path."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))

        path = graph.get_learning_path("c2")
        assert "c1" in path
        assert "c2" in path
        assert path.index("c1") < path.index("c2")

    def test_get_learning_path_no_prereqs(self):
        """Test learning path for concept with no prerequisites."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))

        path = graph.get_learning_path("c1")
        assert path == ["c1"]

    def test_get_learning_path_not_found(self):
        """Test learning path for non-existent concept."""
        graph = KnowledgeGraph(course_id="course-1")
        path = graph.get_learning_path("nonexistent")
        assert path == []

    def test_get_ready_concepts_all_new(self):
        """Test ready concepts when none mastered."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))

        ready = graph.get_ready_concepts(set())
        # Only c1 is ready (c2 requires c1)
        assert "c1" in ready
        assert "c2" not in ready

    def test_get_ready_concepts_some_mastered(self):
        """Test ready concepts with some mastered."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c1"]))

        ready = graph.get_ready_concepts({"c1"})
        assert "c1" not in ready  # Already mastered
        assert "c2" in ready
        assert "c3" in ready

    def test_get_ready_concepts_all_mastered(self):
        """Test ready concepts when all mastered."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))

        ready = graph.get_ready_concepts({"c1"})
        assert ready == []

    def test_get_next_concept(self):
        """Test getting next recommended concept."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description="", difficulty_level=1))
        graph.add_concept(Concept(id="c2", name="C2", description="", difficulty_level=2))

        next_concept = graph.get_next_concept(set())
        # Should pick lower difficulty first
        assert next_concept == "c1"

    def test_get_next_concept_with_progress(self):
        """Test next concept with some progress."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))

        next_concept = graph.get_next_concept({"c1"})
        assert next_concept == "c2"

    def test_get_next_concept_all_mastered(self):
        """Test next concept when all mastered."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))

        next_concept = graph.get_next_concept({"c1"})
        assert next_concept is None

    def test_validate_valid_graph(self):
        """Test validation on valid graph."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))

        issues = graph.validate()
        assert issues == []

    def test_validate_missing_prerequisite(self):
        """Test validation with missing prerequisite."""
        graph = KnowledgeGraph(course_id="course-1")
        # Add concept with prereq that doesn't exist
        concept = Concept(id="c2", name="C2", description="", prerequisites=["c1"])
        graph._concepts["c2"] = concept
        graph.graph.add_node("c2", concept=concept)

        issues = graph.validate()
        assert any("missing prerequisite" in issue for issue in issues)

    def test_to_yaml_from_yaml(self):
        """Test YAML serialization roundtrip."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description="First"))
        graph.add_concept(Concept(id="c2", name="C2", description="Second", prerequisites=["c1"]))

        yaml_str = graph.to_yaml()

        graph2 = KnowledgeGraph.from_yaml("course-1", yaml_str)
        assert "c1" in graph2._concepts
        assert "c2" in graph2._concepts
        assert graph2.get_concept("c2").prerequisites == ["c1"]

    def test_update_concept(self):
        """Test updating a concept."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description="Original"))

        updated = Concept(id="c1", name="C1 Updated", description="Updated")
        graph.update_concept(updated)

        assert graph.get_concept("c1").name == "C1 Updated"

    def test_update_concept_not_found(self):
        """Test updating non-existent concept."""
        graph = KnowledgeGraph(course_id="course-1")
        with pytest.raises(ValueError, match="not found"):
            graph.update_concept(Concept(id="c1", name="C1", description=""))

    def test_update_concept_prerequisites(self):
        """Test updating concept prerequisites."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description=""))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c1"]))

        # Update c3 to require c2 instead of c1
        updated = Concept(id="c3", name="C3", description="", prerequisites=["c2"])
        graph.update_concept(updated)

        assert graph.graph.has_edge("c2", "c3")
        assert not graph.graph.has_edge("c1", "c3")

    def test_topological_order(self):
        """Test getting topological order."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c2"]))

        order = graph.get_topological_order()
        assert order.index("c1") < order.index("c2") < order.index("c3")

    def test_get_dependents(self):
        """Test getting dependents."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c1"]))

        dependents = graph.get_dependents("c1")
        assert "c2" in dependents
        assert "c3" in dependents

    def test_get_prerequisites(self):
        """Test getting prerequisites."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description=""))
        graph.add_concept(Concept(id="c3", name="C3", description="", prerequisites=["c1", "c2"]))

        prereqs = graph.get_prerequisites("c3")
        assert "c1" in prereqs
        assert "c2" in prereqs

    def test_get_statistics(self):
        """Test getting graph statistics."""
        graph = KnowledgeGraph(course_id="course-1")
        graph.add_concept(Concept(id="c1", name="C1", description=""))
        graph.add_concept(Concept(id="c2", name="C2", description="", prerequisites=["c1"]))

        stats = graph.get_statistics()
        assert stats["total_concepts"] == 2
        assert stats["total_edges"] == 1
        assert stats["is_valid"] is True
