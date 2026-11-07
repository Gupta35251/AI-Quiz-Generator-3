import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import httpx
from fastapi import HTTPException

from config import config
from settings import User, Quiz, Evaluation, Question
from validator import validate_quiz_response, QuizValidationError
from circuit_breaker import ProviderCircuitBreaker

logger = logging.getLogger("quizwise.ai_service")

QUIZ_SYSTEM_PROMPT = (
    "You are an expert educational quiz generator for Quizwise. "
    "You generate high-quality quizzes strictly adhering to the requested JSON schema. "
    "Output raw JSON only. Do not wrap output in markdown code blocks or provide any introductory or concluding text."
)

def build_quiz_prompt(user: User) -> str:
    return f"""Create exactly {user.no_of_questions} questions about: {user.content}
Difficulty: {user.level}
Return the topic name and questions.

Include a balanced mix of these question types where suitable:
mcq, multiple_answer, code, theory.
Each question must include a unique "id" (e.g. "q1", "q2", "q3", ...), its correct answer, a clear explanation in description,
and its difficulty. For mcq and multiple_answer, include options.
For multiple_answer, clearly design questions that have more than one correct answer.
Make questions accurate and appropriate for the requested difficulty.
Each question must include a short "concept" (2-4 words, e.g. "Python loops").
Reuse the exact same concept name for related questions.

Required JSON Structure:
{{
  "topic": "string (the quiz topic)",
  "questions": [
    {{
      "id": "q1",
      "question": "string (question text)",
      "concept": "string (2-4 words)",
      "type": "mcq" | "multiple_answer" | "code" | "theory",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": ["Option A"],
      "description": "string (detailed explanation)",
      "difficulty": "easy" | "medium" | "hard"
    }}
  ]
}}"""

def build_eval_prompt(question: Any, user_answer: List[str]) -> str:
    return f"""Evaluate the learner's answer fairly. Accept equivalent correct wording or code when appropriate.
Question: {getattr(question, 'question', question)}
Question type: {getattr(question, 'type', 'unknown')}
Expected answer: {getattr(question, 'answer', [])}
Learner's answer: {user_answer}

Return whether it is correct and a helpful explanation.
If incorrect, explain the underlying concept simply and show the correct answer.
Do not mark a substantially correct answer wrong merely because of minor wording differences.

Required JSON Structure:
{{
  "question": "string",
  "user_answer": ["string"],
  "correct_answer": ["string"],
  "is_correct": true | false,
  "description": "string (explanation)"
}}"""


@dataclass
class ProviderResult:
    provider: str
    model: str
    quiz: Quiz
    latency: float


class BaseAIProvider(ABC):
    def __init__(self, name: str, model: str, api_key: str, enabled: bool, timeout: float):
        self.name = name
        self.model = model
        self.api_key = api_key
        self.enabled = enabled
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    @property
    def is_enabled(self) -> bool:
        return self.enabled and self.is_configured

    @abstractmethod
    async def generate_quiz(self, user: User, client: httpx.AsyncClient) -> Quiz:
        """Call provider endpoint, validate response, and return Quiz object."""
        pass

    @abstractmethod
    async def evaluate_answer(
        self, question: Any, user_answer: List[str], client: httpx.AsyncClient
    ) -> Evaluation:
        """Evaluate a learner's subjective answer."""
        pass


class GeminiProvider(BaseAIProvider):
    def __init__(self):
        super().__init__(
            name="gemini",
            model=config.GEMINI_MODEL,
            api_key=config.GEMINI_API_KEY,
            enabled=config.GEMINI_ENABLED,
            timeout=config.GEMINI_TIMEOUT,
        )

    async def generate_quiz(self, user: User, client: httpx.AsyncClient) -> Quiz:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        prompt = f"{QUIZ_SYSTEM_PROMPT}\n\n{build_quiz_prompt(user)}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.5,
            },
        }

        attempts = 1 + max(0, config.PROVIDER_MAX_RETRIES)
        last_error = None

        for attempt in range(attempts):
            try:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                )
                if response.status_code == 429:
                    raise httpx.HTTPStatusError(
                        "Rate limit exceeded",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    raise QuizValidationError("Gemini returned empty candidates")

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts or "text" not in parts[0]:
                    raise QuizValidationError("Gemini returned no text content")

                raw_text = parts[0]["text"]
                return validate_quiz_response(raw_text, user.no_of_questions)

            except httpx.HTTPStatusError as err:
                last_error = err
                if err.response.status_code == 429:
                    # Do not retry on 429 to avoid wasting quota
                    raise
                if err.response.status_code >= 500 and attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise
            except httpx.RequestError as err:
                last_error = err
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise
            except QuizValidationError:
                raise
            except Exception as err:
                last_error = err
                raise QuizValidationError(f"Gemini processing error: {err}") from err

        raise last_error or RuntimeError("Gemini failed after retries")

    async def evaluate_answer(
        self, question: Any, user_answer: List[str], client: httpx.AsyncClient
    ) -> Evaluation:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent?key={self.api_key}"
        )
        prompt = build_eval_prompt(question, user_answer)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }
        response = await client.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)
        return Evaluation.model_validate(parsed)


class GroqProvider(BaseAIProvider):
    def __init__(self):
        super().__init__(
            name="groq",
            model=config.GROQ_MODEL,
            api_key=config.GROQ_API_KEY,
            enabled=config.GROQ_ENABLED,
            timeout=config.GROQ_TIMEOUT,
        )

    async def generate_quiz(self, user: User, client: httpx.AsyncClient) -> Quiz:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
                {"role": "user", "content": build_quiz_prompt(user)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.5,
        }

        attempts = 1 + max(0, config.PROVIDER_MAX_RETRIES)
        last_error = None

        for attempt in range(attempts):
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                )
                if response.status_code == 429:
                    raise httpx.HTTPStatusError(
                        "Rate limit exceeded",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise QuizValidationError("Groq returned empty choices")

                raw_text = choices[0].get("message", {}).get("content", "")
                return validate_quiz_response(raw_text, user.no_of_questions)

            except httpx.HTTPStatusError as err:
                last_error = err
                if err.response.status_code == 429:
                    raise
                if err.response.status_code >= 500 and attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise
            except httpx.RequestError as err:
                last_error = err
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise
            except QuizValidationError:
                raise
            except Exception as err:
                last_error = err
                raise QuizValidationError(f"Groq processing error: {err}") from err

        raise last_error or RuntimeError("Groq failed after retries")

    async def evaluate_answer(
        self, question: Any, user_answer: List[str], client: httpx.AsyncClient
    ) -> Evaluation:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Evaluate student answer in strict JSON adhering to schema.",
                },
                {"role": "user", "content": build_eval_prompt(question, user_answer)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        response = await client.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_text)
        return Evaluation.model_validate(parsed)


class OpenRouterProvider(BaseAIProvider):
    def __init__(self):
        super().__init__(
            name="openrouter",
            model=config.OPENROUTER_MODEL,
            api_key=config.OPENROUTER_API_KEY,
            enabled=config.OPENROUTER_ENABLED,
            timeout=config.OPENROUTER_TIMEOUT,
        )

    async def generate_quiz(self, user: User, client: httpx.AsyncClient) -> Quiz:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://quizwise.app",
            "X-Title": "Quizwise",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
                {"role": "user", "content": build_quiz_prompt(user)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.5,
        }

        attempts = 1 + max(0, config.PROVIDER_MAX_RETRIES)
        last_error = None

        for attempt in range(attempts):
            try:
                response = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=httpx.Timeout(self.timeout, connect=5.0),
                )
                if response.status_code == 429:
                    raise httpx.HTTPStatusError(
                        "Rate limit exceeded",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    raise QuizValidationError("OpenRouter returned empty choices")

                raw_text = choices[0].get("message", {}).get("content", "")
                return validate_quiz_response(raw_text, user.no_of_questions)

            except httpx.HTTPStatusError as err:
                last_error = err
                if err.response.status_code == 429:
                    raise
                if err.response.status_code >= 500 and attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise
            except httpx.RequestError as err:
                last_error = err
                if attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise
            except QuizValidationError:
                raise
            except Exception as err:
                last_error = err
                raise QuizValidationError(f"OpenRouter processing error: {err}") from err

        raise last_error or RuntimeError("OpenRouter failed after retries")

    async def evaluate_answer(
        self, question: Any, user_answer: List[str], client: httpx.AsyncClient
    ) -> Evaluation:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://quizwise.app",
            "X-Title": "Quizwise",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Evaluate student answer in strict JSON adhering to schema.",
                },
                {"role": "user", "content": build_eval_prompt(question, user_answer)},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        response = await client.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        parsed = json.loads(raw_text)
        return Evaluation.model_validate(parsed)


class MultiAIQuizService:
    """
    Coordinates concurrent quiz generation across configured AI providers.
    - Sends requests to Google Gemini, Groq, and OpenRouter concurrently.
    - Limits concurrency to 3 providers per request.
    - Immediately validates each response upon arrival.
    - The first valid response wins and is returned instantly.
    - Cancels remaining running tasks to save resources.
    - Handles timeouts, rate limits (429), and failures gracefully with a circuit breaker.
    """
    def __init__(self):
        self.circuit_breaker = ProviderCircuitBreaker(
            failure_threshold=3,
            cooldown_seconds=config.PROVIDER_COOLDOWN_SECONDS,
        )
        self.providers: List[BaseAIProvider] = [
            GeminiProvider(),
            GroqProvider(),
            OpenRouterProvider(),
        ]

    def get_configured_providers(self) -> List[BaseAIProvider]:
        return [p for p in self.providers if p.is_enabled]

    def get_provider_status(self) -> Dict[str, Any]:
        """Provides status summary for monitoring without leaking secrets."""
        cb_stats = self.circuit_breaker.get_status()
        res = {}
        for p in self.providers:
            stats = cb_stats.get(p.name, {})
            res[p.name] = {
                "enabled": p.enabled,
                "configured": p.is_configured,
                "model": p.model,
                "timeout_sec": p.timeout,
                "circuit_state": stats.get("state", "CLOSED"),
                "consecutive_failures": stats.get("consecutive_failures", 0),
                "total_requests": stats.get("total_requests", 0),
                "wins": stats.get("wins", 0),
                "avg_latency_sec": stats.get("avg_latency_sec", 0.0),
                "cooldown_remaining_sec": stats.get("cooldown_remaining_sec", 0),
            }
        return res

    async def generate_quiz_fastest(self, user: User) -> ProviderResult:
        """
        Races all available configured providers concurrently.
        First valid response wins and remaining tasks are cancelled immediately.
        """
        # 1. Filter enabled, configured providers that are not cooling down
        available = [
            p for p in self.providers
            if p.is_enabled and self.circuit_breaker.is_available(p.name)
        ]

        if not available:
            # Check if providers are configured but all cooling down
            configured = [p for p in self.providers if p.is_enabled]
            if configured:
                logger.warning("All configured AI providers are currently cooling down.")
                raise HTTPException(
                    status_code=503,
                    detail="AI providers are temporarily busy or cooling down. Please try again in a few moments.",
                )
            logger.error("No AI providers configured with valid API keys.")
            raise HTTPException(
                status_code=500,
                detail="No AI providers are configured on the server. Please check backend environment configuration.",
            )

        # 2. Limit concurrency to maximum of 3 providers per request
        concurrency_limit = min(config.PROVIDER_CONCURRENCY_LIMIT, 3)
        selected_providers = available[:concurrency_limit]
        provider_names = [p.name for p in selected_providers]
        logger.info(f"Starting parallel quiz generation race with providers: {provider_names}")

        # 3. Launch concurrent tasks using httpx.AsyncClient
        async with httpx.AsyncClient() as client:
            async def run_single_provider(prov: BaseAIProvider) -> ProviderResult:
                t0 = time.monotonic()
                try:
                    quiz = await prov.generate_quiz(user, client)
                    latency = time.monotonic() - t0
                    return ProviderResult(
                        provider=prov.name,
                        model=prov.model,
                        quiz=quiz,
                        latency=latency,
                    )
                except httpx.HTTPStatusError as err:
                    latency = time.monotonic() - t0
                    status = err.response.status_code if err.response is not None else None
                    self.circuit_breaker.record_failure(prov.name, status_code=status, error_msg=str(err))
                    raise
                except Exception as err:
                    latency = time.monotonic() - t0
                    self.circuit_breaker.record_failure(prov.name, status_code=None, error_msg=str(err))
                    raise

            # Spawn concurrent tasks
            task_map = {
                asyncio.create_task(run_single_provider(p), name=p.name): p.name
                for p in selected_providers
            }
            tasks = list(task_map.keys())

            winner: Optional[ProviderResult] = None
            errors: Dict[str, str] = {}

            # 4. First valid response wins!
            for completed_fut in asyncio.as_completed(tasks):
                try:
                    result = await completed_fut
                    winner = result
                    # Winner found! Stop waiting for remaining tasks
                    break
                except asyncio.CancelledError:
                    continue
                except Exception as exc:
                    prov_name = "unknown"
                    for t, name in task_map.items():
                        if t.done() and not t.cancelled() and t.exception() == exc:
                            prov_name = name
                            break
                    clean_err = str(exc)
                    errors[prov_name] = clean_err
                    logger.warning(f"Provider '{prov_name}' failed validation or request: {clean_err}")

            # 5. Immediately cancel remaining running tasks
            cancelled_count = 0
            for t in tasks:
                if not t.done():
                    t.cancel()
                    cancelled_count += 1

            if cancelled_count > 0:
                logger.debug(f"Cancelled {cancelled_count} slower provider task(s) following winning response.")

            # 6. If a winner succeeded, record success and return it
            if winner is not None:
                self.circuit_breaker.record_success(winner.provider, winner.latency)
                logger.info(
                    f"[RACE WINNER] Provider: '{winner.provider}' | Model: '{winner.model}' | "
                    f"Latency: {winner.latency:.2f}s | Questions: {len(winner.quiz.questions)}"
                )
                return winner

            # 7. If all failed, log summary and return clear error
            logger.error(f"All concurrent quiz providers failed. Details: {errors}")
            raise HTTPException(
                status_code=502,
                detail="Quiz generation failed across all AI providers. Please try again.",
            )

    async def evaluate_answer(self, question: Any, user_answer: List[str]) -> Evaluation:
        """
        Evaluates a subjective question using available providers with automatic fallback.
        """
        available = [
            p for p in self.providers
            if p.is_enabled and self.circuit_breaker.is_available(p.name)
        ]
        if not available:
            available = [p for p in self.providers if p.is_enabled]

        if not available:
            raise RuntimeError("No AI providers configured for answer evaluation")

        async with httpx.AsyncClient() as client:
            last_err = None
            for provider in available:
                try:
                    return await provider.evaluate_answer(question, user_answer, client)
                except Exception as err:
                    last_err = err
                    logger.warning(f"Provider '{provider.name}' failed answer evaluation: {err}")
                    continue

            raise RuntimeError(f"All providers failed evaluation: {last_err}")


ai_service = MultiAIQuizService()

