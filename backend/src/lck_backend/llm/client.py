import os
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
import litellm
from lck_backend.core.config import settings
from lck_backend.core.logging import logger

if settings.ollama_api_base:
    os.environ["OLLAMA_API_BASE"] = settings.ollama_api_base
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key.get_secret_value()
if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key.get_secret_value()
if settings.gemini_api_key:
    os.environ["GEMINI_API_KEY"] = settings.gemini_api_key.get_secret_value()

litellm.drop_params = True


class LLMClient:
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.llm_model

    def _provider_options(self) -> Dict[str, Any]:
        """
        Ollama truncates the prompt to num_ctx (2048 by default) without warning, which would
        silently drop most of the knowledge snapshot. Hosted providers size their own context.
        """
        if self.model.startswith("ollama"):
            return {"num_ctx": settings.llm_num_ctx}
        return {}

    async def acomplete(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> str:
        temp = temperature if temperature is not None else settings.llm_temperature
        tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
        tout = timeout if timeout is not None else settings.llm_timeout_seconds

        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                timeout=tout,
                **self._provider_options(),
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LiteLLM completion error for model {self.model}: {e}")
            raise

    async def astream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        temp = temperature if temperature is not None else settings.llm_temperature
        tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
        tout = timeout if timeout is not None else settings.llm_timeout_seconds

        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                timeout=tout,
                stream=True,
                **self._provider_options(),
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"LiteLLM stream error for model {self.model}: {e}")
            raise


llm_client = LLMClient()

