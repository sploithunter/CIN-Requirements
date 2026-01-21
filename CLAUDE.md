# CLAUDE.md - Project Guidelines for Claude Code

This file provides context and guidelines for Claude Code when working on the Conversational Requirements Platform.

## Project Overview

This is a full-stack application for AI-powered requirements gathering with:
- **Backend**: FastAPI + SQLAlchemy (async) + PostgreSQL
- **Frontend**: Next.js 14 + TypeScript + TipTap + Liveblocks
- **AI**: Claude API for conversational features

## Development Philosophy

### Test Early, Test Often

**CRITICAL**: Every significant code change should be tested before moving on.

1. **Unit Tests**: Write tests for new functions/methods immediately after implementation
2. **Integration Tests**: Test API endpoints after creating routes
3. **E2E Tests**: Validate complete user flows after major features
4. **Manual Testing**: Run the app locally after each significant change

### Testing Checkpoints

At each major step, ensure:
- [ ] Backend tests pass: `cd backend && pytest tests/ -v`
- [ ] Frontend builds: `cd frontend && npm run build`
- [ ] Type checking passes: Backend `mypy app/`, Frontend `npm run type-check`
- [ ] Linting passes: Backend `ruff check app/`, Frontend `npm run lint`

## Code Style

### Backend (Python)
- Use async/await for all database operations
- Type hints on all function signatures
- Pydantic models for request/response validation
- Follow existing patterns in `app/api/routes/`

### Frontend (TypeScript)
- Strict TypeScript - no `any` types
- React Server Components by default, `"use client"` only when needed
- Use hooks from `lib/hooks/` for data fetching
- Shadcn/ui patterns for components in `components/ui/`

## Key Files Reference

### Backend
- `app/main.py` - FastAPI app entry point
- `app/core/config.py` - Environment configuration
- `app/core/database.py` - Database connection
- `app/api/deps.py` - Dependency injection (auth, db session)
- `app/services/claude_service.py` - AI integration

### Frontend
- `src/app/layout.tsx` - Root layout with providers
- `src/lib/api.ts` - API client for all backend calls
- `src/lib/auth.ts` - Authentication utilities
- `src/providers/AuthProvider.tsx` - Auth context

## Common Tasks

### Adding a New API Endpoint

1. Create/update schema in `app/schemas/`
2. Create/update model in `app/models/` if needed
3. Add route in `app/api/routes/`
4. Register in `app/api/routes/__init__.py`
5. **Write tests** in `tests/`
6. Update API client in `frontend/src/lib/api.ts`

### Adding a New Frontend Page

1. Create page in `src/app/{route}/page.tsx`
2. Add any new components to `src/components/`
3. Add hooks if needed in `src/lib/hooks/`
4. **Test the page** - build and run locally

### Adding a New AI Feature

1. Update `ClaudeService` in `app/services/claude_service.py`
2. Add endpoint in `app/api/routes/ai.py`
3. Add schema in `app/schemas/ai.py`
4. Update `useAI` hook in `frontend/src/lib/hooks/useAI.ts`
5. **Test with real API calls** - mock for unit tests

## Database Migrations

```bash
cd backend
# Create migration after model changes
alembic revision --autogenerate -m "Description"
# Apply migrations
alembic upgrade head
```

## Environment Setup

Backend requires:
- PostgreSQL running on localhost:5432
- Redis running on localhost:6379
- Valid API keys in `.env`

Frontend requires:
- Backend running on localhost:8000
- Valid Liveblocks key in `.env.local`

## Debugging Tips

- Backend logs: Check uvicorn output, add `print()` or use debugger
- Frontend: Use React DevTools, check Network tab
- Database: Use `psql` or pgAdmin to inspect data
- Redis: Use `redis-cli` to check cached data

## Don't Forget

1. **Run tests** after every significant change
2. **Type check** before committing
3. **Lint** your code
4. **Update IMPLEMENTATION_PROGRESS.md** when completing features
5. **Test locally** before considering a feature complete
