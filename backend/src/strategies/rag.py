import time
from typing import List, Dict, Any, AsyncGenerator
from strategies.base import KnowledgeStrategy
from schemas.chat import ChatResponse, Citation, StreamChunk
from knowledge.snapshot import snapshot_manager
from retrieval.lexical import LexicalIndex
from retrieval.hybrid import HybridRetriever
from llm.client import LLMClient
from core.config import settings
from core.logging import logger

RAG_SYSTEM_TEMPLATE = """You are the official AI Talking Avatar Assistant for Chaudhary Charan Singh International Airport (LCK) in Lucknow, India.

Answer the passenger's question using ONLY the retrieved evidence chunks below.
Rules:
1. Every answer must be directly supported by the evidence.
2. If the evidence does not clearly contain the answer, state: "I cannot find this information in the official airport records. Please visit the nearest airport inquiry desk."
3. If an evidence chunk is a table, read rows and columns accurately.
4. Keep the answer spoken, natural, concise, and friendly.
5. Language: Respond in {language_instruction}.

--- RETRIEVED EVIDENCE ---
{evidence}
"""


class RAGStrategy(KnowledgeStrategy):
    def __init__(self):
        self.llm = LLMClient()
        self._cached_version = None
        self._retriever = None

    def _ensure_retriever(self):
        snapshot = snapshot_manager.active_snapshot
        if not snapshot:
            snapshot = snapshot_manager.refresh()

        if self._cached_version != snapshot.version or not self._retriever:
            lexical = LexicalIndex(snapshot.chunks)
            self._retriever = HybridRetriever(lexical_index=lexical)
            self._cached_version = snapshot.version
            logger.info(f"RAG hybrid retriever built with {len(snapshot.chunks)} chunks.")

        return self._retriever

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
        retriever = self._ensure_retriever()

        evidence_chunks = retriever.retrieve(query, top_k=settings.rag_top_k)

        # Assemble evidence text
        evidence_text = ""
        citations = []
        for idx, chunk in enumerate(evidence_chunks):
            evidence_text += f"\n[Evidence {idx+1} | Source: {chunk['doc_title']} - {chunk['header']}]\n{chunk['text']}\n"
            citations.append(
                Citation(
                    document_id=chunk["doc_id"],
                    document_title=chunk["doc_title"],
                    source_file=chunk["doc_id"],
                    snippet=chunk["text"][:150] + "...",
                    confidence=round(chunk.get("rrf_score", 0.0), 4)
                )
            )

        lang_instr = self._get_language_instruction(language)
        system_prompt = RAG_SYSTEM_TEMPLATE.format(
            evidence=evidence_text if evidence_text else "No relevant evidence found.",
            language_instruction=lang_instr
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        raw_answer = await self.llm.acomplete(messages)
        latency = (time.time() - start_time) * 1000

        abstained = "cannot find this information" in raw_answer.lower() or "not in the official" in raw_answer.lower()

        return ChatResponse(
            answer=raw_answer,
            strategy_used="rag",
            session_id="",
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
        retriever = self._ensure_retriever()
        evidence_chunks = retriever.retrieve(query, top_k=settings.rag_top_k)

        evidence_text = ""
        citations = []
        for idx, chunk in enumerate(evidence_chunks):
            evidence_text += f"\n[Evidence {idx+1} | Source: {chunk['doc_title']} - {chunk['header']}]\n{chunk['text']}\n"
            citations.append(
                Citation(
                    document_id=chunk["doc_id"],
                    document_title=chunk["doc_title"],
                    source_file=chunk["doc_id"],
                    snippet=chunk["text"][:150] + "...",
                    confidence=round(chunk.get("rrf_score", 0.0), 4)
                )
            )

        lang_instr = self._get_language_instruction(language)
        system_prompt = RAG_SYSTEM_TEMPLATE.format(
            evidence=evidence_text if evidence_text else "No relevant evidence found.",
            language_instruction=lang_instr
        )

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        async for token in self.llm.astream(messages):
            yield StreamChunk(chunk=token, is_final=False)

        yield StreamChunk(chunk="", is_final=True, citations=citations)

