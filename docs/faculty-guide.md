# Faculty Guide

This guide covers everything faculty need to know to create and manage AI tutoring courses in Mentor.

## Course Creation

### Defining Concepts

Concepts are the atomic units of knowledge in your course. Each concept should:

- Have clear learning objectives
- Be appropriately sized (not too broad, not too narrow)
- Include prerequisite relationships

```yaml
concepts:
  - id: variables
    name: "Variables and Data Types"
    description: "Understanding how to store and manipulate data"
    bloom_level: understand  # remember, understand, apply, analyze, evaluate, create
    prerequisites: []
    learning_objectives:
      - "Declare and assign variables"
      - "Identify common data types"
```

### Knowledge Graph

Mentor automatically builds a directed acyclic graph (DAG) from your concept prerequisites. This enables:

- **Adaptive sequencing**: Students progress through concepts in valid orders
- **Prerequisite checking**: Concepts unlock when prerequisites are mastered
- **Learning path visualization**: Students see their progression

Best practices for prerequisites:
- Keep the graph relatively shallow (avoid long chains)
- Identify truly necessary prerequisites, not just "nice to have"
- Consider multiple valid learning paths

### Misconceptions

Documenting common misconceptions helps the tutor provide targeted corrections:

```yaml
misconceptions:
  - concept_id: variables
    misconception: "Variables are like boxes that hold values"
    correction: "Variables are names that reference objects in memory"
    detection_patterns:
      - "copy.*variable"
      - "put.*into"
```

Detection patterns are regular expressions that help identify when a student expresses a misconception.

## Material Processing

### Supported Formats

- **PDF**: Textbooks, lecture notes, papers
- **DOCX**: Word documents
- **Markdown**: Course notes, tutorials
- **Plain text**: Any text content

### Chunking Strategy

Materials are automatically chunked for retrieval. The system uses semantic chunking with:

- Target chunk size: ~512 tokens
- Overlap: 50 tokens between chunks
- Heading preservation: Maintains document structure

### Concept Mapping

After uploading materials, map chunks to concepts for targeted retrieval during tutoring sessions.

## Pedagogical Configuration

### Teaching Styles

| Style | Description | Best For |
|-------|-------------|----------|
| `socratic` | Questions that guide discovery | Critical thinking, deep understanding |
| `scaffold` | Structured support, gradually removed | Complex problem-solving |
| `direct` | Clear explanations and examples | Factual knowledge, procedures |
| `exploratory` | Open-ended investigation | Creative thinking, research skills |

### Difficulty Progression

- **adaptive**: Adjusts based on student performance
- **linear**: Fixed progression through difficulty levels
- **mastery**: Must demonstrate mastery before advancing

### Hint Configuration

```yaml
pedagogy:
  hint_frequency: medium  # low, medium, high
  max_hints_per_problem: 3
  wait_time_seconds: 30  # Time before offering hints
```

## Monitoring Students

### Dashboard Metrics

The faculty dashboard provides:

- **Class Overview**: Aggregate mastery levels, engagement trends
- **At-Risk Students**: Identified by low engagement or struggling patterns
- **Concept Difficulty**: Which concepts students struggle with most
- **Gaming Detection**: Flags for potentially non-learning behavior

### Individual Student View

For each student:
- Mastery levels per concept
- Learning trajectory over time
- Session history with transcripts
- Gaming detection flags

### Gaming Detection

Mentor detects several gaming patterns:

| Signal | Description |
|--------|-------------|
| `rapid_response` | Responses too fast for genuine engagement |
| `copy_paste` | Detected copy-paste behavior |
| `pattern_matching` | Trying answers without understanding |
| `help_abuse` | Requesting hints without attempting problems |
| `off_topic` | Conversations unrelated to course material |

## Assessment Integration

### Verification Reports

Generate verification reports for human assessment:

```
Student: Jane Doe
Course: Introduction to Python
Period: Oct 1 - Nov 15, 2024

Concept Mastery:
- Variables: 92% (Mastered)
- Loops: 78% (Proficient)
- Functions: 65% (Developing)

Interaction Summary:
- Total sessions: 23
- Total time: 8.5 hours
- Pedagogical moves: 45% Socratic, 30% Scaffold, 25% Direct

Gaming Flags: None

Recommendation: Student demonstrates genuine engagement and
progressive mastery. Recommend credit for tutoring participation.
```

### Export for Research

Export anonymized data for learning analytics research:

```python
from research.export import TrajectoryExporter

exporter = TrajectoryExporter(session)
await exporter.export_course_trajectories(
    course_id=course_id,
    output_dir=Path("./exports"),
    anonymize=True,
    format="csv"
)
```

## Best Practices

### Course Design

1. **Start small**: Begin with 5-10 core concepts
2. **Iterate**: Refine based on student performance data
3. **Document misconceptions**: Add them as you discover patterns
4. **Update materials**: Keep content current and relevant

### Student Communication

1. **Set expectations**: Explain how AI tutoring fits into the course
2. **Encourage genuine engagement**: Emphasize learning over completion
3. **Review flags**: Follow up on gaming detection flags personally
4. **Provide feedback**: Use verification reports in conversations

### Quality Assurance

1. **Test the tutor**: Go through sessions yourself before launching
2. **Monitor early sessions**: Watch for issues in first student interactions
3. **Check misconception detection**: Verify patterns catch real issues
4. **Review learning curves**: Ensure students are actually progressing
