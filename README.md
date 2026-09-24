# AI Assistant 🤖

A learning-focused, end-to-end Generative AI application built to understand and master the complete foundational LLM application architecture.

---

## 🎯 Educational Objective

The primary goal of **AI Assistant** is to demystify how production Generative AI applications function under the hood. 

To ensure clear mental models:
- **No heavy abstraction frameworks:** LangChain, LangGraph, RAG, vector databases, or complex agent loops are intentionally omitted.
- **Direct official Gemini SDK:** All model interactions interface directly with Google's official Gemini SDK (`google-generativeai`).
- **Complete traceability:** A student or engineer can trace every single byte of an inquiry through:
  `User → Next.js UI → FastAPI (/chat) → ChatService → PromptService → LLMService → GeminiProvider → Gemini API → Validation → Next.js UI`.

---

## 🏗️ Architecture Diagram

### Mermaid Flowchart

```mermaid
flowchart TD
    User([👤 User]) -->|Enters Question| NextUI[Next.js Chat UI]
    NextUI -->|POST /chat\n{ message }| FastAPIRoute[FastAPI Route\n/chat]
    
    subgraph Backend [FastAPI Application Core]
        FastAPIRoute -->|Validated ChatRequest| ChatSvc[ChatService\n(Business Orchestration)]
        ChatSvc -->|user_query| PromptSvc[PromptService\n(Templates & System Prompts)]
        PromptSvc -->|Formatted Prompt + System Instruction| ChatSvc
        ChatSvc -->|Prompt + System Instruction| LLMSvc[LLMService\n(Generic Dispatch & Telemetry)]
        LLMSvc -->|generate_text()| ProviderContract[BaseLLMProvider Interface]
        ProviderContract -->|generate_text()| GeminiProv[GeminiProvider\n(Official Gemini SDK)]
    end

    GeminiProv -->|Async SDK Call| GeminiAPI[☁️ Google Gemini API\ngemini-1.5-flash]
    GeminiAPI -->|Raw LLM Response| GeminiProv
    GeminiProv -->|Candidate & Safety Checks| LLMSvc
    LLMSvc -->|Metrics Logged & Text Returned| ChatSvc
    ChatSvc -->|ChatResponse Validation| FastAPIRoute
    FastAPIRoute -->|HTTP 200 JSON\n{ answer, model }| NextUI
    NextUI -->|Renders Markdown & Badge| User
```

### ASCII Flow Diagram

```
User
  ↓
Next.js UI (Browser)
  ↓ [POST /chat with { "message": "..." }]
FastAPI Controller (app/api/routes/chat.py)
  ↓ [Pydantic validated ChatRequest]
ChatService (app/services/chat_service.py)
  ↓ [Prompt construction request]
PromptService (app/services/prompt_service.py)
  ↓ [Formatted prompt + system prompt returned]
LLMService (app/services/llm_service.py)
  ↓ [Dispatches via BaseLLMProvider contract]
GeminiProvider (app/providers/gemini.py)
  ↓ [Async generation request via official Google GenAI SDK]
Google Gemini API (Cloud)
  ↓ [Generated tokens & finish reasons]
Response Verification & Extraction (app/providers/gemini.py)
  ↓ [Latency & telemetry logging]
ChatResponse Validation (app/schemas/chat.py)
  ↓ [HTTP 200 JSON: { "answer": "...", "model": "..." }]
Next.js UI
  ↓
User
```

---

## 🔄 Step-by-Step Request Flow

1. **User Interaction (Next.js UI):**
   The user types a question into the text input. Upon clicking **Send** or pressing `Enter`, the button disables and a loading state activates.
2. **Frontend API Layer (`frontend/src/services/api.ts`):**
   The frontend dispatches an HTTP `POST` request to `http://localhost:8000/chat`. Notice: **no Gemini API key or SDK is in the client bundle**.
3. **Route & Validation Layer (`backend/app/api/routes/chat.py`):**
   FastAPI receives the request and validates the JSON body using `ChatRequest` (Pydantic v2). Empty strings, pure whitespace, or payloads exceeding 4000 characters immediately return `422 Unprocessable Content`.
4. **Business Orchestration (`backend/app/services/chat_service.py`):**
   The thin route hands the valid `ChatRequest` to `ChatService.answer_question()`. `ChatService` coordinates the steps and remains agnostic to which LLM vendor is configured.
5. **Prompt Assembly (`backend/app/services/prompt_service.py`):**
   `PromptService` combines the system prompt (`SYSTEM_PROMPT` in `app/prompts/system.py`) and the template (`USER_QUERY_TEMPLATE` in `app/prompts/templates.py`) to prepare the final payload.
6. **Generic LLM Service (`backend/app/services/llm_service.py`):**
   `LLMService` receives the constructed prompt. It initiates a high-resolution timer to track latency and logs structured execution metadata without exposing private user content.
7. **Vendor Provider (`backend/app/providers/gemini.py`):**
   `GeminiProvider` implements `BaseLLMProvider`. It initializes `genai.GenerativeModel`, attaches system instructions, enforces the request timeout limit, and calls `model.generate_content_async()`.
8. **Upstream Gemini API:**
   Google Gemini processes the prompt and returns model candidates and finish reasons.
9. **Provider Error & Candidate Verification:**
   `GeminiProvider` unpacks the response, checks for safety blocks or empty outputs, and translates any SDK exceptions into domain exceptions (`LLMTimeoutError`, `LLMEmptyResponseError`, `LLMAuthenticationError`).
10. **Schema Validation & Response Formatting:**
    `ChatService` validates the output against `ChatResponse(answer=..., model=...)`.
11. **HTTP Delivery to Client:**
    FastAPI serializes the response to JSON and sends it over HTTP 200.
12. **UI Render:**
    Next.js appends the assistant's message bubble with a model badge, stops the loading indicator, and re-enables the input field.

---

## 📁 Major File Responsibilities

Below is the file responsibility map for the repository:

### Backend (`backend/`)

| File Path | Responsibility |
|:---|:---|
| [`backend/app/main.py`](file:///backend/app/main.py) | **Application Entry Point:** Configures FastAPI app, CORS middleware, lifespan events, health check endpoint (`/health`), and OpenAPI documentation. |
| [`backend/app/api/routes/chat.py`](file:///backend/app/api/routes/chat.py) | **Thin HTTP Controller:** Defines `POST /chat`, handles FastAPI dependency injection, and maps domain exceptions to standard HTTP status codes (`200`, `422`, `502`, `504`, `500`). |
| [`backend/app/schemas/chat.py`](file:///backend/app/schemas/chat.py) | **Contract & Validation Schemas:** Contains Pydantic models (`ChatRequest`, `ChatResponse`, `ErrorDetail`) ensuring boundary data integrity. |
| [`backend/app/services/chat_service.py`](file:///backend/app/services/chat_service.py) | **Domain Business Logic:** Orchestrates prompt building via `PromptService` and dispatching via `LLMService`. Validates domain response. |
| [`backend/app/services/prompt_service.py`](file:///backend/app/services/prompt_service.py) | **Prompt Pipeline:** Assembles user inquiries into reusable prompt templates and attaches system instructions. |
| [`backend/app/services/llm_service.py`](file:///backend/app/services/llm_service.py) | **Generic LLM Dispatch:** Interacts with the `BaseLLMProvider` abstraction, tracks generation latency, and logs structured operational metrics. |
| [`backend/app/providers/base.py`](file:///backend/app/providers/base.py) | **Provider Contract:** Defines the `BaseLLMProvider` abstract base class and domain exceptions (`LLMTimeoutError`, `LLMEmptyResponseError`, etc.). |
| [`backend/app/providers/gemini.py`](file:///backend/app/providers/gemini.py) | **Gemini SDK Provider:** Encapsulates official Google Gemini SDK (`google-generativeai`) calls, configuration, timeouts, and error translation. |
| [`backend/app/prompts/system.py`](file:///backend/app/prompts/system.py) | **System Instructions:** Defines assistant role, technical accuracy standards, uncertainty handling, and formatting instructions. |
| [`backend/app/prompts/templates.py`](file:///backend/app/prompts/templates.py) | **Prompt Templates:** Reusable template formatters with variable validation to decouple prompt formatting from business code. |
| [`backend/app/core/config.py`](file:///backend/app/core/config.py) | **Settings & Environment:** Loads and validates configuration (`GEMINI_API_KEY`, `GEMINI_MODEL`, timeouts, CORS) using `pydantic-settings`. |
| [`backend/app/core/logging.py`](file:///backend/app/core/logging.py) | **Structured Logging:** Formats logs as JSON without logging confidential user queries, tokens, or API keys. |
| [`backend/tests/test_chat.py`](file:///backend/tests/test_chat.py) | **Automated Tests:** Unit and integration tests for `/chat`, request validation, provider timeout/error mapping, and `/health`. |

### Frontend (`frontend/`)

| File Path | Responsibility |
|:---|:---|
| [`frontend/src/app/page.tsx`](file:///frontend/src/app/page.tsx) | **Interactive Chat UI:** User interface with real-time loading spinners, error alerts, architecture trace visualizer, and preset exploration questions. |
| [`frontend/src/services/api.ts`](file:///frontend/src/services/api.ts) | **Frontend API Service:** Isolates all network calls to the FastAPI backend. Ensures no LLM SDK is loaded in the browser. |
| [`frontend/src/types/chat.ts`](file:///frontend/src/types/chat.ts) | **TypeScript Contracts:** Type definitions for chat requests, responses, and message histories. |
| [`frontend/src/app/globals.css`](file:///frontend/src/app/globals.css) | **Global Styling:** Tailwind CSS styles and dark mode theme configuration. |

---

## 🔌 Extensibility: Adding Another LLM Provider

Because this project follows the **Dependency Inversion Principle**, adding a new LLM provider (such as Anthropic Claude, OpenAI, or a local Ollama model) does **NOT** require changing `ChatService` or `PromptService`.

### How to Add a New Provider:

1. Create a new provider file `backend/app/providers/openai_provider.py`:
   ```python
   from app.providers.base import BaseLLMProvider

   class OpenAIProvider(BaseLLMProvider):
       def __init__(self, api_key: str, model: str = "gpt-4o"):
           self.api_key = api_key
           self.model = model

       async def generate_text(self, prompt: str, system_instruction: str | None = None) -> tuple[str, str]:
           # Call OpenAI SDK directly here
           return generated_text, self.model
   ```
2. In `backend/app/api/routes/chat.py` (or your dependency injector), swap:
   ```python
   # provider = GeminiProvider(settings=settings)
   provider = OpenAIProvider(api_key=settings.OPENAI_API_KEY)
   llm_service = LLMService(provider=provider)
   ```
3. `ChatService` continues to work completely unchanged!

---

## 🚀 Getting Started

### 1. Prerequisites

- **Python 3.10+** (tested on Python 3.13)
- **Node.js 18+** & **npm**
- A **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/)

---

### 2. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure environment variables:
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env     # Windows
   cp .env.example .env       # macOS / Linux
   ```
   Edit `.env` and set your key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-1.5-flash
   ```
4. Run automated tests to verify the installation:
   ```bash
   python -m pytest tests/
   ```
5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Interactive Swagger API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Alternative ReDoc Documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - Healthcheck: [http://localhost:8000/health](http://localhost:8000/health)

---

### 3. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install Node dependencies (if not already installed):
   ```bash
   npm install
   ```
3. Verify or create `.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```
4. Start the Next.js development server:
   ```bash
   npm run dev
   ```
5. Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## 🧪 Testing

The backend includes a dedicated test suite using `pytest` and FastAPI's `TestClient` with a mock provider:

```bash
cd backend
python -m pytest tests/ -v
```

Tests verify:
- `POST /chat` success path with mock provider response.
- Input validation: empty strings and whitespace rejection (`HTTP 422`).
- Input validation: missing required fields (`HTTP 422`).
- Upstream timeout exception mapping (`HTTP 504 Gateway Timeout`).
- Empty provider response exception mapping (`HTTP 502 Bad Gateway`).
- Service health check status (`GET /health`).

---

## 🔒 Security Best Practices Implemented

- **No Client Secrets:** The Gemini API key is stored exclusively on the backend server and never sent to the browser.
- **Privacy-Safe Structured Logging:** Log records scrub API keys and do not record raw user question contents in logs.
- **Input Boundaries:** Pydantic models reject excessively large prompts (limiting denial-of-service risks) and empty payloads.
- **Strict Timeouts:** Upstream Gemini requests are bounded by configurable timeout thresholds (`REQUEST_TIMEOUT_SECONDS`).
