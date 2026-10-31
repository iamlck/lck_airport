import time
from typing import List, Dict, Any, AsyncGenerator
from strategies.base import KnowledgeStrategy
from schemas.chat import ChatResponse, Citation, StreamChunk
from knowledge.snapshot import snapshot_manager
from llm.client import LLMClient
from core.logging import logger

# Everything in this template is byte-identical on every request, in every language.
# It is sent as its own system message so it forms a stable prompt prefix that the model
# can serve from cache (Ollama KV reuse, and automatic prompt caching on hosted APIs).
# Anything that varies per request belongs below it, never inside it.
OKF_KNOWLEDGE_TEMPLATE = """You are the official AI Talking Avatar Assistant for Chaudhary Charan Singh International Airport (LCK) in Lucknow, India.

Your knowledge is STRICTLY constrained to the official documents provided below.
Rules:
1. Ground every claim directly in the approved context.
2. If the user question cannot be answered from the provided documents, or the context is missing the requested fact, state clearly: "I cannot find this information in the official airport records. Please visit the nearest airport inquiry desk."
3. Do not make up flight schedules, gates, fees, or contact details.
4. Keep the answer spoken, natural, concise, and helpful for a talking avatar.

--- OFFICIAL KNOWLEDGE BASE ---
{context}
--- END OF OFFICIAL KNOWLEDGE BASE ---
"""

# The only per-request instruction, kept after the knowledge base so it cannot disturb the prefix.
OKF_LANGUAGE_TEMPLATE = "Language: Respond in {language_instruction}."


class OKFStrategy(KnowledgeStrategy):
    def __init__(self):
        self.llm = LLMClient()

    def _get_language_instruction(self, lang: str) -> str:
        if lang == "hi":
            return "Hindi (हिन्दी)"
        elif lang == "es":
            return "Spanish (Español)"
        return "English"

    def _build_messages(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str
    ) -> List[Dict[str, str]]:
        """
        Builds the prompt for both the buffered and streaming paths.

        Both paths must produce byte-identical leading messages or they will not share
        a cache entry, so neither builds its own prompt.
        """
        snapshot = snapshot_manager.active_snapshot
        if not snapshot:
            snapshot = snapshot_manager.refresh()

        messages = [
            {"role": "system", "content": OKF_KNOWLEDGE_TEMPLATE.format(context=snapshot.get_full_context())},
            {"role": "system", "content": OKF_LANGUAGE_TEMPLATE.format(
                language_instruction=self._get_language_instruction(language)
            )},
        ]
        messages.extend(history)
        messages.append({"role": "user", "content": query})
        return messages

    def _build_citations(self) -> List[Citation]:
        return [
            Citation(
                document_id="okf_full_knowledge",
                document_title="LCK Airport Approved Knowledge Base",
                source_file="manifest.json",
                snippet="Full approved knowledge context",
                confidence=1.0
            )
        ]

    async def answer(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str = "en",
        stream: bool = False
    ) -> ChatResponse:
        start_time = time.time()

        messages = self._build_messages(query, history, language)
        raw_answer = await self.llm.acomplete(messages)
        latency = (time.time() - start_time) * 1000

        abstained = "cannot find this information" in raw_answer.lower() or "not in the official" in raw_answer.lower()

        return ChatResponse(
            answer=raw_answer,
            strategy_used="okf",
            session_id="",  # Injected by service
            citations=self._build_citations(),
            latency_ms=round(latency, 2),
            abstained=abstained
        )

    async def astream_answer(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str = "en"
    ) -> AsyncGenerator[StreamChunk, None]:
        messages = self._build_messages(query, history, language)

        async for token in self.llm.astream(messages):
            yield StreamChunk(chunk=token, is_final=False)

        yield StreamChunk(chunk="", is_final=True, citations=self._build_citations())
