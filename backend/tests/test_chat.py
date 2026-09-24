from typing import Optional, Tuple
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.routes.chat import get_chat_service
from app.providers.base import (
    BaseLLMProvider,
    LLMEmptyResponseError,
    LLMTimeoutError,
)
from app.schemas.chat import ChatResponse
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from app.services.prompt_service import PromptService


class MockLLMProvider(BaseLLMProvider):
    """
    Test mock provider mimicking LLM generation without invoking external APIs.
    """
    def __init__(self, mock_response: str = "Mocked explanation of neural networks.", should_timeout: bool = False, should_empty: bool = False):
        self.mock_response = mock_response
        self.should_timeout = should_timeout
        self.should_empty = should_empty

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Tuple[str, str]:
        if self.should_timeout:
            raise LLMTimeoutError("Test simulated provider timeout.")
        if self.should_empty:
            raise LLMEmptyResponseError("Test simulated empty model candidates.")
        return self.mock_response, "mock-gemini-test"


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    """Verifies that the /health endpoint reports service health."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data


def test_chat_success(client):
    """Verifies successful end-to-end chat flow with mock LLM provider."""
    mock_provider = MockLLMProvider(mock_response="A Transformer uses self-attention mechanisms.")
    mock_service = ChatService(
        prompt_service=PromptService(),
        llm_service=LLMService(provider=mock_provider)
    )

    app.dependency_overrides[get_chat_service] = lambda: mock_service

    try:
        response = client.post("/chat", json={"message": "What is a Transformer?"})
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "A Transformer uses self-attention mechanisms."
        assert data["model"] == "mock-gemini-test"
    finally:
        app.dependency_overrides.clear()


def test_chat_validation_empty_string(client):
    """Verifies that empty messages or whitespace fail validation with 422."""
    response = client.post("/chat", json={"message": "   "})
    assert response.status_code == 422


def test_chat_validation_missing_field(client):
    """Verifies that requests missing 'message' fail validation with 422."""
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_provider_timeout_maps_to_504(client):
    """Verifies that provider timeout exceptions map to HTTP 504 Gateway Timeout."""
    timeout_provider = MockLLMProvider(should_timeout=True)
    mock_service = ChatService(
        prompt_service=PromptService(),
        llm_service=LLMService(provider=timeout_provider)
    )

    app.dependency_overrides[get_chat_service] = lambda: mock_service

    try:
        response = client.post("/chat", json={"message": "Trigger timeout"})
        assert response.status_code == 504
        assert "timeout" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_chat_empty_response_maps_to_502(client):
    """Verifies that empty provider generations map to HTTP 502 Bad Gateway."""
    empty_provider = MockLLMProvider(should_empty=True)
    mock_service = ChatService(
        prompt_service=PromptService(),
        llm_service=LLMService(provider=empty_provider)
    )

    app.dependency_overrides[get_chat_service] = lambda: mock_service

    try:
        response = client.post("/chat", json={"message": "Trigger empty"})
        assert response.status_code == 502
    finally:
        app.dependency_overrides.clear()
