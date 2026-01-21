"""
AI endpoint tests using real Claude API calls.
These tests use Haiku for cost efficiency.
"""
import pytest
from httpx import AsyncClient

from app.models.session import Session


@pytest.mark.asyncio
async def test_chat_endpoint(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test non-streaming chat with real Claude API."""
    response = await client.post(
        f"/api/v1/ai/{test_session.id}/chat",
        json={
            "message": "Say exactly: Hello Test",
            "include_history": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert "Hello" in data["content"]
    assert data["input_tokens"] > 0
    assert data["output_tokens"] > 0


@pytest.mark.asyncio
async def test_chat_endpoint_unauthorized(client: AsyncClient, test_session: Session):
    """Test that chat endpoint requires authentication."""
    response = await client.post(
        f"/api/v1/ai/{test_session.id}/chat",
        json={"message": "Hello"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_with_history(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test chat with conversation history."""
    # First message
    response1 = await client.post(
        f"/api/v1/ai/{test_session.id}/chat",
        json={
            "message": "Remember this number: 42",
            "include_history": False,
        },
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Second message with history
    response2 = await client.post(
        f"/api/v1/ai/{test_session.id}/chat",
        json={
            "message": "What number did I ask you to remember?",
            "include_history": True,
            "max_history_messages": 10,
        },
        headers=auth_headers,
    )
    assert response2.status_code == 200
    data = response2.json()
    assert "42" in data["content"]


@pytest.mark.asyncio
async def test_chat_stream_endpoint(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test streaming chat endpoint."""
    response = await client.post(
        f"/api/v1/ai/{test_session.id}/chat/stream",
        json={
            "message": "Say: Hi",
            "include_history": False,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Check that we got SSE data
    content = response.text
    assert "data:" in content
    assert "[DONE]" in content


@pytest.mark.asyncio
async def test_questionnaire_generation(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test questionnaire generation with real Claude API."""
    response = await client.post(
        f"/api/v1/ai/{test_session.id}/questionnaire",
        json={
            "topic": "User Login",
            "context": "A simple web application",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "questions" in data
    assert len(data["questions"]) > 0
    assert data["topic"] == "User Login"

    # Verify question structure
    question = data["questions"][0]
    assert "id" in question
    assert "question" in question
    assert "type" in question


@pytest.mark.asyncio
async def test_suggest_requirements(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test requirement suggestions with real Claude API."""
    # First, add some conversation context
    await client.post(
        f"/api/v1/ai/{test_session.id}/chat",
        json={
            "message": "I need a task tracking system for my team",
            "include_history": False,
        },
        headers=auth_headers,
    )

    # Now get suggestions
    response = await client.post(
        f"/api/v1/ai/{test_session.id}/suggest-requirements",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) > 0

    # Verify suggestion structure
    suggestion = data["suggestions"][0]
    assert "id" in suggestion
    assert "text" in suggestion
    assert "category" in suggestion
    assert "priority" in suggestion


@pytest.mark.asyncio
async def test_get_messages(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test getting message history."""
    # Create a message first
    await client.post(
        f"/api/v1/ai/{test_session.id}/chat",
        json={
            "message": "Test message for history",
            "include_history": False,
        },
        headers=auth_headers,
    )

    # Get messages
    response = await client.get(
        f"/api/v1/ai/{test_session.id}/messages",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2  # At least user message + assistant response

    # Check message structure
    user_msg = next((m for m in data if m["role"] == "user"), None)
    assert user_msg is not None
    assert "Test message for history" in user_msg["content"]


@pytest.mark.asyncio
async def test_questionnaire_answer_submission(
    client: AsyncClient, auth_headers: dict, test_session: Session
):
    """Test submitting questionnaire answers."""
    # First create a questionnaire
    q_response = await client.post(
        f"/api/v1/ai/{test_session.id}/questionnaire",
        json={
            "topic": "Basic Features",
            "context": "Testing",
        },
        headers=auth_headers,
    )
    assert q_response.status_code == 200
    questionnaire = q_response.json()

    # Submit answers
    response = await client.post(
        f"/api/v1/ai/{test_session.id}/questionnaire/answer",
        json={
            "questionnaire_id": questionnaire["id"],
            "answers": {"q1": "Test answer"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
