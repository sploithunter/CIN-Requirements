from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.message import MessageRole, MessageType


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    message_type: MessageType = MessageType.TEXT
    extra_data: dict | None = None


class ChatRequest(BaseModel):
    message: str
    include_history: bool = True
    max_history_messages: int = 20


class ChatResponse(BaseModel):
    id: UUID
    role: MessageRole
    content: str
    message_type: MessageType
    extra_data: dict | None
    input_tokens: int
    output_tokens: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionnaireQuestion(BaseModel):
    id: str
    question: str
    type: str  # text, select, multiselect, boolean
    options: list[str] | None = None
    required: bool = True


class QuestionnaireRequest(BaseModel):
    topic: str
    context: str | None = None


class QuestionnaireResponse(BaseModel):
    id: UUID
    questions: list[QuestionnaireQuestion]
    topic: str
    created_at: datetime


class QuestionnaireAnswers(BaseModel):
    questionnaire_id: UUID
    answers: dict[str, str | list[str] | bool]


class RequirementSuggestion(BaseModel):
    id: str
    text: str
    category: str
    priority: str | None = None
    rationale: str | None = None


class RequirementSuggestionsResponse(BaseModel):
    suggestions: list[RequirementSuggestion]
    context_used: str
