# AI-Powered Todo Chatbot

A full-stack conversational AI application for managing todo tasks through natural language. Built with FastAPI, Next.js, and Google Gemini LLM, featuring JWT authentication and Kubernetes deployment support.

## Features

- **Natural Language Task Management** - Create, update, complete, and delete tasks through conversational AI
- **Conversation Persistence** - Full chat history saved across sessions
- **JWT Authentication** - Secure, stateless token-based authentication
- **AI Agent with Tool Use** - Gemini LLM with MCP (Model Context Protocol) tools for safe, auditable AI actions
- **Observability** - Built-in logging and analytics for agent decisions
- **Kubernetes Ready** - Helm charts for local Minikube and production deployments

## Tech Stack

### Backend
- **Python 3.11+** with FastAPI
- **PostgreSQL** (Neon) via SQLModel ORM
- **Google Gemini API** (gemini-2.5-flash)
- **MCP SDK** for AI tool orchestration
- **JWT** (python-jose) for authentication

### Frontend
- **Next.js 14+** with TypeScript
- **React 18+** with Tailwind CSS
- **SWR** for data fetching

### Infrastructure
- **Docker** (multi-stage builds)
- **Kubernetes** with Helm charts
- **Nginx** reverse proxy

## Project Structure

```
Chatbot_TODO/
├── backend/                    # FastAPI Python service
│   ├── src/
│   │   ├── api/               # REST API routes & schemas
│   │   ├── agent/             # AI decision engine
│   │   ├── llm_runtime/       # Gemini LLM integration
│   │   ├── mcp_server/        # MCP tools (task CRUD)
│   │   ├── models/            # SQLModel data models
│   │   ├── observability/     # Logging & analytics
│   │   └── main.py            # FastAPI entry point
│   ├── tests/                 # Pytest test suites
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                   # Next.js React application
│   ├── app/                   # App router pages
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── helm/                       # Kubernetes Helm charts
│   └── todo-chatbot/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── values-local.yaml
└── specs/                      # Feature specifications (SDD)
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL database (or [Neon](https://neon.tech) account)
- Google Gemini API key
- Docker (optional, for containerized deployment)
- Minikube + Helm (optional, for Kubernetes deployment)

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Required
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
JWT_SECRET=your-secret-key-minimum-32-characters
GEMINI_API_KEY=your-gemini-api-key

# Optional
FRONTEND_URL=http://localhost:3000
GEMINI_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.0
LLM_MAX_TOKENS=1024
JWT_EXPIRATION_HOURS=24
MAX_TOOL_ITERATIONS=5
```

## Installation

### Backend

```bash
cd backend

# Install dependencies
uv sync

# Run database migrations (if applicable)
# Tables are auto-created via SQLModel

# Start development server
uv run uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000` and will proxy API requests to the backend at `http://localhost:8000`.

## Running Tests

```bash
cd backend
uv run pytest
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login (returns JWT) |
| `/api/conversations/` | GET | List user conversations |
| `/api/conversations/` | POST | Create new conversation |
| `/api/chat/` | POST | Send message and get AI response |
| `/api/tasks/` | GET | List user tasks |
| `/health` | GET | Health check |

## Docker Deployment

### Build Images

```bash
# Backend
cd backend
docker build -t todo-backend:dev .

# Frontend
cd frontend
docker build -t todo-frontend:dev .
```

### Run Containers

```bash
# Backend
docker run -p 8000:8000 \
  -e DATABASE_URL="your-database-url" \
  -e JWT_SECRET="your-jwt-secret" \
  -e GEMINI_API_KEY="your-gemini-key" \
  todo-backend:dev

# Frontend
docker run -p 80:80 todo-frontend:dev
```

## Kubernetes Deployment (Minikube)

```bash
# Start Minikube
minikube start

# Load images into Minikube
minikube image load todo-backend:dev
minikube image load todo-frontend:dev

# Deploy with Helm
helm install todo-chatbot ./helm/todo-chatbot \
  -f helm/todo-chatbot/values-local.yaml \
  --set backend.secrets.databaseUrl="<DATABASE_URL>" \
  --set backend.secrets.jwtSecret="<JWT_SECRET>" \
  --set backend.secrets.geminiApiKey="<GEMINI_API_KEY>"

# Get service URL
minikube service todo-chatbot-frontend --url
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│  PostgreSQL │
│  (Next.js)  │     │  (FastAPI)  │     │   (Neon)    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   Gemini    │
                    │     LLM     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  MCP Tools  │
                    │ (Task CRUD) │
                    └─────────────┘
```

**Key Design Decisions:**
- **Stateless Backend** - All state persists to PostgreSQL for horizontal scaling
- **MCP Tools for AI Safety** - AI agent actions are routed through MCP tools, never direct database access
- **JWT Authentication** - Token-based auth for distributed deployments
- **Spec-Driven Development** - Features are specified before implementation (see `specs/` directory)

## Data Models

| Model | Description |
|-------|-------------|
| `User` | User account (email, password hash) |
| `Conversation` | Chat session with title and metadata |
| `Message` | Individual message (role: user/assistant/system) |
| `Task` | Todo item (description, status: pending/completed) |

## Development

This project follows **Spec-Driven Development (SDD)**. Feature specifications are located in the `specs/` directory:

- `001-conversation-persistence` - Chat history persistence
- `002-mcp-task-tools` - MCP tool definitions
- `003-agent-behavior-policy` - Agent decision rules
- `004-agent-observability` - Logging and analytics
- `005-llm-agent-runtime` - Gemini integration
- `006-frontend-chat-ui` - UI specifications
- `007-jwt-authentication` - JWT auth implementation
- `008-local-k8s-deployment` - Kubernetes deployment

## License

This project is proprietary. All rights reserved.
