# Research Guide

Mentor provides tools for educational research on AI tutoring effectiveness, learning trajectories, and pedagogical strategies.

## Data Export

### Exporting Course Data

Use the `TrajectoryExporter` to export anonymized learning data:

```python
from pathlib import Path
from research.export.trajectory_exporter import TrajectoryExporter
from mentor.database import get_session

async def export_data():
    async with get_session() as session:
        exporter = TrajectoryExporter(session)
        
        paths = await exporter.export_course_trajectories(
            course_id=course_id,
            output_dir=Path("./exports/fall_2024"),
            anonymize=True,  # Replace student IDs with pseudonyms
            format="csv"     # or "json"
        )
        
        print(f"Exported to: {paths}")
```

### Export Files

The export produces three files:

1. **interactions.csv** - Individual tutoring interactions
   - `student_id`: Anonymized student identifier
   - `session_id`: Session identifier
   - `timestamp`: Interaction time
   - `turn_number`: Position in conversation
   - `student_message_length`: Length of student input
   - `tutor_message_length`: Length of tutor response
   - `concept_id`: Associated concept (if any)
   - `pedagogical_move`: Tutor's pedagogical strategy
   - `response_time_ms`: Student response time
   - `mastery_before`: Mastery estimate before interaction
   - `mastery_after`: Mastery estimate after interaction

2. **mastery_states.csv** - Mastery snapshots per concept
   - `student_id`: Anonymized student identifier
   - `concept_id`: Concept identifier
   - `concept_name`: Human-readable concept name
   - `mastery_level`: Current mastery estimate (0-1)
   - `updated_at`: Last update timestamp

3. **summary.json** - Aggregate statistics
   - Total students and interactions
   - Per-student summaries
   - Pedagogical move distributions

## Analysis Tools

### Loading Exported Data

```python
from pathlib import Path
from research.export.trajectory_exporter import AnonymizedDataset

dataset = AnonymizedDataset(Path("./exports/fall_2024"))

# Load individual datasets
interactions = dataset.load_interactions()
mastery = dataset.load_mastery()
summary = dataset.load_summary()

# Get trajectory for a specific student
trajectory = dataset.get_student_trajectory("student_0001")

# Compute learning curves
curves = dataset.compute_learning_curves()
```

### Example Analysis Notebook

See `research/notebooks/analysis_example.ipynb` for examples of:

- Pedagogical move distribution analysis
- Learning curve visualization
- Concept difficulty analysis
- Time-on-task analysis
- Session-level statistics

## Research Questions

Mentor data can support research on:

### Learning Effectiveness

- Do students using AI tutoring achieve higher mastery?
- How does mastery progression compare across teaching styles?
- What is the optimal session length for learning gains?

### Pedagogical Strategies

- Which pedagogical moves are most effective for different concepts?
- How does Socratic questioning compare to direct instruction?
- When should hints be offered for optimal learning?

### Student Behavior

- What patterns indicate productive struggle vs. frustration?
- How do response times correlate with learning?
- Can gaming behavior be accurately detected?

### Concept Analysis

- Which concepts are most difficult for students?
- Do misconception patterns match instructor predictions?
- How do prerequisite relationships affect learning?

## IRB Considerations

When conducting research with Mentor data:

### Data Protection

- Always use anonymized exports for research
- Store data securely with appropriate access controls
- Follow your institution's data retention policies

### Informed Consent

Consider consent processes for:
- Students whose data will be analyzed
- Faculty whose course designs are studied
- Any identifiable information in materials

### Transparency

- Document data collection practices
- Provide opt-out mechanisms where required
- Report aggregate findings back to participants

## Extending Research Tools

### Custom Exporters

Create custom exporters by extending `TrajectoryExporter`:

```python
class CustomExporter(TrajectoryExporter):
    async def export_pedagogical_analysis(
        self,
        course_id: UUID,
        output_path: Path
    ) -> Path:
        # Custom export logic
        interactions = await self._get_interactions(course_id)
        
        # Analyze pedagogical move effectiveness
        move_effectiveness = self._analyze_moves(interactions)
        
        self._write_json(output_path, move_effectiveness)
        return output_path
```

### Custom Analysis

Add new analysis methods to `AnonymizedDataset`:

```python
class ExtendedDataset(AnonymizedDataset):
    def compute_concept_difficulty(self) -> dict[str, float]:
        """Compute difficulty score for each concept."""
        mastery = self.load_mastery()
        
        difficulty = {}
        for concept in set(m['concept_name'] for m in mastery):
            concept_mastery = [
                float(m['mastery_level']) 
                for m in mastery 
                if m['concept_name'] == concept
            ]
            # Lower average mastery = higher difficulty
            difficulty[concept] = 1 - (sum(concept_mastery) / len(concept_mastery))
        
        return difficulty
```

## Data Schema Reference

### Interaction Fields

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Unique identifier |
| student_id | UUID | Student reference |
| session_id | UUID | Session reference |
| course_id | UUID | Course reference |
| concept_id | UUID | Associated concept (nullable) |
| turn_number | int | Position in conversation |
| student_message | text | Student input |
| tutor_response | text | Tutor output |
| pedagogical_move | string | Strategy used |
| response_time_ms | int | Student response time |
| mastery_before | float | Pre-interaction mastery |
| mastery_after | float | Post-interaction mastery |
| created_at | timestamp | Interaction time |

### Pedagogical Moves

| Move | Description |
|------|-------------|
| `socratic` | Guiding question to prompt thinking |
| `scaffold` | Structured support for problem-solving |
| `direct` | Direct explanation or instruction |
| `probe` | Question to assess understanding |
| `hint` | Targeted hint toward solution |
| `encourage` | Positive reinforcement |
| `redirect` | Steering back to topic |
| `summarize` | Recap of key points |
| `correct` | Error correction with explanation |

### Gaming Signals

| Signal | Description |
|--------|-------------|
| `rapid_response` | Response time < 2 seconds |
| `copy_paste` | Detected paste behavior |
| `pattern_matching` | Systematic answer testing |
| `help_abuse` | Excessive hint requests |
| `off_topic` | Unrelated conversation |
| `ai_generated` | Suspected AI-generated input |
