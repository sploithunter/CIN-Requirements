from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_session_with_access
from app.models.message import Message, MessageRole, MessageType
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    QuestionnaireRequest,
    QuestionnaireResponse,
    QuestionnaireAnswers,
    RequirementSuggestionsResponse,
)
from app.services.claude_service import ClaudeService

router = APIRouter()


@router.post("/{session_id}/chat", response_model=ChatResponse)
async def chat(
    session_id: UUID,
    chat_request: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    claude_service = ClaudeService()

    # Get message history if requested
    history = []
    if chat_request.include_history:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(chat_request.max_history_messages)
        )
        history = list(reversed(result.scalars().all()))

    # Save user message
    user_message = Message(
        session_id=session_id,
        role=MessageRole.USER,
        message_type=MessageType.TEXT,
        content=chat_request.message,
    )
    db.add(user_message)
    await db.flush()

    # Get AI response
    response_content, input_tokens, output_tokens = await claude_service.chat(
        message=chat_request.message,
        history=history,
        system_prompt=session.system_prompt,
    )

    # Save assistant message
    assistant_message = Message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        message_type=MessageType.TEXT,
        content=response_content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    db.add(assistant_message)

    # Update session token usage
    session.token_usage += input_tokens + output_tokens

    await db.commit()
    await db.refresh(assistant_message)

    return assistant_message


@router.post("/{session_id}/chat/stream")
async def chat_stream(
    session_id: UUID,
    chat_request: ChatRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    claude_service = ClaudeService()

    # Get message history if requested
    history = []
    if chat_request.include_history:
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.desc())
            .limit(chat_request.max_history_messages)
        )
        history = list(reversed(result.scalars().all()))

    # Save user message
    user_message = Message(
        session_id=session_id,
        role=MessageRole.USER,
        message_type=MessageType.TEXT,
        content=chat_request.message,
    )
    db.add(user_message)
    await db.commit()

    async def generate():
        full_response = ""
        input_tokens = 0
        output_tokens = 0

        async for chunk in claude_service.chat_stream(
            message=chat_request.message,
            history=history,
            system_prompt=session.system_prompt,
        ):
            if chunk.get("type") == "content":
                full_response += chunk["content"]
                yield f"data: {chunk['content']}\n\n"
            elif chunk.get("type") == "usage":
                input_tokens = chunk.get("input_tokens", 0)
                output_tokens = chunk.get("output_tokens", 0)

        # Save assistant message after streaming completes
        assistant_message = Message(
            session_id=session_id,
            role=MessageRole.ASSISTANT,
            message_type=MessageType.TEXT,
            content=full_response,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
        db.add(assistant_message)
        session.token_usage += input_tokens + output_tokens
        await db.commit()

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/{session_id}/questionnaire", response_model=QuestionnaireResponse)
async def generate_questionnaire(
    session_id: UUID,
    request: QuestionnaireRequest,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    claude_service = ClaudeService()

    questions, input_tokens, output_tokens = await claude_service.generate_questionnaire(
        topic=request.topic,
        context=request.context,
    )

    # Save questionnaire as a message
    questionnaire_message = Message(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        message_type=MessageType.QUESTIONNAIRE,
        content=f"Questionnaire: {request.topic}",
        extra_data={"questions": [q.model_dump() for q in questions], "topic": request.topic},
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    db.add(questionnaire_message)
    session.token_usage += input_tokens + output_tokens
    await db.commit()
    await db.refresh(questionnaire_message)

    return QuestionnaireResponse(
        id=questionnaire_message.id,
        questions=questions,
        topic=request.topic,
        created_at=questionnaire_message.created_at,
    )


@router.post("/{session_id}/questionnaire/answer")
async def submit_questionnaire_answers(
    session_id: UUID,
    answers: QuestionnaireAnswers,
    current_user: CurrentUser,
    db: DbSession,
):
    await get_session_with_access(session_id, current_user, db)

    # Get the questionnaire message
    result = await db.execute(
        select(Message).where(Message.id == answers.questionnaire_id)
    )
    questionnaire = result.scalar_one_or_none()

    if questionnaire is None or questionnaire.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Questionnaire not found",
        )

    # Save user's answers
    answer_message = Message(
        session_id=session_id,
        role=MessageRole.USER,
        message_type=MessageType.QUESTIONNAIRE,
        content="Questionnaire answers submitted",
        extra_data={"questionnaire_id": str(answers.questionnaire_id), "answers": answers.answers},
    )
    db.add(answer_message)
    await db.commit()

    return {"status": "success", "message_id": str(answer_message.id)}


@router.post("/{session_id}/suggest-requirements", response_model=RequirementSuggestionsResponse)
async def suggest_requirements(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
):
    session = await get_session_with_access(session_id, current_user, db)
    claude_service = ClaudeService()

    # Get conversation history for context
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(50)
    )
    history = list(reversed(result.scalars().all()))

    suggestions, context_used = await claude_service.suggest_requirements(
        history=history,
        document_content=session.document_content,
    )

    return RequirementSuggestionsResponse(
        suggestions=suggestions,
        context_used=context_used,
    )


@router.get("/{session_id}/messages", response_model=list[ChatResponse])
async def get_messages(
    session_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
):
    await get_session_with_access(session_id, current_user, db)

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()
