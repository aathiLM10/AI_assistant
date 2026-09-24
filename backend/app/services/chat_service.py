from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


"""
ChatService encapsulates the domain business logic for user chat interactions.
It coordinates the prompt assembly phase and the generic LLM execution phase,
then validates and packages the output into a strict ChatResponse schema.
"""

class ChatService:
    def __init__(self, prompt_service: PromptService, llm_service: LLMService):
        self.prompt_service = prompt_service
        self.llm_service = llm_service

    async def answer_question(self, request: ChatRequest) -> ChatResponse:
        """
        Orchestration pipeline:
        1. PromptService builds structured prompt and attaches system instructions.
        2. LLMService dispatches the prompt to the configured foundational provider.
        3. Response is verified and mapped into the typed Pydantic ChatResponse domain model.
        """
        # Step 1: Prompt Construction
        formatted_prompt, system_instruction = self.prompt_service.build_prompt(
            user_query=request.message
        )

        # Step 2: LLM Invocation
        raw_answer, model_name = await self.llm_service.generate(
            prompt=formatted_prompt,
            system_instruction=system_instruction
        )

        # Step 3: Response Validation & Normalization
        return ChatResponse(
            answer=raw_answer,
            model=model_name
        )
