# Architecture Overview

Mentor is designed as a modular, extensible platform for AI-powered tutoring with full faculty control.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Faculty   │  │   Student   │  │     Shared Components   │ │
│  │  Dashboard  │  │   Tutor     │  │   (Auth, Navigation)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │   Auth   │  │  Courses │  │  Tutor   │  │    Assessment    ││
│  │  Routes  │  │  Routes  │  │  Routes  │  │      Routes      ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Core Modules                             │
│ ┌───────────────┐ ┌───────────────┐ ┌─────────────────────────┐│
│ │    Course     │ │   Material    │ │     Tutor Runtime       ││
│ │  Definition   │ │  Processing   │ │  (LLM, RAG, Dialogue)   ││
│ └───────────────┘ └───────────────┘ └─────────────────────────┘│
│ ┌───────────────┐ ┌───────────────────────────────────────────┐│
│ │ Student State │ │           Assessment Engine               ││
│ │   (BKT)       │ │    (Gaming Detection, Verification)       ││
│ └───────────────┘ └───────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                 │
│  ┌──────────────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │   PostgreSQL     │  │  Redis   │  │   Vector Store       │  │
│  │   (+ pgvector)   │  │  Cache   │  │   (pgvector)         │  │
│  └──────────────────┘  └──────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │  Ollama  │  │ Together │  │OpenRouter│  │ Anthropic/OpenAI ││
│  │  (local) │  │    AI    │  │          │  │                  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### Course Definition Module

Manages the academic structure of courses:

- **Knowledge Graph**: DAG-based concept relationships with topological sorting
- **Misconceptions Registry**: Pattern-based misconception detection
- **Pedagogy Configuration**: Teaching style and progression settings

### Material Processing Module

Handles course content:

- **Document Processor**: Extracts text from PDF, DOCX, Markdown
- **Semantic Chunker**: Splits content into retrievable chunks
- **Embedder**: Generates vector embeddings (local or API-based)

### Tutor Runtime Module

Powers the tutoring interaction:

- **LLM Client**: Abstraction over multiple providers with streaming support
- **Retriever**: Vector similarity search for relevant content
- **Dialogue Manager**: Selects pedagogical moves and manages conversation
- **Response Generator**: Constructs context-aware tutor responses

### Student State Module

Tracks learning progress:

- **Mastery Tracker**: Bayesian Knowledge Tracing (BKT) implementation
- **Engagement Metrics**: Time-on-task, interaction patterns
- **State Manager**: Persistent state across sessions

### Assessment Engine

Provides verification capabilities:

- **Gaming Detector**: Identifies non-learning behavior patterns
- **Verification Report Generator**: Creates human-readable assessment summaries

## Data Models

### Key Entities

```
User ──────────────────┐
  │                    │
  ├── Institution      │
  │                    │
  ├── Course ◄─────────┘ (faculty creates)
  │     │
  │     ├── Concept
  │     │     └── Misconception
  │     │
  │     ├── Material
  │     │     └── MaterialChunk (with embedding)
  │     │
  │     └── CourseEnrollment ◄── Student
  │           │
  │           └── StudentState
  │                 └── Interaction
  │
  └── VerificationReport
```

### Vector Storage

Material chunks are stored with pgvector embeddings:

```sql
CREATE TABLE material_chunks (
    id UUID PRIMARY KEY,
    material_id UUID REFERENCES materials(id),
    content TEXT NOT NULL,
    embedding VECTOR(384),  -- dimension depends on model
    ...
);

CREATE INDEX ON material_chunks 
USING ivfflat (embedding vector_cosine_ops);
```

## Tutoring Flow

```
Student Message
      │
      ▼
┌─────────────────┐
│ Gaming Detection│──── Flag if suspicious
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Context Building│
│  - History      │
│  - Student state│
│  - Relevant docs│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Pedagogical Move │
│   Selection     │
│  - Based on:    │
│    - Mastery    │
│    - Config     │
│    - History    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LLM Generation │
│  (streaming)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Mastery Update  │
│   (BKT)         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Log Interaction │
└────────┬────────┘
         │
         ▼
   Tutor Response
```

## Bayesian Knowledge Tracing

Student mastery is estimated using BKT:

```
P(Ln) = P(Ln-1) + (1 - P(Ln-1)) * P(T)  // if correct
P(Ln) = P(Ln-1) * (1 - P(F))            // if incorrect

Where:
- P(L) = probability of mastery
- P(T) = probability of learning/transition
- P(F) = probability of forgetting
- P(G) = probability of guessing correctly
- P(S) = probability of slipping (error despite mastery)
```

## Scalability Considerations

### Horizontal Scaling

- **API**: Stateless FastAPI instances behind load balancer
- **Database**: PostgreSQL with read replicas
- **Cache**: Redis cluster for session state
- **LLM**: Multiple provider fallback for availability

### Performance Optimizations

- **Async everywhere**: All I/O operations are async
- **Connection pooling**: SQLAlchemy async pool
- **Streaming responses**: LLM responses stream to client
- **Batch embeddings**: Material processing batches embedding calls

## Security

### Authentication

- JWT tokens with configurable expiration
- Refresh token rotation
- Role-based access control (faculty, student, admin)

### Data Protection

- Anonymization tools for research exports
- Configurable data retention policies
- Audit logging for sensitive operations

### Input Validation

- Pydantic schemas for all API inputs
- SQL injection prevention via SQLAlchemy ORM
- Content sanitization for user inputs
