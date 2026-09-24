import asyncio
from typing import Optional, Tuple
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.core.config import Settings
from app.core.logging import logger
from app.providers.base import (
    BaseLLMProvider,
    LLMAuthenticationError,
    LLMEmptyResponseError,
    LLMProviderError,
    LLMServiceUnavailableError,
    LLMTimeoutError,
)


class GeminiProvider(BaseLLMProvider):
    """
    Direct vendor integration for Google's Gemini foundational models using the official Gemini SDK.
    Encapsulates all Google-specific SDK calls, client configuration, and exception translation.
    """
    def __init__(self, settings: Settings):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.timeout_seconds = settings.REQUEST_TIMEOUT_SECONDS

        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            logger.warning(
                "Gemini API key is not configured. Calls to the provider will require a valid GEMINI_API_KEY."
            )
        else:
            genai.configure(api_key=self.api_key)

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Executes an asynchronous generation call against the Gemini API.
        Enforces timeout limits and translates vendor SDK exceptions into domain exceptions.
        """
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            raise LLMAuthenticationError(
                "Gemini API key is missing or unconfigured. Please set GEMINI_API_KEY in the backend .env file."
            )

        try:
            # Concept: GenerativeModel instance holds model hyperparameters and persistent system instructions
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_instruction
            )

            # Enforce async timeout boundary to prevent hanging sockets
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=self.timeout_seconds
            )

            # Verify response validity and extract text
            if not response or not response.candidates:
                raise LLMEmptyResponseError("The Gemini model returned an empty response with no candidate completions.")

            first_candidate = response.candidates[0]
            # Handle potential safety or policy blockages
            finish_reason = getattr(first_candidate, "finish_reason", None)
            
            try:
                answer = response.text
            except (ValueError, AttributeError) as val_err:
                finish_reason_name = str(finish_reason)
                raise LLMEmptyResponseError(
                    f"Model candidate could not be extracted (finish_reason: {finish_reason_name})."
                ) from val_err

            if not answer or not answer.strip():
                raise LLMEmptyResponseError("The Gemini model generated an empty text output.")

            return answer.strip(), self.model_name

        except asyncio.TimeoutError as exc:
            logger.error("Gemini API call timed out after configured duration", extra={"extra_fields": {"timeout": self.timeout_seconds}})
            raise LLMTimeoutError(f"Gemini API timed out after {self.timeout_seconds} seconds.") from exc

        except (google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as exc:
            logger.error("Gemini API authentication failed")
            raise LLMAuthenticationError("Gemini API authentication failed. Verify that GEMINI_API_KEY is valid.") from exc

        except google_exceptions.ResourceExhausted as exc:
            logger.error("Gemini API quota or rate limit exceeded")
            raise LLMServiceUnavailableError("Gemini API quota or rate limit exceeded. Please retry shortly.") from exc

        except google_exceptions.GoogleAPIError as exc:
            logger.error("Upstream Gemini API error encountered", extra={"extra_fields": {"error_type": type(exc).__name__}})
            raise LLMProviderError(f"Gemini API error: {str(exc)}", original_error=exc) from exc

        except (LLMTimeoutError, LLMAuthenticationError, LLMEmptyResponseError, LLMServiceUnavailableError):
            # Re-raise known domain exceptions
            raise

        except Exception as exc:
            logger.exception("Unexpected exception occurred during Gemini provider execution")
            raise LLMProviderError(f"Unexpected provider error: {str(exc)}", original_error=exc) from exc
