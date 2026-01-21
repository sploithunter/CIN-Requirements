# Conversational Requirements Platform

An AI-powered platform for gathering, documenting, and managing software requirements through natural conversation.

## Features

- **AI-Powered Conversations**: Chat with Claude to gather and refine requirements
- **Smart Questionnaires**: Auto-generate targeted questionnaires based on context
- **Real-time Collaboration**: Work together with Liveblocks-powered collaboration
- **Rich Text Editor**: TipTap-based editor with requirement-specific formatting
- **Voice Input**: Speech-to-text for hands-free requirement capture
- **Document Export**: Generate professional DOCX or Markdown documents
- **OAuth Authentication**: Sign in with Google or Microsoft

## Tech Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **SQLAlchemy** - Async ORM with PostgreSQL
- **Alembic** - Database migrations
- **Anthropic Claude** - AI-powered features
- **Cloudflare R2** - S3-compatible object storage
- **Redis** - Caching and session management

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **TipTap** - Rich text editor
- **Liveblocks** - Real-time collaboration
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment file and configure
cp .env.example .env
# Edit .env with your values

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file and configure
cp .env.example .env.local
# Edit .env.local with your values

# Start development server
npm run dev
```

### Environment Variables

#### Backend (.env)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing key (min 32 chars) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `MICROSOFT_CLIENT_ID` | Microsoft OAuth client ID |
| `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth client secret |
| `ANTHROPIC_API_KEY` | Claude API key |
| `S3_ENDPOINT_URL` | R2/S3 endpoint URL |
| `S3_ACCESS_KEY` | R2/S3 access key |
| `S3_SECRET_KEY` | R2/S3 secret key |
| `S3_BUCKET_NAME` | Storage bucket name |
| `LIVEBLOCKS_SECRET_KEY` | Liveblocks secret key |

#### Frontend (.env.local)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |
| `NEXT_PUBLIC_LIVEBLOCKS_PUBLIC_KEY` | Liveblocks public key |

## Project Structure

```
conversational-requirements/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/       # API endpoints
│   │   │   └── deps.py       # Dependencies
│   │   ├── core/             # Config, DB, security
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── services/         # Business logic
│   ├── alembic/              # Database migrations
│   └── tests/                # Backend tests
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages
│       ├── components/       # React components
│       ├── lib/              # Utilities & hooks
│       ├── providers/        # Context providers
│       └── types/            # TypeScript types
└── .github/workflows/        # CI/CD
```

## API Endpoints

### Authentication
- `GET /api/v1/auth/google/authorize` - Get Google OAuth URL
- `POST /api/v1/auth/google/callback` - Handle Google OAuth callback
- `GET /api/v1/auth/microsoft/authorize` - Get Microsoft OAuth URL
- `POST /api/v1/auth/microsoft/callback` - Handle Microsoft OAuth callback
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user

### Sessions
- `POST /api/v1/sessions` - Create session
- `GET /api/v1/sessions` - List sessions
- `GET /api/v1/sessions/{id}` - Get session
- `PATCH /api/v1/sessions/{id}` - Update session
- `DELETE /api/v1/sessions/{id}` - Delete session
- `POST /api/v1/sessions/{id}/liveblocks-token` - Get collaboration token

### AI
- `POST /api/v1/ai/{session_id}/chat` - Send message
- `POST /api/v1/ai/{session_id}/chat/stream` - Stream message
- `POST /api/v1/ai/{session_id}/questionnaire` - Generate questionnaire
- `POST /api/v1/ai/{session_id}/questionnaire/answer` - Submit answers
- `POST /api/v1/ai/{session_id}/suggest-requirements` - Get suggestions
- `GET /api/v1/ai/{session_id}/messages` - Get message history

### Media
- `POST /api/v1/media/{session_id}/upload` - Upload file
- `GET /api/v1/media/{session_id}/files` - List files
- `DELETE /api/v1/media/{session_id}/files/{id}` - Delete file

### Documents
- `POST /api/v1/documents/{session_id}/generate/requirements` - Generate doc
- `POST /api/v1/documents/{session_id}/generate/summary` - Get summary
- `POST /api/v1/documents/{session_id}/export` - Export session data

## Development

### Running Tests

```bash
# Backend
cd backend
pytest tests/ -v --cov=app

# Frontend
cd frontend
npm run lint
npm run type-check
```

### Code Style

Backend uses Ruff for linting and formatting:
```bash
ruff check app/
ruff format app/
```

Frontend uses ESLint:
```bash
npm run lint
```

## Deployment

### Docker

```bash
# Backend
cd backend
docker build -t cr-api .
docker run -p 8000:8000 --env-file .env cr-api

# Frontend
cd frontend
docker build -t cr-frontend .
docker run -p 3000:3000 cr-frontend
```

### Production Considerations

- Use a production-grade ASGI server (Gunicorn with Uvicorn workers)
- Set up proper database connection pooling
- Configure Redis for session caching
- Use CDN for static assets
- Enable HTTPS with proper certificates
- Set up monitoring and logging

## License

MIT
