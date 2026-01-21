import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import get_settings
from app.core.security import create_access_token
from app.models.user import User
from app.models.session import Session, SessionStatus
from app.models.message import Message


# Use sqlite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create a test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test HTTP client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        oauth_provider="google",
        oauth_id="test-oauth-id",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def auth_headers(test_user: User) -> dict:
    """Create authorization headers for the test user."""
    token = create_access_token(test_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def test_session(db_session: AsyncSession, test_user: User) -> Session:
    """Create a test session."""
    session = Session(
        id=uuid4(),
        owner_id=test_user.id,
        title="Test Session",
        description="A test session for unit tests",
        status=SessionStatus.IN_PROGRESS,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest_asyncio.fixture(scope="function")
async def test_message(db_session: AsyncSession, test_session: Session) -> Message:
    """Create a test message."""
    from app.models.message import MessageRole, MessageType

    message = Message(
        id=uuid4(),
        session_id=test_session.id,
        role=MessageRole.USER,
        message_type=MessageType.TEXT,
        content="Test message content",
    )
    db_session.add(message)
    await db_session.commit()
    await db_session.refresh(message)
    return message
