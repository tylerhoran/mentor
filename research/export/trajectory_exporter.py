"""
Export student learning trajectories for research analysis.

This module provides tools to export anonymized learning data
for educational research purposes.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mentor.models.concept import Concept
from mentor.models.course import Course, CourseEnrollment
from mentor.models.interaction import Interaction
from mentor.models.student_state import StudentState


class TrajectoryExporter:
    """Export learning trajectories in various formats for research."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def export_course_trajectories(
        self, course_id: UUID, output_dir: Path, anonymize: bool = True, format: str = "csv"
    ) -> dict[str, Path]:
        """
        Export all student trajectories for a course.

        Args:
            course_id: The course to export data for
            output_dir: Directory to write export files
            anonymize: Whether to anonymize student identifiers
            format: Output format ("csv", "json", or "both")

        Returns:
            Dictionary mapping export type to file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Get course data
        course = await self.session.get(Course, course_id)
        if not course:
            raise ValueError(f"Course {course_id} not found")

        # Get enrollments
        enrollments = await self.session.execute(
            select(CourseEnrollment).where(CourseEnrollment.course_id == course_id)
        )
        enrollments = enrollments.scalars().all()

        # Create anonymization mapping
        student_map = {}
        if anonymize:
            for i, enrollment in enumerate(enrollments):
                student_map[str(enrollment.student_id)] = f"student_{i:04d}"
        else:
            for enrollment in enrollments:
                student_map[str(enrollment.student_id)] = str(enrollment.student_id)

        # Export interactions
        interactions_path = await self._export_interactions(
            course_id, student_map, output_dir, format
        )

        # Export mastery states
        mastery_path = await self._export_mastery_states(course_id, student_map, output_dir, format)

        # Export summary statistics
        summary_path = await self._export_summary(course_id, student_map, output_dir)

        return {
            "interactions": interactions_path,
            "mastery": mastery_path,
            "summary": summary_path,
        }

    async def _export_interactions(
        self, course_id: UUID, student_map: dict[str, str], output_dir: Path, format: str
    ) -> Path:
        """Export interaction-level data."""

        interactions = await self.session.execute(
            select(Interaction)
            .where(Interaction.course_id == course_id)
            .order_by(Interaction.created_at)
        )
        interactions = interactions.scalars().all()

        rows = []
        for interaction in interactions:
            row = {
                "student_id": student_map.get(str(interaction.student_id), "unknown"),
                "session_id": str(interaction.session_id),
                "timestamp": interaction.created_at.isoformat(),
                "turn_number": interaction.turn_number,
                "student_message_length": len(interaction.student_message)
                if interaction.student_message
                else 0,
                "tutor_message_length": len(interaction.tutor_response)
                if interaction.tutor_response
                else 0,
                "concept_id": str(interaction.concept_id) if interaction.concept_id else None,
                "pedagogical_move": interaction.pedagogical_move,
                "response_time_ms": interaction.response_time_ms,
                "mastery_before": interaction.mastery_before,
                "mastery_after": interaction.mastery_after,
            }
            rows.append(row)

        output_path = output_dir / f"interactions.{format}"

        if format == "csv":
            self._write_csv(output_path, rows)
        else:
            self._write_json(output_path, rows)

        return output_path

    async def _export_mastery_states(
        self, course_id: UUID, student_map: dict[str, str], output_dir: Path, format: str
    ) -> Path:
        """Export mastery state snapshots."""

        # Get all concepts for the course
        concepts = await self.session.execute(select(Concept).where(Concept.course_id == course_id))
        concepts = {str(c.id): c.name for c in concepts.scalars().all()}

        # Get all student states
        states = await self.session.execute(
            select(StudentState).where(StudentState.course_id == course_id)
        )
        states = states.scalars().all()

        rows = []
        for state in states:
            for concept_id, mastery in (state.concept_mastery or {}).items():
                row = {
                    "student_id": student_map.get(str(state.student_id), "unknown"),
                    "concept_id": concept_id,
                    "concept_name": concepts.get(concept_id, "unknown"),
                    "mastery_level": mastery,
                    "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                }
                rows.append(row)

        output_path = output_dir / f"mastery_states.{format}"

        if format == "csv":
            self._write_csv(output_path, rows)
        else:
            self._write_json(output_path, rows)

        return output_path

    async def _export_summary(
        self, course_id: UUID, student_map: dict[str, str], output_dir: Path
    ) -> Path:
        """Export summary statistics."""

        # Count interactions per student
        interactions = await self.session.execute(
            select(Interaction).where(Interaction.course_id == course_id)
        )
        interactions = interactions.scalars().all()

        student_stats: dict[str, dict[str, Any]] = {}
        for interaction in interactions:
            student_id = student_map.get(str(interaction.student_id), "unknown")
            if student_id not in student_stats:
                student_stats[student_id] = {
                    "total_interactions": 0,
                    "total_sessions": set(),
                    "first_interaction": interaction.created_at,
                    "last_interaction": interaction.created_at,
                    "pedagogical_moves": {},
                }

            stats = student_stats[student_id]
            stats["total_interactions"] += 1
            stats["total_sessions"].add(str(interaction.session_id))
            stats["first_interaction"] = min(stats["first_interaction"], interaction.created_at)
            stats["last_interaction"] = max(stats["last_interaction"], interaction.created_at)

            move = interaction.pedagogical_move or "unknown"
            stats["pedagogical_moves"][move] = stats["pedagogical_moves"].get(move, 0) + 1

        # Convert to serializable format
        summary = {
            "export_date": datetime.utcnow().isoformat(),
            "course_id": str(course_id),
            "total_students": len(student_stats),
            "total_interactions": sum(s["total_interactions"] for s in student_stats.values()),
            "students": {},
        }

        for student_id, stats in student_stats.items():
            summary["students"][student_id] = {
                "total_interactions": stats["total_interactions"],
                "total_sessions": len(stats["total_sessions"]),
                "first_interaction": stats["first_interaction"].isoformat(),
                "last_interaction": stats["last_interaction"].isoformat(),
                "days_active": (stats["last_interaction"] - stats["first_interaction"]).days + 1,
                "pedagogical_move_distribution": stats["pedagogical_moves"],
            }

        output_path = output_dir / "summary.json"
        self._write_json(output_path, summary)

        return output_path

    def _write_csv(self, path: Path, rows: list[dict]) -> None:
        """Write rows to CSV file."""
        if not rows:
            return

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

    def _write_json(self, path: Path, data: Any) -> None:
        """Write data to JSON file."""
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)


class AnonymizedDataset:
    """
    Helper class for working with exported anonymized datasets.

    Provides utilities for loading and analyzing exported data.
    """

    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self._interactions = None
        self._mastery = None
        self._summary = None

    def load_interactions(self) -> list[dict]:
        """Load interactions data."""
        if self._interactions is None:
            csv_path = self.export_dir / "interactions.csv"
            json_path = self.export_dir / "interactions.json"

            if csv_path.exists():
                with open(csv_path) as f:
                    reader = csv.DictReader(f)
                    self._interactions = list(reader)
            elif json_path.exists():
                with open(json_path) as f:
                    self._interactions = json.load(f)
            else:
                raise FileNotFoundError("No interactions file found")

        return self._interactions

    def load_mastery(self) -> list[dict]:
        """Load mastery state data."""
        if self._mastery is None:
            csv_path = self.export_dir / "mastery_states.csv"
            json_path = self.export_dir / "mastery_states.json"

            if csv_path.exists():
                with open(csv_path) as f:
                    reader = csv.DictReader(f)
                    self._mastery = list(reader)
            elif json_path.exists():
                with open(json_path) as f:
                    self._mastery = json.load(f)
            else:
                raise FileNotFoundError("No mastery file found")

        return self._mastery

    def load_summary(self) -> dict:
        """Load summary statistics."""
        if self._summary is None:
            with open(self.export_dir / "summary.json") as f:
                self._summary = json.load(f)

        return self._summary

    def get_student_trajectory(self, student_id: str) -> list[dict]:
        """Get chronological trajectory for a specific student."""
        interactions = self.load_interactions()
        student_interactions = [i for i in interactions if i["student_id"] == student_id]
        return sorted(student_interactions, key=lambda x: x["timestamp"])

    def compute_learning_curves(self) -> dict[str, list[tuple[int, float]]]:
        """
        Compute learning curves (mastery over interactions) per student.

        Returns:
            Dictionary mapping student_id to list of (interaction_num, mastery) tuples
        """
        interactions = self.load_interactions()

        curves: dict[str, list[tuple[int, float]]] = {}

        for interaction in interactions:
            student_id = interaction["student_id"]
            if student_id not in curves:
                curves[student_id] = []

            mastery_after = interaction.get("mastery_after")
            if mastery_after is not None:
                curves[student_id].append((len(curves[student_id]), float(mastery_after)))

        return curves
