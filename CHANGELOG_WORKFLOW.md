# AI Assistant - Task Workflow & Architecture Change Log 📋

This document maintains a continuous, detailed record of all architectural updates, bugs encountered, root cause analyses, code changes, and resolution workflows across the lifecycle of the **AI Assistant** application.

---

## 📑 Workflow Log Entries

### [2026-09-24] - Task 01: Core Architecture Implementation & Repository Scaffolding

#### 1. Goal & Context
Build a learning-focused, end-to-end Generative AI application to demonstrate the complete, unabstracted LLM application pipeline without heavy orchestration frameworks (no LangChain, no LangGraph).

#### 2. Architecture Implemented
```
User (Browser)
  ↓
Next.js Chat UI (frontend/src/app/page.tsx)
  ↓ [POST /chat]
FastAPI Controller (backend/app/api/routes/chat.py)
  ↓ [Pydantic v2 boundary validation]
ChatService (backend/app/services/chat_service.py)
  ↓ [Prompt construction request]
PromptService (backend/app/services/prompt_service.py)
  ↓ [Formatted template + system instruction]
LLMService (backend/app/services/llm_service.py)
  ↓ [Provider contract + latency metrics]
GeminiProvider (backend/app/providers/gemini.py)
  ↓ [Direct google-generativeai SDK call]
Google Gemini API (Cloud)
  ↓ [Candidates & safety verification]
ChatService Validation (ChatResponse domain model)
  ↓ [HTTP 200 JSON]
Next.js Chat UI
```

#### 3. Key Design Decisions
- **Provider Pattern (`backend/app/providers/base.py`):** An abstract base class (`BaseLLMProvider`) defines the LLM contract. Swapping Gemini for OpenAI, Anthropic, or local models requires zero changes to `ChatService`.
- **Direct Gemini SDK:** Used `google-generativeai` directly without intermediate wrappers.
- **Privacy-Safe Structured Logging:** Logs execution latency and model identifiers as structured JSON while scrubbing credentials and sensitive user inputs.
- **Frontend Isolation:** Next.js exclusively communicates with FastAPI `/chat`; no LLM API keys or SDKs are loaded in the browser.

#### 4. Files Created
- **Backend:** `app/main.py`, `app/api/routes/chat.py`, `app/schemas/chat.py`, `app/services/chat_service.py`, `app/services/prompt_service.py`, `app/services/llm_service.py`, `app/providers/base.py`, `app/providers/gemini.py`, `app/prompts/system.py`, `app/prompts/templates.py`, `app/core/config.py`, `app/core/logging.py`, `tests/test_chat.py`.
- **Frontend:** `src/app/page.tsx`, `src/services/api.ts`, `src/types/chat.ts`, `src/app/layout.tsx`.
- **Configuration:** `backend/.env.example`, `backend/requirements.txt`, `backend/pytest.ini`, `frontend/.env.example`, `frontend/.env.local`, root `.gitignore`, root `README.md`.

#### 5. Verification
- Pytest suite executed: 6 passed in 1.18s (`test_health_check`, `test_chat_success`, `test_chat_validation_empty_string`, `test_chat_validation_missing_field`, `test_chat_provider_timeout_maps_to_504`, `test_chat_empty_response_maps_to_502`).
- Next.js build executed: Compiled with Turbopack and TypeScript verification without errors.

---

### [2026-09-24] - Task 02: CORS Origin Multi-Port Resolution (`OPTIONS /chat 400`)

#### 1. Issue Encountered
When the frontend initiated a request to the backend, the browser console and server logged:
```text
INFO: 127.0.0.1 - "OPTIONS /chat HTTP/1.1" 400 Bad Request
```

#### 2. Root Cause Analysis
- The FastAPI backend was originally configured with `CORS_ORIGINS=["http://localhost:3000"]`.
- When the user launched Next.js while port 3000 was already bound by another process, Next.js automatically bound to port `3001` (`http://localhost:3001`).
- The browser sent an HTTP preflight request (`OPTIONS /chat`) containing the header `Origin: http://localhost:3001`.
- Because `http://localhost:3001` was not in the backend's allowed origins whitelist, the CORS middleware rejected the request with HTTP 400 Bad Request.

#### 3. Resolution & Code Changes
Updated CORS settings to whitelist both standard local development ports:
- **`backend/app/core/config.py`:**
  ```python
  CORS_ORIGINS: List[str] = Field(
      default=["http://localhost:3000", "http://localhost:3001"],
      description="Allowed origins for frontend CORS communication"
  )
  ```
- **`backend/.env` & `backend/.env.example`:**
  ```env
  CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
  ```

#### 4. Verification
The backend server reloaded with Uvicorn. Preflight `OPTIONS` requests from `http://localhost:3001` and `http://localhost:3000` are permitted and return HTTP 200 with appropriate CORS headers (`access-control-allow-origin`).

---

### [2026-09-24] - Task 03: Gemini Model Version Deprecation (`gemini-1.5-flash` → `gemini-3.6-flash`)

#### 1. Issue Encountered
Submitting a chat question returned the following error banner on the frontend:
```text
Upstream LLM Provider error: Gemini API error: 404 models/gemini-1.5-flash is not found for API version v1beta, or is not supported for generateContent. Call ModelService.ListModels to see the list of available models and their supported methods.
```

#### 2. Root Cause Analysis
- We ran programmatic model discovery using `genai.list_models()` with the user's active API key.
- Google's Generative Language API endpoint responded that older generation model identifiers (`models/gemini-1.5-flash` and `models/gemini-2.5-flash`) have been deprecated and retired for new API project endpoints:
  > *"404 This model models/gemini-2.5-flash is no longer available to new users. Please update your code to use models/gemini-3.6-flash for the latest features and improvements."*
- Testing `gemini-3.8-flash` on the free tier encountered rate limits (5 RPM limit quota), whereas `gemini-3.6-flash` is fully available and generated responses instantly without quota friction.

#### 3. Resolution & Code Changes
- **`backend/.env`:**
  ```env
  GEMINI_MODEL=gemini-3.6-flash
  ```
- **`backend/.env.example`:**
  ```env
  GEMINI_MODEL=gemini-3.6-flash
  ```
- **`backend/app/core/config.py`:**
  ```python
  GEMINI_MODEL: str = Field(
      default="gemini-3.6-flash",
      description="Target Gemini foundational model identifier"
  )
  ```

#### 4. Verification
- Executed direct SDK verification script:
  ```python
  model = genai.GenerativeModel('gemini-3.6-flash')
  response = model.generate_content('Say hello')
  # Output: "Hello, I hope you are having a wonderful day!"
  ```
- Automated test suite re-verified with `python -m pytest tests/` (6/6 tests passing).
- Committed changes to branch `features/AI_assistant`.

---

## 📌 Standard Operating Procedure for Future Changes

Whenever a new feature, bug fix, or model update is performed:
1. **Identify Issue / Request:** Document user request or error stack trace.
2. **Conduct Root Cause Analysis:** Investigate why the behavior occurred.
3. **Execute Minimal, Targeted Changes:** Edit code cleanly following architecture principles.
4. **Run Automated Tests / Build:** Verify that no regressions were introduced.
5. **Update This Log (`CHANGELOG_WORKFLOW.md`):** Append a new chronological entry containing issue, root cause, changed files, and verification results.
