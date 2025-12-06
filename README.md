# Mentor

An open-source platform for faculty-controlled AI tutoring and assessment.

Mentor enables faculty to create personalized AI tutors from their course materials while maintaining full control over pedagogy, tracking student learning trajectories, and generating verification reports for human assessment.

## Features

- **Faculty-Controlled Pedagogy**: Define teaching styles, hint frequencies, and difficulty progression
- **Knowledge Graph**: Model course concepts with prerequisites and learning objectives
- **Misconception Detection**: Document and automatically detect common student misconceptions
- **Adaptive Tutoring**: Bayesian Knowledge Tracing estimates mastery and adapts instruction
- **Gaming Detection**: Identify non-learning behaviors like rapid responses or copy-paste
- **Verification Reports**: Generate summaries for human assessment of student learning
- **Research Tools**: Export anonymized data for learning analytics research
- **Multiple LLM Support**: Use local models (Ollama) or cloud providers (Together, OpenRouter, Anthropic, OpenAI)

## Quick Start

```bash
# Clone and setup
git clone https://github.com/your-org/mentor.git
cd mentor
cp .env.example .env

# Start with Docker
docker compose up -d

# Run migrations
docker compose exec api alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

## Architecture

```
mentor/
├── mentor/                 # Backend (Python/FastAPI)
│   ├── api/               # REST API routes
│   ├── core/              # Core modules
│   │   ├── course_definition/    # Knowledge graphs, misconceptions
│   │   ├── material_processing/  # Document processing, embeddings
│   │   ├── tutor_runtime/        # LLM client, dialogue management
│   │   ├── student_state/        # Mastery tracking (BKT)
│   │   └── assessment_engine/    # Gaming detection, verification
│   └── models/            # Database models
├── frontend/              # React frontend
├── research/              # Research tools and notebooks
├── examples/              # Example course configurations
└── docs/                  # Documentation
```

## Documentation

- [Getting Started](docs/getting-started.md) - Setup and installation
- [Faculty Guide](docs/faculty-guide.md) - Creating and managing courses
- [Architecture](docs/architecture.md) - System design overview
- [API Reference](docs/api-reference.md) - REST API documentation
- [Research Guide](docs/research-guide.md) - Data export and analysis

## Technology Stack

**Backend**
- Python 3.11+
- FastAPI with async SQLAlchemy
- PostgreSQL 16 with pgvector
- Redis for caching

**Frontend**
- React 18 with TypeScript
- Tailwind CSS
- React Query + Zustand

**LLM Integration**
- Ollama (local)
- Together.ai, OpenRouter, Anthropic, OpenAI (cloud)

## Development

```bash
# Backend development
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn mentor.api.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev
```

## Example Course

See `examples/intro_to_python.yaml` for a complete course configuration:

```yaml
course:
  name: "Introduction to Python Programming"
  code: "CS101"

concepts:
  - id: variables
    name: "Variables and Data Types"
    prerequisites: []
    
  - id: loops
    name: "Loops and Iteration"
    prerequisites: [conditionals]

misconceptions:
  - concept_id: loops
    misconception: "range(5) includes the number 5"
    correction: "range(5) generates 0-4. The stop value is exclusive."
```

## Research

Export anonymized learning data for research:

```python
from research.export import TrajectoryExporter

exporter = TrajectoryExporter(session)
await exporter.export_course_trajectories(
    course_id=course_id,
    output_dir=Path("./exports"),
    anonymize=True
)
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.
