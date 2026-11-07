# Quizwise Upgrade — Changes Documentation

This document explains in short, simple terms the changes made across the project to implement concurrent multi-model quiz generation.

---

## 1. Summary of Changes

Quizwise previously generated quizzes solely using Google Gemini in a sequential manner. It now uses a **concurrent racing architecture**:
- **3 Providers**: Google Gemini, Groq, and OpenRouter compete in parallel.
- **Fastest Valid Wins**: Whichever provider returns the first fully valid quiz provides the response to the user.
- **Automatic Cancellation**: Slower tasks are immediately cancelled to save tokens and resources.
- **Circuit Breaker**: Providers encountering rate limits (HTTP 429) or consecutive failures automatically enter cooldown so requests don't hang.
- **Zero Frontend Breaking Changes**: The existing React UI, Firebase Auth, Firestore database, and API contracts are 100% preserved.

---

## 2. File-by-File Changes

### New Files Created

1. **`Backend/config.py`**
   - Central configuration file loading environment variables from `Backend/.env`.
   - Manages API keys, model names, enable/disable flags, individual provider timeouts, and circuit breaker settings.

2. **`Backend/validator.py`**
   - Strict quiz response validator.
   - Verifies:
     - Correct JSON format (removes markdown code fences if present).
     - Exact requested question count.
     - Required fields (`id`, `question`, `concept`, `type`, `difficulty`, `options`, `answer`, `description`).
     - Unique question IDs across the quiz.
     - MCQ & multiple-answer options (minimum 2 options, no duplicates).
     - Answer references (answers must match available options).

3. **`Backend/circuit_breaker.py`**
   - Health and cooldown manager for providers.
   - Trips circuit to `OPEN` after 3 failures or on HTTP 429 rate limit.
   - Automatically probes after cooldown timer (`HALF_OPEN`).
   - Tracks metrics: total requests, wins, average latency per provider.

4. **`Backend/ai_service.py`**
   - Contains modular providers: `GeminiProvider`, `GroqProvider`, and `OpenRouterProvider`.
   - Implements `MultiAIQuizService`:
     - Dispatches concurrent tasks with `asyncio.create_task` and `httpx.AsyncClient`.
     - Races tasks using `asyncio.as_completed`.
     - Cancels remaining tasks as soon as the first valid quiz arrives.
     - Includes provider-fallback logic for evaluating subjective code/theory answers.
     - Provides `/api/providers/status` metrics without exposing secrets.

5. **`Backend/.env.example`**
   - Clean template showing all required and optional environment variables.

6. **`Backend/tests/` (25 Automated Tests)**
   - `test_validator.py`: 9 tests for JSON extraction, schema validation, option checks, duplicate ID detection.
   - `test_circuit_breaker.py`: 4 tests for state transitions, failure threshold, 429 handling, and cooldown recovery.
   - `test_providers.py`: 4 tests for Gemini, Groq, and OpenRouter mocked HTTP requests and error handling.
   - `test_concurrent_race.py`: 5 tests verifying that the fastest valid response wins, slower tasks cancel, invalid responses are rejected, and failover works.
   - `test_api_integration.py`: 3 end-to-end tests for `/api/health`, `/api/providers/status`, and quiz generation/submission/history.

7. **`pytest.ini`**
   - Adds `Backend` to pythonpath for clean pytest discovery.

8. **`README.md`**
   - Complete setup guide and Windows PowerShell startup instructions.

---

### Modified Files

1. **`Backend/settings.py`**
   - Added `id: Optional[str] = None` to `Question` model to support question ID validation while remaining 100% backward-compatible with existing stored quizzes.

2. **`Backend/database.py`**
   - Updated `create_quiz_session` and `save_quiz` to accept an optional `metadata` dictionary (stores winning provider, model, and latency in Firestore).

3. **`Backend/firebase_service.py`**
   - Added `LazyDB` wrapper so importing the module in offline/test environments does not block on gRPC network discovery.
   - Added `FIREBASE_SERVICE_ACCOUNT_PATH` environment variable support.

4. **`Backend/llm.py`**
   - Replaced single-provider logic with multi-provider async functions:
     - `generate_answer_async(user: User)`: runs fastest-response race.
     - `generate_answer(user: User)`: synchronous wrapper for backward compatibility.
     - `evaluate_answer_async(question, user_answer)`: resilient multi-provider answer evaluation.
     - Preserved `check_answer(question, user_answer)`.

5. **`Backend/api.py`**
   - Converted `create_quiz_for_user`, `generate_quiz`, `submit_quiz`, and `generate_weekly_quiz` to `async def` for native non-blocking async execution.
   - Added `id` into `make_safe_quiz`.
   - Recorded winning provider metadata in Firestore session and response.
   - Added `GET /api/providers/status` endpoint to monitor provider health.
   - Migrated startup event to modern FastAPI `lifespan` handler.

6. **`Backend/requirements-api.txt`**
   - Added `httpx` and `pytest` dependencies.

7. **`Backend/.env`**
   - Added configurable placeholders for `GROQ_API_KEY`, `OPENROUTER_API_KEY`, models, timeouts, and flags while preserving existing keys.

---

## 3. How to Verify

Run all 25 automated unit and integration tests:
```powershell
pytest Backend/tests -v
```
All 25 tests pass in ~4 seconds with zero API quota consumption!

