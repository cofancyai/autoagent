# ThinkingAgent Backend

AI-powered thinking agent with interactive approval mode for complex decision-making workflows.

## 🎯 Overview

ThinkingAgent is a backend system that enables AI agents to make complex decisions with human oversight through an interactive approval workflow. Built with FastAPI, PostgreSQL, and supporting both Anthropic Claude and OpenRouter APIs, it provides a robust foundation for building collaborative AI systems.

## ✨ Key Features

- **Interactive Approval Workflow**: Present decisions to users with pros/cons analysis
- **Session Management**: Track conversation contexts and agent state
- **Event Sourcing**: Complete audit trail of all decisions and actions
- **Multi-Provider LLM Support**:
  - **Anthropic Claude**: Opus, Sonnet, and Haiku models with prompt caching
  - **OpenRouter**: Access to free and paid models (auto-detected from API key)
- **Hybrid API Design**: REST endpoints for commands, GraphQL for flexible querying (planned)
- **Real-time Updates**: WebSocket support for live progress notifications (planned)
- **Cost Tracking**: Monitor LLM API usage and costs (with $0 for free OpenRouter models)

## 🏗️ Architecture

**Modular Monolith** with clean separation of concerns:

```
app/
├── api/           # REST API endpoints
├── models/        # SQLAlchemy database models
├── schemas/       # Pydantic validation schemas
├── services/      # Business logic layer
├── integrations/  # External API clients (Anthropic)
├── config.py      # Configuration management
├── database.py    # Database setup
└── main.py        # FastAPI application
```

## 📊 Database Schema

**Hybrid Relational + Event Log** approach:

- **Core Tables**: Users, Sessions, Messages, Goals, Approvals, Decisions
- **Monitoring**: LLM API Calls, Execution Logs
- **Audit Trail**: Event Log for complete history

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- **LLM API Key** (choose one):
  - Anthropic API Key (for Claude models)
  - OpenRouter API Key (for free/paid models including Qwen, Claude, GPT, etc.)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd autoagent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your API key:
   # - For Anthropic: ANTHROPIC_API_KEY=sk-ant-...
   # - For OpenRouter: ANTHROPIC_API_KEY=sk-or-v1-... (and optionally OPENROUTER_MODEL)
   ```

   **OpenRouter Configuration** (optional):
   ```bash
   # Example for using free Qwen model via OpenRouter
   ANTHROPIC_API_KEY=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
   OPENROUTER_MODEL=qwen/qwen3-coder:free
   ```

   See [OPENROUTER_INTEGRATION.md](OPENROUTER_INTEGRATION.md) for detailed setup guide.

5. **Start services with Docker Compose**
   ```bash
   docker-compose up -d postgres redis
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the API**
   - API Documentation: http://localhost:8000/api/v1/docs
   - Health Check: http://localhost:8000/health

### Using Docker Compose

Run the entire stack:

```bash
docker-compose up
```

## 📚 API Documentation

### Core Endpoints

**Sessions**
- `POST /api/v1/sessions` - Create new session
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `PATCH /api/v1/sessions/{id}` - Update session
- `DELETE /api/v1/sessions/{id}` - Delete session

**Messages**
- `POST /api/v1/sessions/{id}/messages` - Send message
- `GET /api/v1/sessions/{id}/messages` - Get conversation history

**Approvals** ⭐ Core Feature
- `POST /api/v1/sessions/{id}/approvals` - Create approval checkpoint
- `GET /api/v1/sessions/{id}/approvals` - List approvals
- `GET /api/v1/approvals/{id}` - Get approval details
- `POST /api/v1/approvals/{id}/decide` - Submit decision
- `PATCH /api/v1/approvals/{id}` - Update status (reject)

**Goals**
- `POST /api/v1/sessions/{id}/goals` - Create goal
- `GET /api/v1/sessions/{id}/goals` - List goals
- `PATCH /api/v1/goals/{id}` - Update goal

### Example: Approval Workflow

```python
import httpx

# 1. Create a session
session = httpx.post("http://localhost:8000/api/v1/sessions", json={
    "title": "Build ThinkingAgent Backend"
})
session_id = session.json()["data"]["id"]

# 2. Agent creates approval checkpoint
approval = httpx.post(
    f"http://localhost:8000/api/v1/sessions/{session_id}/approvals",
    json={
        "checkpoint_type": "tech_stack",
        "decision_needed": "Choose technology stack",
        "options": [
            {
                "name": "Python + FastAPI",
                "pros": ["Fast development", "Great AI ecosystem"],
                "cons": ["Slower than compiled languages"]
            },
            {
                "name": "Node.js + Express",
                "pros": ["JavaScript everywhere"],
                "cons": ["Less mature AI tooling"]
            }
        ],
        "recommended_option": 0
    }
)
approval_id = approval.json()["data"]["id"]

# 3. User submits decision
decision = httpx.post(
    f"http://localhost:8000/api/v1/approvals/{approval_id}/decide",
    json={
        "selected_option": 0,
        "modifications": "Use PostgreSQL for database",
        "reasoning": "Better JSON support and reliability"
    }
)
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api/test_approvals.py -v

# Run only critical tests
pytest -m "not slow"
```

### Test Coverage

Current coverage: **~65%** (MVP target: 60-70%)

Priority test coverage:
- ✅ Approval workflow (90%+)
- ✅ API endpoints (70%+)
- ✅ Core services (70%+)
- ✅ Models & DB (60%+)

## 🔧 Development

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## 📈 Monitoring

### LLM API Cost Tracking

The system automatically tracks:
- Token usage per request
- Cost per model
- Latency metrics
- Provider distribution

Query costs via database:
```sql
SELECT
    provider,
    model,
    SUM(total_cost) as total_spent,
    COUNT(*) as num_calls
FROM llm_api_calls
WHERE created_at >= NOW() - INTERVAL '1 day'
GROUP BY provider, model;
```

## 🏷️ Technology Stack

**Approved in Design Phase:**
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL 15+ (with asyncpg)
- **Cache**: Redis 7+
- **LLM Provider**: Anthropic Claude (Opus, Sonnet, Haiku)
- **ORM**: SQLAlchemy (async)
- **Testing**: pytest + pytest-asyncio
- **CI/CD**: GitHub Actions

## 📋 Roadmap

### MVP (Weeks 1-3) ✅ Complete
- [x] Project structure and configuration
- [x] Database models and schemas
- [x] Core services (session, approval, message)
- [x] REST API endpoints
- [x] Anthropic Claude integration
- [x] Critical path tests
- [x] CI/CD pipeline
- [x] Documentation

### Phase 2 (Weeks 4-6)
- [ ] GraphQL schema and resolvers
- [ ] WebSocket real-time updates
- [ ] Thinking process service
- [ ] Prompt caching optimization
- [ ] Enhanced error handling
- [ ] Integration tests expansion

### Phase 3 (Weeks 7+)
- [ ] Admin dashboard
- [ ] Cost optimization layer
- [ ] Advanced thinking strategies
- [ ] Multi-user support
- [ ] OpenAI fallback provider
- [ ] Performance optimization
- [ ] Security hardening

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Run linting and tests
5. Submit a pull request

## 📝 License

[Add your license here]

## 🙏 Acknowledgments

Built with the collaborative approval process demonstrated by this project itself!

---

**Questions or Issues?**

Open an issue or reach out to the development team.
