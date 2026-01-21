import json
from typing import AsyncIterator

from anthropic import AsyncAnthropic

from app.core.config import get_settings
from app.models.message import Message, MessageRole
from app.schemas.ai import QuestionnaireQuestion, RequirementSuggestion
from app.services.ai_provider import AIProvider

settings = get_settings()

REQUIREMENTS_SYSTEM_PROMPT = """You are an expert requirements analyst helping to gather and document software requirements.
Your role is to:
1. Ask clarifying questions to understand the user's needs
2. Help structure and organize requirements
3. Identify potential gaps or inconsistencies
4. Suggest best practices for requirements documentation

Always be helpful, professional, and thorough in your analysis."""


class ClaudeService(AIProvider):
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.claude_model

    def _format_history(self, history: list[Message]) -> list[dict]:
        messages = []
        for msg in history:
            if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })
        return messages

    async def chat(
        self,
        message: str,
        history: list[Message],
        system_prompt: str | None = None,
    ) -> tuple[str, int, int]:
        messages = self._format_history(history)
        messages.append({"role": "user", "content": message})

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system_prompt or REQUIREMENTS_SYSTEM_PROMPT,
            messages=messages,
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        return content, input_tokens, output_tokens

    async def chat_stream(
        self,
        message: str,
        history: list[Message],
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict]:
        messages = self._format_history(history)
        messages.append({"role": "user", "content": message})

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=4096,
            system=system_prompt or REQUIREMENTS_SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield {"type": "content", "content": text}

            message = await stream.get_final_message()
            yield {
                "type": "usage",
                "input_tokens": message.usage.input_tokens,
                "output_tokens": message.usage.output_tokens,
            }

    async def generate_questionnaire(
        self,
        topic: str,
        context: str | None = None,
    ) -> tuple[list[QuestionnaireQuestion], int, int]:
        prompt = f"""Generate a questionnaire to gather requirements about: {topic}

{f'Additional context: {context}' if context else ''}

Return a JSON array of questions with the following structure:
[
  {{
    "id": "q1",
    "question": "The question text",
    "type": "text|select|multiselect|boolean",
    "options": ["option1", "option2"] // only for select/multiselect
    "required": true
  }}
]

Generate 5-10 relevant questions that will help understand the requirements thoroughly.
Return ONLY the JSON array, no other text."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="You are a requirements analyst. Generate structured questionnaires in JSON format.",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens

        # Parse JSON response
        try:
            # Find JSON array in response
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                questions_data = json.loads(json_str)
                questions = [QuestionnaireQuestion(**q) for q in questions_data]
            else:
                questions = []
        except (json.JSONDecodeError, ValueError):
            questions = []

        return questions, input_tokens, output_tokens

    async def suggest_requirements(
        self,
        history: list[Message],
        document_content: dict | None = None,
    ) -> tuple[list[RequirementSuggestion], str]:
        # Build context from conversation history
        conversation_context = "\n".join([
            f"{msg.role.value}: {msg.content[:500]}"
            for msg in history[-20:]
        ])

        doc_context = ""
        if document_content:
            doc_context = f"\nCurrent document content: {json.dumps(document_content)[:2000]}"

        prompt = f"""Based on the following conversation and document content, suggest specific requirements that should be documented.

Conversation:
{conversation_context}
{doc_context}

Return a JSON array of requirement suggestions:
[
  {{
    "id": "req1",
    "text": "The requirement statement",
    "category": "functional|non-functional|constraint|assumption",
    "priority": "high|medium|low",
    "rationale": "Why this requirement is suggested"
  }}
]

Generate 3-8 specific, actionable requirements. Return ONLY the JSON array."""

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system="You are a requirements analyst. Generate specific requirement suggestions in JSON format.",
            messages=[{"role": "user", "content": prompt}],
        )

        content = response.content[0].text

        # Parse JSON response
        try:
            start = content.find("[")
            end = content.rfind("]") + 1
            if start != -1 and end > start:
                json_str = content[start:end]
                suggestions_data = json.loads(json_str)
                suggestions = [RequirementSuggestion(**s) for s in suggestions_data]
            else:
                suggestions = []
        except (json.JSONDecodeError, ValueError):
            suggestions = []

        context_used = f"Analyzed {len(history)} messages"
        if document_content:
            context_used += " and document content"

        return suggestions, context_used
