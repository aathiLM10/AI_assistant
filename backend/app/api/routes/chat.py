from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.providers.base import (
    LLMAuthenticationError,
    LLMEmptyResponseError,
    LLMProviderError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
)
from app.providers.gemini import GeminiProvider
from app.schemas.chat import ChatRequest, ChatResponse, ErrorDetail
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService

router = APIRouter(tags=["Chat"])


def get_chat_service(settings: Settings = Depends(get_settings)) -> ChatService:
    """
    FastAPI dependency factory assembling the layered architecture:
    Config -> GeminiProvider -> LLMService -> PromptService -> ChatService.
    Using dependency injection ensures easy test mocking without modifying routes.
    """
    provider = GeminiProvider(settings=settings)
    llm_service = LLMService(provider=provider)
    prompt_service = PromptService()
    return ChatService(prompt_service=prompt_service, llm_service=llm_service)


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit user question and receive AI response",
    description=(
        "Accepts a user question, processes it through the structured prompt pipeline, "
        "queries Gemini LLM via the provider layer, and returns the validated answer."
    ),
    responses={
        status.HTTP_200_OK: {
            "model": ChatResponse,
            "description": "Successful generation from foundational model"
        },
        422: {
            "model": ErrorDetail,
            "description": "Request body validation failure (e.g. empty or too long message)"
        },
        status.HTTP_502_BAD_GATEWAY: {
            "model": ErrorDetail,
            "description": "Upstream Gemini API or empty candidate generation failure"
        },
        status.HTTP_504_GATEWAY_TIMEOUT: {
            "model": ErrorDetail,
            "description": "Upstream LLM request exceeded timeout limit"
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorDetail,
            "description": "Internal server configuration or unhandled error"
        }
    }
)
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """
    Thin HTTP route controller: receives verified payload, delegates to ChatService,
    and maps domain exceptions into standardized HTTP error responses.
    """
    try:
        return await chat_service.answer_question(request)

    except LLMTimeoutError as exc:
        logger.error("Chat request timed out", extra={"extra_fields": {"error": str(exc)}})
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc)
        ) from exc

    except LLMAuthenticationError as exc:
        logger.error("Chat request failed due to provider credential error", extra={"extra_fields": {"error": str(exc)}})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc)
        ) from exc

    except (LLMEmptyResponseError, LLMServiceUnavailableError) as exc:
        logger.error("Provider returned an empty response or service unavailable", extra={"extra_fields": {"error": str(exc)}})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        ) from exc

    except LLMProviderError as exc:
        logger.error("LLM Provider encountered an error", extra={"extra_fields": {"error": str(exc)}})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        logger.exception("Unhandled error processing chat request")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal server error occurred while processing the chat request."
        ) from exc
