# ThinkingAgent Architecture

## Design Decisions

This document records all major architectural decisions made during the interactive approval process.

## ✅ Approved Decisions

### 1. Technology Stack (Checkpoint 1)
**Decision**: Python + FastAPI + PostgreSQL

**Options Considered**:
- Python + FastAPI + PostgreSQL ⭐ SELECTED
- Node.js + NestJS + MongoDB
- Go + Gin + PostgreSQL

**Reasoning**:
- Excellent AI/ML ecosystem
- FastAPI provides automatic OpenAPI docs
- Strong async support for AI API calls
- Rich typing with Pydantic
- Large community for AI applications

**Timeline Impact**: 2-3 weeks MVP (Fast)

---

### 2. System Architecture (Checkpoint 2)
**Decision**: Modular Monolith

**Options Considered**:
- Modular Monolith ⭐ SELECTED
- Microservices Architecture
- Event-Driven Layered Architecture

**Reasoning**:
- Clean separation of concerns via modules
- Easy to develop and debug
- Single deployment unit
- Can evolve to microservices later
- Fast development cycle

**Modules**:
- API Layer (REST + WebSocket)
- Core Business Logic (Thinking, Approval, Session Services)
- Integration Layer (LLM Providers)
- Data Access Layer (SQLAlchemy + Redis)

---

### 3. Database Schema (Checkpoint 3)
**Decision**: Hybrid Relational + Event Log

**Options Considered**:
- Event-Sourced Schema
- Traditional Relational Schema
- Hybrid Relational + Event Log ⭐ SELECTED

**Reasoning**:
- Best of both worlds
- Fast queries on relational tables
- Complete audit trail in event log
- Easy to understand and query
- Flexible for future changes

**Core Tables**:
- users, sessions, messages, goals
- thinking_processes, approval_checkpoints, decisions
- execution_logs, llm_api_calls
- event_log (complete audit trail)

---

### 4. API Design (Checkpoint 4)
**Decision**: Hybrid REST + GraphQL

**Options Considered**:
- Resource-Oriented REST API
- RPC-Style API (Action-Oriented)
- Hybrid REST + GraphQL ⭐ SELECTED

**Reasoning**:
- REST for simple commands (clear semantics)
- GraphQL for complex queries (fetch exactly what you need)
- No over-fetching or under-fetching data
- Self-documenting (GraphQL introspection)
- Easy to build rich UIs
- WebSocket for real-time updates

**Endpoints**:
- REST: Commands and mutations
- GraphQL: Flexible querying (Phase 2)
- WebSocket: Real-time events (Phase 2)

---

### 5. AI Integration Strategy (Checkpoint 5)
**Decision**: Anthropic-First (Single Provider)

**Options Considered**:
- Multi-Provider with Task-Based Routing
- Anthropic-First (Single Provider) ⭐ SELECTED
- Provider-Agnostic with Unified Interface

**Reasoning**:
- Simplicity: Single provider = less complexity
- Quality: Claude perfect for thinking/reasoning
- Cost Efficiency: Prompt caching (50-90% savings)
- Context: 200K tokens across all models
- Extended Thinking: Claude's thinking mode
- MVP Speed: Faster development

**Model Selection**:
- Opus 4: Deep research, complex reasoning, architecture
- Sonnet 4.5: Code generation, planning, approvals
- Haiku 4: Quick responses, simple tasks

**Cost Estimate**: $80-125/month with caching

---

### 6. Testing Strategy (Checkpoint 6)
**Decision**: Pragmatic Testing (MVP-Focused)

**Options Considered**:
- Comprehensive Multi-Layer Testing
- Pragmatic Testing (MVP-Focused) ⭐ SELECTED
- Manual Testing Only

**Reasoning**:
- Faster MVP delivery
- Focus on what matters (approval workflow)
- Lower initial overhead
- Incremental coverage growth
- Good balance speed/quality

**Coverage Strategy**:
- Phase 1 (MVP): 60-70% overall
  - Critical approval flow: 90%+
  - API endpoints: 70%+
  - Core services: 70%+
- Phase 2: 75-80%
- Phase 3: 85%+

---

## Architecture Patterns

### Layered Architecture

```
┌─────────────────────────────────────┐
│         API Layer                   │
│  (REST, GraphQL, WebSocket)         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Business Logic Layer           │
│  (Services: Session, Approval,      │
│   Thinking, Message)                │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Integration Layer              │
│  (Anthropic Client, External APIs)  │
└─────────────────────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Data Access Layer              │
│  (SQLAlchemy ORM, Redis Cache)      │
└─────────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
   PostgreSQL      Redis
```

### Request Flow

```
User Request
    │
    ▼
API Endpoint (FastAPI)
    │
    ▼
Service Layer (Business Logic)
    │
    ├──> Database (via ORM)
    │
    └──> Anthropic Client (LLM API)
         │
         └──> Event Log (Audit Trail)
    │
    ▼
Response to User
```

## Data Flow

### Approval Workflow

```
1. User Request
   → Create Session

2. Agent Analysis
   → Thinking Process
   → Generate Options

3. Create Approval Checkpoint
   → Store in DB
   → Log Event
   → Notify User (WebSocket)

4. User Decision
   → Validate Selection
   → Store Decision
   → Update Checkpoint Status
   → Log Event

5. Agent Execution
   → Execute with Approved Option
   → Log Execution
   → Update Goal Status
```

## Scalability Considerations

### Current (MVP)
- Single server deployment
- Vertical scaling
- Connection pooling
- Database indexing

### Future (Phase 2+)
- Horizontal scaling (multiple servers)
- Load balancing
- Redis caching layer
- Background task queue (Celery)
- Database read replicas
- CDN for static assets

## Security Architecture

### Current (MVP)
- CORS configuration
- Input validation (Pydantic)
- SQL injection prevention (ORM)
- Environment variable secrets

### Future (Phase 2+)
- JWT authentication
- API rate limiting
- Role-based access control (RBAC)
- Encryption at rest
- Audit logging
- OWASP compliance

## Monitoring & Observability

### Implemented
- Health check endpoint
- Event log (audit trail)
- LLM API cost tracking

### Planned
- Prometheus metrics
- Structured logging
- Distributed tracing
- Error tracking (Sentry)
- Performance monitoring

---

This architecture was designed through an interactive approval process, with each decision carefully evaluated and approved before implementation.
