from abc import ABC, abstractmethod
from typing import Optional, Tuple


"""
The Provider abstraction isolates vendor-specific SDK semantics (Google GenAI, OpenAI, Anthropic)
behind a unified interface. This satisfies the Dependency Inversion Principle, allowing the application
to substitute underlying LLMs without altering core business or chat services.
"""

class LLMProviderError(Exception):
    """Base domain exception for failures originating in LLM provider execution."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class LLMTimeoutError(LLMProviderError):
    """Raised when an LLM provider request exceeds the configured network timeout threshold."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when provider authentication fails due to missing or invalid credentials."""
    pass


class LLMEmptyResponseError(LLMProviderError):
    """Raised when the LLM provider completes without generating any candidate text (e.g. safety blocks)."""
    pass


class LLMServiceUnavailableError(LLMProviderError):
    """Raised when the provider is rate-limited, quota-exhausted, or encountering upstream downtime."""
    pass


class BaseLLMProvider(ABC):
    """
    Abstract interface defining the contract that all LLM providers must fulfill.
    """
    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generate a text response given a prompt and optional system instructions.
        Returns a tuple of (generated_answer, model_name).
        """
        pass
