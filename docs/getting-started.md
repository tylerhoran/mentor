# Getting Started with Mentor

This guide will help you set up and run Mentor locally for development.

## Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development without Docker)
- Git

## Quick Start with Docker

The fastest way to get Mentor running is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/your-org/mentor.git
cd mentor

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Access the application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## Local Development Setup

### Backend

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL and Redis (via Docker)
docker compose up -d postgres redis

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://mentor:mentor@localhost:5432/mentor"
export REDIS_URL="redis://localhost:6379"

# Run migrations
alembic upgrade head

# Start the API server
uvicorn mentor.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### LLM Setup

Mentor supports multiple LLM providers. For local development, we recommend Ollama:

```bash
# Start Ollama (included in docker-compose)
docker compose up -d ollama

# Pull a model
docker compose exec ollama ollama pull llama3.2

# Or use an external provider by setting environment variables:
# TOGETHER_API_KEY=your-key
# OPENROUTER_API_KEY=your-key
# ANTHROPIC_API_KEY=your-key
# OPENAI_API_KEY=your-key
```

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `LLM_PROVIDER` | LLM provider (ollama, together, openrouter, anthropic, openai) | ollama |
| `LLM_MODEL` | Model name | llama3.2 |
| `OLLAMA_HOST` | Ollama server URL | http://localhost:11434 |
| `EMBEDDING_MODEL` | Sentence transformer model | all-MiniLM-L6-v2 |

## Creating Your First Course

1. Register as a faculty member at http://localhost:3000/register
2. Navigate to the Faculty Dashboard
3. Click "Create Course"
4. Define concepts and their prerequisites
5. Upload course materials (PDF, DOCX, or Markdown)
6. Configure pedagogical settings
7. Share the enrollment code with students

## Project Structure

```
mentor/
├── mentor/                 # Backend Python package
│   ├── api/               # FastAPI routes and schemas
│   ├── core/              # Core business logic
│   │   ├── course_definition/
│   │   ├── material_processing/
│   │   ├── tutor_runtime/
│   │   ├── student_state/
│   │   └── assessment_engine/
│   └── models/            # SQLAlchemy models
├── frontend/              # React frontend
│   └── src/
│       ├── api/          # API client
│       ├── components/   # Reusable UI components
│       ├── pages/        # Page components
│       └── stores/       # Zustand state stores
├── research/             # Research tools
│   ├── export/          # Data export utilities
│   └── notebooks/       # Analysis notebooks
├── examples/            # Example course configurations
└── docs/               # Documentation
```

## Next Steps

- Read the [Faculty Guide](./faculty-guide.md) for course creation details
- Review the [API Reference](./api-reference.md) for integration
- Check [Architecture](./architecture.md) for system design details
- See [Research Guide](./research-guide.md) for data analysis
