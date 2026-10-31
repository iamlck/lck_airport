from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncGenerator
from schemas.chat import ChatResponse, Citation, StreamChunk


class KnowledgeStrategy(ABC):
    @abstractmethod
    async def answer(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str = "en",
        stream: bool = False
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def astream_answer(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str = "en"
    ) -> AsyncGenerator[StreamChunk, None]:
        pass

