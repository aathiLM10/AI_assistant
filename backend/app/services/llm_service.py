import time
from typing import Optional, Tuple
from app.core.logging import logger
from app.providers.base import BaseLLMProvider


"""
LLMService acts as the generic model dispatch and telemetry layer.
It depends only on the BaseLLMProvider interface, allowing swapping between Gemini, OpenAI,
or local open-source models without requiring any code changes in upstream business services.
"""

class LLMService:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Executes text generation via the injected provider, capturing performance telemetry
        and logging metrics without exposing user content.
        """
        start_time = time.perf_counter()

        logger.info(
            "Dispatching generation request to LLM provider",
            extra={"extra_fields": {"provider": self.provider.__class__.__name__}}
        )

        answer, model_name = await self.provider.generate_text(
            prompt=prompt,
            system_instruction=system_instruction
        )

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.info(
            "LLM generation completed successfully",
            extra={"extra_fields": {"model": model_name, "latency_ms": duration_ms}}
        )

        return answer, model_name
