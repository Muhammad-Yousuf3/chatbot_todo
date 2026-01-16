# Frontend Quickstart Guide

**Feature**: 006-frontend-chat-ui
**Purpose**: Step-by-step guide to run the frontend locally

---

## Prerequisites

- Node.js 20+ (LTS recommended)
- npm 10+ or pnpm 8+
- Backend running at `http://localhost:8000` (see backend quickstart)

---

## Setup

### 1. Create Next.js Application

```bash
# From repository root
cd /home/muhammad-yousuf/Desktop/Chatbot_TODO

# Create frontend directory
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"

# Navigate to frontend
cd frontend
```

### 2. Install Dependencies

```bash
# Core dependencies
npm install swr

# OpenAI ChatKit
npm install @openai/chatkit-react

# Development dependencies
npm install -D @types/node
```

### 3. Configure Environment

Create `.env.local` in the `frontend` directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Authentication (set to false for mock auth)
NEXT_PUBLIC_AUTH_ENABLED=false
```

### 4. Start Development Server

```bash
npm run dev
```

Frontend will be available at `http://localhost:3000`.

---

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with providers
│   ├── page.tsx             # Landing page
│   ├── login/
│   │   └── page.tsx         # Login page
│   ├── chat/
│   │   └── page.tsx         # Chat interface (ChatKit)
│   └── dashboard/
│       ├── page.tsx         # Metrics dashboard
│       └── traces/
│           └── page.tsx     # Decision trace viewer
├── components/
│   ├── ui/                  # Base UI components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Skeleton.tsx
│   │   └── ...
│   ├── chat/                # Chat components
│   │   ├── ChatContainer.tsx
│   │   ├── MessageList.tsx
│   │   └── ...
│   ├── dashboard/           # Dashboard components
│   │   ├── MetricsCard.tsx
│   │   ├── ToolUsageChart.tsx
│   │   └── ...
│   └── trace/               # Trace viewer components
│       ├── DecisionTimeline.tsx
│       ├── ToolInvocationCard.tsx
│       └── ...
├── lib/
│   ├── api.ts               # API client
│   ├── hooks/               # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useConversations.ts
│   │   └── useMetrics.ts
│   └── utils.ts             # Utility functions
├── contexts/
│   └── AuthContext.tsx      # Authentication context
├── types/
│   └── index.ts             # TypeScript type definitions
├── tailwind.config.ts       # Tailwind configuration
└── next.config.js           # Next.js configuration
```

---

## Running with Backend

### Terminal 1: Backend

```bash
cd backend
source .venv/bin/activate
uvicorn src.main:app --reload
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

### Verify Integration

1. Open `http://localhost:3000`
2. Click "Start Chatting"
3. Login with any email/password (mock auth)
4. Send a message: "Add a task to buy groceries"
5. Verify agent response appears

---

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint

# Type check
npx tsc --noEmit
```

---

## Troubleshooting

### CORS Errors

Ensure backend has CORS configured for `http://localhost:3000`:

```python
# backend/src/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### API Connection Failed

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Restart development server after env changes

### Authentication Issues

For mock auth mode, ensure:
1. `NEXT_PUBLIC_AUTH_ENABLED=false` in `.env.local`
2. Backend has `AUTH_MODE=mock` in its `.env`

---

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import project in Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL`: Your backend URL
   - `NEXT_PUBLIC_AUTH_ENABLED`: `false` or `true`
4. Deploy

### Docker

```bash
# Build image
docker build -t chatbot-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=https://api.example.com \
  chatbot-frontend
```

---

## Next Steps

1. Implement pages following spec requirements
2. Add ChatKit integration for chat interface
3. Build dashboard with metrics cards
4. Implement decision trace viewer
5. Polish styling with Tailwind
6. Test error handling scenarios
