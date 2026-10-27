import time
from typing import List, Dict, Any, AsyncGenerator
from lck_backend.strategies.base import KnowledgeStrategy
from lck_backend.schemas.chat import ChatResponse, Citation, StreamChunk
from lck_backend.knowledge.snapshot import snapshot_manager
from lck_backend.llm.client import LLMClient
from lck_backend.core.logging import logger

OKF_SYSTEM_TEMPLATE = """You are the official AI Talking Avatar Assistant for Chaudhary Charan Singh International Airport (LCK) in Lucknow, India.

Your knowledge is STRICTLY constrained to the official documents provided below.
Rules:
1. Ground every claim directly in the approved context.
2. If the user question cannot be answered from the provided documents, or the context is missing the requested fact, state clearly: "I cannot find this information in the official airport records. Please visit the nearest airport inquiry desk."
3. Do not make up flight schedules, gates, fees, or contact details.
4. Keep the answer spoken, natural, concise, and helpful for a talking avatar.
5. Language: Respond in {language_instruction}.

--- OFFICIAL KNOWLEDGE BASE ---
{context}
"""


class OKFStrategy(KnowledgeStrategy):
    def __init__(self):
        self.llm = LLMClient()

    def _get_language_instruction(self, lang: str) -> str:
        if lang == "hi":
            return "Hindi (हिन्दी)"
        elif lang == "es":
            return "Spanish (Español)"
        return "English"

    async def answer(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str = "en",
        stream: bool = False
    ) -> ChatResponse:
        start_time = time.time()
        snapshot = snapshot_manager.active_snapshot
        if not snapshot:
            snapshot = snapshot_manager.refresh()

        context = snapshot.get_full_context()
        lang_instr = self._get_language_instruction(language)

        system_prompt = OKF_SYSTEM_TEMPLATE.format(
            context=context,
            language_instruction=lang_instr
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        raw_answer = await self.llm.acomplete(messages)
        latency = (time.time() - start_time) * 1000

        # Citations
        citations = [
            Citation(
                document_id="okf_full_knowledge",
                document_title="LCK Airport Approved Knowledge Base",
                source_file="manifest.json",
                snippet="Full approved knowledge context",
                confidence=1.0
            )
        ]

        abstained = "cannot find this information" in raw_answer.lower() or "not in the official" in raw_answer.lower()

        return ChatResponse(
            answer=raw_answer,
            strategy_used="okf",
            session_id="",  # Injected by service
            citations=citations,
            latency_ms=round(latency, 2),
            abstained=abstained
        )

    async def astream_answer(
        self,
        query: str,
        history: List[Dict[str, str]],
        language: str = "en"
    ) -> AsyncGenerator[StreamChunk, None]:
        snapshot = snapshot_manager.active_snapshot
        if not snapshot:
            snapshot = snapshot_manager.refresh()

        context = snapshot.get_full_context()
        lang_instr = self._get_language_instruction(language)
        system_prompt = OKF_SYSTEM_TEMPLATE.format(
            context=context,
            language_instruction=lang_instr
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        async for token in self.llm.astream(messages):
            yield StreamChunk(chunk=token, is_final=False)

        citations = [
            Citation(
                document_id="okf_full_knowledge",
                document_title="LCK Airport Approved Knowledge Base",
                source_file="manifest.json",
                snippet="Full approved knowledge context",
                confidence=1.0
            )
        ]
        yield StreamChunk(chunk="", is_final=True, citations=citations)

