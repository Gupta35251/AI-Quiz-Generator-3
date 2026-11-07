# Quizwise — Multi-Model AI Quiz Generator

Quizwise is an AI-powered educational quiz application built with **React + Vite** on the frontend, **FastAPI** on the backend, **Firebase Authentication**, and **Firestore**.

This version features a **Parallel Fastest-Response Multi-Provider Engine**:
When a quiz is requested, generation requests are dispatched concurrently to **Google Gemini**, **Groq**, and **OpenRouter**. The first provider that returns a fully validated quiz wins and immediately delivers it to the user, while slower tasks are cancelled to optimize latency and quota usage.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   React + Vite Frontend   │
                          └─────────────┬─────────────┘
                                        │ POST /api/quiz/generate
                                        ▼
                          ┌───────────────────────────┐
                          │    FastAPI Backend API    │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           │ Concurrent asyncio tasks   │                            │
           ▼                            ▼                            ▼
  ┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
  │  Google Gemini  │          │      Groq       │          │   OpenRouter    │
  └────────┬────────┘          └────────┬────────┘          └────────┬────────┘
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │ Response Validator Engine │
                          │ (Schema, count, options,  │
                          │   unique IDs, answers)    │
                          └─────────────┬─────────────┘
                                        ▼
                         ★ First Valid Response Wins ★
                         (Cancel remaining running tasks)
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │ Saved to Firestore & Sent │
                          │        to Frontend        │
                          └───────────────────────────┘
```

---

## Quick Setup & Run (Windows PowerShell)

### Prerequisites

- **Python 3.10+** (e.g. Anaconda / Python virtual environment)
- **Node.js 18+** & **npm**
- Firebase Service Account Key JSON (`serviceAccountKey.json`)

---

### Step 1: Configure Environment Variables

1. Navigate to the `Backend` folder:
   ```powershell
   cd "d:\PythonProject\AI Quiz Generator 3\Backend"
   ```
2. Copy `.env.example` to `.env` (if not already present):
   ```powershell
   Copy-Item .env.example .env
   ```
3. Open `Backend\.env` and configure your API keys and models:
   ```env
   # --- AI Providers ---
   GEMINI_API_KEY=your_gemini_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here

   # --- Configurable Model Names ---
   GEMINI_MODEL=gemini-2.5-flash
   GROQ_MODEL=llama-3.3-70b-versatile
   OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct

   # --- Provider Flags & Timeouts ---
   GEMINI_ENABLED=true
   GROQ_ENABLED=true
   OPENROUTER_ENABLED=true

   GEMINI_TIMEOUT=15.0
   GROQ_TIMEOUT=15.0
   OPENROUTER_TIMEOUT=15.0

   # --- Parallel Racing & Reliability ---
   PROVIDER_MAX_RETRIES=1
   PROVIDER_COOLDOWN_SECONDS=60.0
   PROVIDER_CONCURRENCY_LIMIT=3

   # --- Firebase Service Account ---
   FIREBASE_SERVICE_ACCOUNT_PATH=D:\PythonProject\QuizWise-Secrets\serviceAccountKey.json
   ```

---

### Step 2: Install Backend Dependencies

In PowerShell:
```powershell
# Navigate to Backend
cd "d:\PythonProject\AI Quiz Generator 3\Backend"

# Install dependencies
pip install -r requirements-api.txt
```

---

### Step 3: Run Backend Server

In PowerShell:
```powershell
cd "d:\PythonProject\AI Quiz Generator 3\Backend"
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```
Backend will be live at: `http://127.0.0.1:8000`  
Interactive Swagger docs: `http://127.0.0.1:8000/docs`

---

### Step 4: Install & Run Frontend

Open a new PowerShell window:
```powershell
cd "d:\PythonProject\AI Quiz Generator 3\Frontend"

# Install dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```
Frontend will be live at: `http://localhost:5173`

---

## Running Automated Tests

Run the complete test suite (25 tests covering all 3 providers, racing, fastest-response selection, validation, timeouts, 429 rate-limiting, and API endpoints):

```powershell
cd "d:\PythonProject\AI Quiz Generator 3"
pytest Backend/tests -v
```

---

## Features & Reliability Guarantees

1. **Parallel Racing**: Requests are dispatched concurrently to all configured providers using `asyncio` and `httpx`.
2. **First Valid Wins**: Raw responses are strictly validated as they arrive. The first response that passes full validation wins and is returned immediately.
3. **Task Cancellation**: Unfinished slower provider tasks are cancelled immediately upon winning, saving server resources and token quotas.
4. **Circuit Breaker & Cooldown**: Providers that fail repeatedly or encounter HTTP 429 quota exhaustion enter an automatic cooldown (default 60s), preventing subsequent requests from stalling.
5. **Strict Schema & Option Validation**:
   - Exact question count verification.
   - Required question fields (`id`, `question`, `concept`, `type`, `difficulty`, `options`, `answer`, `description`).
   - Answer options: uniqueness and minimum 2 options.
   - Answer references: all answers must match listed options.
   - Unique question IDs across the quiz.
6. **Zero Secrets Leaked**: API keys and internal traces are kept exclusively on the backend and are never returned in responses or logs.

