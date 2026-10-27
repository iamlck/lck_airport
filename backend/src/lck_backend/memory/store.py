import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, update
from lck_backend.core.config import settings
from lck_backend.core.logging import logger
from lck_backend.memory.models import Base, SessionModel, MessageModel
from lck_backend.llm.client import LLMClient


class MemoryStore:
    def __init__(self):
        self.db_url = settings.get_database_url()
        self.engine = create_async_engine(self.db_url, echo=False)
        self.session_factory = async_sessionmaker(bind=self.engine, expire_on_commit=False)
        self._initialized = False

    async def initialize(self):
        if not self._initialized:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            self._initialized = True
            logger.info("Memory database initialized.")

    async def get_or_create_session(self, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
        await self.initialize()
        sid = session_id or str(uuid.uuid4())
        async with self.session_factory() as session:
            result = await session.execute(select(SessionModel).where(SessionModel.id == sid))
            existing = result.scalar_one_or_none()
            if not existing:
                new_session = SessionModel(id=sid, user_id=user_id)
                session.add(new_session)
                await session.commit()
            elif user_id and existing.user_id != user_id:
                existing.user_id = user_id
                await session.commit()
        return sid

    async def add_message(self, session_id: str, role: str, content: str, strategy: Optional[str] = None):
        await self.initialize()
        async with self.session_factory() as session:
            msg = MessageModel(session_id=session_id, role=role, content=content, strategy=strategy)
            session.add(msg)
            await session.commit()

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        await self.initialize()
        async with self.session_factory() as session:
            result = await session.execute(
                select(MessageModel)
                .where(MessageModel.session_id == session_id)
                .order_by(MessageModel.created_at.asc())
            )
            messages = result.scalars().all()

            # If within window
            if len(messages) <= settings.memory_max_turns:
                return [{"role": m.role, "content": m.content} for m in messages]

            # Otherwise: sliding window + summary
            recent_messages = messages[-settings.memory_max_turns:]
            older_messages = messages[:-settings.memory_max_turns]

            # Fetch session summary
            s_result = await session.execute(select(SessionModel).where(SessionModel.id == session_id))
            sess = s_result.scalar_one_or_none()
            summary = sess.summary if sess else None

            # Condense older messages if enabled
            if settings.memory_summarize_older and len(older_messages) > 0 and not summary:
                asyncio.create_task(self._summarize_older(session_id, older_messages))

            history = []
            if summary:
                history.append({
                    "role": "system",
                    "content": f"Previous conversation summary: {summary}"
                })
            for m in recent_messages:
                history.append({"role": m.role, "content": m.content})
            return history

    async def _summarize_older(self, session_id: str, older_messages: List[MessageModel]):
        try:
            client = LLMClient()
            convo = "\n".join([f"{m.role}: {m.content}" for m in older_messages])
            summary_prompt = [
                {"role": "system", "content": "Summarize this early conversation history concisely in 2-3 sentences."},
                {"role": "user", "content": convo}
            ]
            summary_text = await client.acomplete(summary_prompt, max_tokens=150)
            async with self.session_factory() as session:
                await session.execute(
                    update(SessionModel)
                    .where(SessionModel.id == session_id)
                    .values(summary=summary_text)
                )
                await session.commit()
        except Exception as e:
            logger.warning(f"Failed to summarize older messages for session {session_id}: {e}")


memory_store = MemoryStore()

