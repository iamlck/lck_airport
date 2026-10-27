import json
from typing import AsyncGenerator
from lck_backend.schemas.chat import ChatRequest, ChatResponse, StreamChunk
from lck_backend.guardrail.classifier import guardrail
from lck_backend.memory.store import memory_store
from lck_backend.strategies.factory import strategy_factory
from lck_backend.core.errors import GuardrailRejectedError
from lck_backend.core.logging import logger


class ChatService:
    async def process_chat(self, req: ChatRequest) -> ChatResponse:
        # Step 1: Guardrail Inspection
        check = await guardrail.classify(req.query)
        if check["status"] != "PASS":
            logger.warning(f"Query rejected by guardrail: {check['status']} - {check['reason']}")
            if check["status"] == "OFF_TOPIC":
                msg = "I am specifically designed to assist passengers with Chaudhary Charan Singh International Airport (LCK) inquiries. How may I help you with your airport travel today?"
            elif check["status"] == "INJECTION":
                msg = "Security policy violation: prompt manipulation attempt detected."
            else:
                msg = "Your query cannot be processed as it violates airport safety guidelines."

            # Return polite abstention/redirection directly without hitting heavy LLM
            sid = await memory_store.get_or_create_session(req.session_id, req.user_id)
            await memory_store.add_message(sid, "user", req.query)
            await memory_store.add_message(sid, "assistant", msg, strategy="guardrail")

            return ChatResponse(
                answer=msg,
                strategy_used="guardrail",
                session_id=sid,
                citations=[],
                latency_ms=10.0,
                abstained=True
            )

        # Step 2: Session & Memory
        sid = await memory_store.get_or_create_session(req.session_id, req.user_id)
        history = await memory_store.get_history(sid)

        # Step 3: Select Strategy
        strategy = strategy_factory.get_strategy(req.strategy)

        # Step 4: Execute Strategy
        resp = await strategy.answer(
            query=req.query,
            history=history,
            language=req.language or "en",
            stream=req.stream
        )
        resp.session_id = sid

        # Step 5: Save turn to memory
        await memory_store.add_message(sid, "user", req.query)
        await memory_store.add_message(sid, "assistant", resp.answer, strategy=req.strategy)

        return resp

    async def stream_chat(self, req: ChatRequest) -> AsyncGenerator[str, None]:
        # Guardrail check
        check = await guardrail.classify(req.query)
        sid = await memory_store.get_or_create_session(req.session_id, req.user_id)

        if check["status"] != "PASS":
            msg = "I am specifically designed to assist passengers with Chaudhary Charan Singh International Airport (LCK) inquiries."
            yield f"data: {json.dumps({'chunk': msg, 'is_final': True, 'abstained': True, 'session_id': sid})}\n\n"
            return

        history = await memory_store.get_history(sid)
        strategy = strategy_factory.get_strategy(req.strategy)

        full_answer = []
        async for chunk in strategy.astream_answer(req.query, history, req.language or "en"):
            if chunk.chunk:
                full_answer.append(chunk.chunk)
            payload = {
                "chunk": chunk.chunk,
                "is_final": chunk.is_final,
                "citations": [c.dict() for c in (chunk.citations or [])],
                "session_id": sid
            }
            yield f"data: {json.dumps(payload)}\n\n"

        # Record to memory
        complete_text = "".join(full_answer)
        await memory_store.add_message(sid, "user", req.query)
        await memory_store.add_message(sid, "assistant", complete_text, strategy=req.strategy)


chat_service = ChatService()

