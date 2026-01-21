from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.models.message import Message


class AIProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        message: str,
        history: list[Message],
        system_prompt: str | None = None,
    ) -> tuple[str, int, int]:
        """
        Send a chat message and get a response.
        Returns: (response_content, input_tokens, output_tokens)
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        message: str,
        history: list[Message],
        system_prompt: str | None = None,
    ) -> AsyncIterator[dict]:
        """
        Stream a chat response.
        Yields dicts with type 'content' or 'usage'.
        """
        pass

    @abstractmethod
    async def generate_questionnaire(
        self,
        topic: str,
        context: str | None = None,
    ) -> tuple[list, int, int]:
        """
        Generate a questionnaire for gathering requirements.
        Returns: (questions, input_tokens, output_tokens)
        """
        pass

    @abstractmethod
    async def suggest_requirements(
        self,
        history: list[Message],
        document_content: dict | None = None,
    ) -> tuple[list, str]:
        """
        Suggest requirements based on conversation history.
        Returns: (suggestions, context_used)
        """
        pass
