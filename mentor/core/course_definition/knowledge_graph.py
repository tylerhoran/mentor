"""
Knowledge graph management for course concepts.

Supports:
- Adding/removing concepts
- Defining prerequisites (DAG structure)
- Topological sorting for learning paths
- Detecting cycles
- Exporting/importing graph structure
"""

from dataclasses import dataclass, field
from typing import Any

import networkx as nx
import yaml


@dataclass
class Concept:
    """A concept in the knowledge graph."""

    id: str
    name: str
    description: str
    prerequisites: list[str] = field(default_factory=list)
    learning_objectives: list[str] = field(default_factory=list)
    estimated_time_minutes: int = 60
    difficulty_level: int = 1  # 1-5

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "prerequisites": self.prerequisites,
            "learning_objectives": self.learning_objectives,
            "estimated_time_minutes": self.estimated_time_minutes,
            "difficulty_level": self.difficulty_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Concept":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            prerequisites=data.get("prerequisites", []),
            learning_objectives=data.get("learning_objectives", []),
            estimated_time_minutes=data.get("estimated_time_minutes", 60),
            difficulty_level=data.get("difficulty_level", 1),
        )


class KnowledgeGraph:
    """
    Knowledge graph for managing course concepts and their relationships.

    The graph is a directed acyclic graph (DAG) where edges represent
    prerequisite relationships. An edge from A to B means A is a
    prerequisite for B.
    """

    def __init__(self, course_id: str):
        """Initialize an empty knowledge graph."""
        self.course_id = course_id
        self.graph = nx.DiGraph()
        self._concepts: dict[str, Concept] = {}

    def add_concept(self, concept: Concept) -> None:
        """
        Add a concept node with prerequisite edges.

        Args:
            concept: The concept to add

        Raises:
            ValueError: If adding this concept would create a cycle
        """
        # Add node
        self.graph.add_node(concept.id, concept=concept)
        self._concepts[concept.id] = concept

        # Add prerequisite edges
        for prereq_id in concept.prerequisites:
            if prereq_id in self._concepts:
                self.graph.add_edge(prereq_id, concept.id)

        # Update edges from other concepts that might depend on this one
        for other_id, other_concept in self._concepts.items():
            if concept.id in other_concept.prerequisites and other_id != concept.id:
                self.graph.add_edge(concept.id, other_id)

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            # Remove the concept and restore
            self.remove_concept(concept.id)
            raise ValueError(f"Adding concept {concept.id} would create a cycle")

    def remove_concept(self, concept_id: str) -> None:
        """Remove a concept from the graph."""
        if concept_id in self._concepts:
            self.graph.remove_node(concept_id)
            del self._concepts[concept_id]

    def update_concept(self, concept: Concept) -> None:
        """Update an existing concept."""
        if concept.id not in self._concepts:
            raise ValueError(f"Concept {concept.id} not found")

        # Remove old edges
        old_prereqs = self._concepts[concept.id].prerequisites
        for prereq_id in old_prereqs:
            if self.graph.has_edge(prereq_id, concept.id):
                self.graph.remove_edge(prereq_id, concept.id)

        # Update concept
        self._concepts[concept.id] = concept
        self.graph.nodes[concept.id]["concept"] = concept

        # Add new edges
        for prereq_id in concept.prerequisites:
            if prereq_id in self._concepts:
                self.graph.add_edge(prereq_id, concept.id)

        # Verify no cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Update would create a cycle")

    def get_concept(self, concept_id: str) -> Concept | None:
        """Get a concept by ID."""
        return self._concepts.get(concept_id)

    def get_all_concepts(self) -> list[Concept]:
        """Get all concepts in the graph."""
        return list(self._concepts.values())

    def get_learning_path(self, target_concept_id: str) -> list[str]:
        """
        Return ordered list of concepts to reach target.

        Uses topological sort to ensure prerequisites come first.

        Args:
            target_concept_id: The concept to reach

        Returns:
            List of concept IDs in learning order
        """
        if target_concept_id not in self._concepts:
            return []

        # Get all ancestors (prerequisites recursively)
        ancestors = nx.ancestors(self.graph, target_concept_id)
        ancestors.add(target_concept_id)

        # Create subgraph and topologically sort
        subgraph = self.graph.subgraph(ancestors)
        return list(nx.topological_sort(subgraph))

    def get_ready_concepts(self, mastered_concepts: set[str]) -> list[str]:
        """
        Return concepts whose prerequisites are all mastered.

        Args:
            mastered_concepts: Set of concept IDs already mastered

        Returns:
            List of concept IDs ready to learn
        """
        ready = []
        for concept_id, concept in self._concepts.items():
            if concept_id in mastered_concepts:
                continue
            # Check if all prerequisites are mastered
            if all(prereq in mastered_concepts for prereq in concept.prerequisites):
                ready.append(concept_id)
        return ready

    def get_next_concept(self, mastered_concepts: set[str]) -> str | None:
        """
        Get the recommended next concept to learn.

        Chooses the ready concept with lowest difficulty level.

        Args:
            mastered_concepts: Set of concept IDs already mastered

        Returns:
            The next concept ID to learn, or None if all mastered
        """
        ready = self.get_ready_concepts(mastered_concepts)
        if not ready:
            return None

        # Sort by difficulty and sequence order
        ready_concepts = [self._concepts[cid] for cid in ready]
        ready_concepts.sort(key=lambda c: (c.difficulty_level, c.id))
        return ready_concepts[0].id

    def get_dependents(self, concept_id: str) -> list[str]:
        """Get concepts that depend on this concept."""
        if concept_id not in self.graph:
            return []
        return list(self.graph.successors(concept_id))

    def get_prerequisites(self, concept_id: str) -> list[str]:
        """Get direct prerequisites of a concept."""
        if concept_id not in self.graph:
            return []
        return list(self.graph.predecessors(concept_id))

    def validate(self) -> list[str]:
        """
        Check for cycles, orphans, return list of issues.

        Returns:
            List of validation issue descriptions
        """
        issues = []

        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            for cycle in cycles:
                issues.append(f"Cycle detected: {' -> '.join(cycle)}")

        # Check for missing prerequisites
        for concept_id, concept in self._concepts.items():
            for prereq_id in concept.prerequisites:
                if prereq_id not in self._concepts:
                    issues.append(f"Concept '{concept_id}' has missing prerequisite '{prereq_id}'")

        # Check for orphans (no path to any starting concept)
        roots = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        if not roots and len(self._concepts) > 0:
            issues.append("No root concepts found (all concepts have prerequisites)")

        return issues

    def to_yaml(self) -> str:
        """Export graph structure as YAML."""
        data = {"concepts": [concept.to_dict() for concept in self._concepts.values()]}
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, course_id: str, yaml_content: str) -> "KnowledgeGraph":
        """Import graph from YAML."""
        data = yaml.safe_load(yaml_content)
        graph = cls(course_id)

        # First pass: add all concepts without edges
        concepts = [Concept.from_dict(c) for c in data.get("concepts", [])]

        # Sort by number of prerequisites to add in dependency order
        concepts.sort(key=lambda c: len(c.prerequisites))

        for concept in concepts:
            try:
                graph.add_concept(concept)
            except ValueError as e:
                # Log warning but continue
                print(f"Warning: {e}")

        return graph

    def get_topological_order(self) -> list[str]:
        """Get all concepts in topological order."""
        return list(nx.topological_sort(self.graph))

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the knowledge graph."""
        return {
            "total_concepts": len(self._concepts),
            "total_edges": self.graph.number_of_edges(),
            "root_concepts": len([n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]),
            "leaf_concepts": len([n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]),
            "max_depth": nx.dag_longest_path_length(self.graph) if self._concepts else 0,
            "is_valid": len(self.validate()) == 0,
        }
