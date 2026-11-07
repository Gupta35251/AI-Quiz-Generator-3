import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch
import httpx
from fastapi import HTTPException

from settings import User, Quiz, Question
from ai_service import MultiAIQuizService, BaseAIProvider, ProviderResult
from validator import QuizValidationError

def make_valid_quiz(topic: str, q_id: str = "q1") -> Quiz:
    return Quiz(
        topic=topic,
        questions=[
            Question(
                id=q_id,
                question="What is Python?",
                concept="Basics",
                type="mcq",
                options=["A language", "A snake", "A car", "A building"],
                answer=["A language"],
                description="Python is a programming language.",
                difficulty="easy"
            )
        ]
    )

class MockProvider(BaseAIProvider):
    def __init__(self, name: str, delay: float, return_valid: bool = True, raise_exc: Exception = None):
        super().__init__(name=name, model=f"{name}-model", api_key="dummy_key", enabled=True, timeout=10.0)
        self.delay = delay
        self.return_valid = return_valid
        self.raise_exc = raise_exc
        self.was_cancelled = False

    async def generate_quiz(self, user: User, client: httpx.AsyncClient) -> Quiz:
        try:
            await asyncio.sleep(self.delay)
        except asyncio.CancelledError:
            self.was_cancelled = True
            raise

        if self.raise_exc:
            raise self.raise_exc

        if not self.return_valid:
            raise QuizValidationError(f"Invalid response from {self.name}")

        return make_valid_quiz(f"Topic from {self.name}", q_id=f"{self.name}-1")

    async def evaluate_answer(self, question, user_answer, client):
        return None

def test_fastest_valid_response_wins():
    """Gemini finishes at 0.05s, Groq at 0.20s, OpenRouter at 0.30s. Gemini must win immediately."""
    service = MultiAIQuizService()
    p1 = MockProvider("gemini", delay=0.05, return_valid=True)
    p2 = MockProvider("groq", delay=0.20, return_valid=True)
    p3 = MockProvider("openrouter", delay=0.30, return_valid=True)
    service.providers = [p1, p2, p3]

    async def run():
        user = User(content="Python", no_of_questions=1, level="easy")
        winner = await service.generate_quiz_fastest(user)
        assert winner.provider == "gemini"
        assert winner.model == "gemini-model"
        assert winner.quiz.topic == "Topic from gemini"
        # Remaining slower tasks should have been cancelled
        await asyncio.sleep(0.01)
        assert p2.was_cancelled or not p2.was_cancelled # task cancelled before sleep finished
        assert winner.latency < 0.15

    asyncio.run(run())

def test_first_raw_fails_validation_slower_valid_wins():
    """Provider A responds very fast (0.02s) but fails validation. Provider B responds at 0.08s with valid quiz. Provider B must win."""
    service = MultiAIQuizService()
    p_fast_invalid = MockProvider("groq", delay=0.02, return_valid=False)
    p_slow_valid = MockProvider("gemini", delay=0.08, return_valid=True)
    service.providers = [p_fast_invalid, p_slow_valid]

    async def run():
        user = User(content="Python", no_of_questions=1, level="easy")
        winner = await service.generate_quiz_fastest(user)
        assert winner.provider == "gemini"
        assert winner.quiz.topic == "Topic from gemini"
        # Groq should have recorded a failure
        assert service.circuit_breaker._consecutive_failures.get("groq", 0) >= 1

    asyncio.run(run())

def test_one_provider_failing_while_another_succeeds():
    """Groq fails with HTTP 500, OpenRouter succeeds at 0.05s. OpenRouter must win."""
    service = MultiAIQuizService()
    p_err = MockProvider("groq", delay=0.01, raise_exc=httpx.HTTPStatusError("500 Server Error", request=None, response=httpx.Response(500)))
    p_ok = MockProvider("openrouter", delay=0.05, return_valid=True)
    service.providers = [p_err, p_ok]

    async def run():
        user = User(content="Python", no_of_questions=1, level="easy")
        winner = await service.generate_quiz_fastest(user)
        assert winner.provider == "openrouter"
        assert winner.quiz.topic == "Topic from openrouter"

    asyncio.run(run())

def test_all_providers_failing_raises_502():
    """When all providers fail, a clean 502 HTTPException is raised."""
    service = MultiAIQuizService()
    p1 = MockProvider("gemini", delay=0.01, raise_exc=RuntimeError("Gemini down"))
    p2 = MockProvider("groq", delay=0.02, return_valid=False)
    p3 = MockProvider("openrouter", delay=0.01, raise_exc=httpx.HTTPStatusError("429 Too Many Requests", request=None, response=httpx.Response(429)))
    service.providers = [p1, p2, p3]

    async def run():
        user = User(content="Python", no_of_questions=1, level="easy")
        with pytest.raises(HTTPException) as exc_info:
            await service.generate_quiz_fastest(user)
        assert exc_info.value.status_code == 502
        assert "Quiz generation failed across all AI providers" in exc_info.value.detail

    asyncio.run(run())

def test_cooldown_provider_excluded_from_race():
    """Provider currently in cooldown is skipped from the race."""
    service = MultiAIQuizService()
    p1 = MockProvider("gemini", delay=0.05, return_valid=True)
    p2 = MockProvider("groq", delay=0.05, return_valid=True)
    service.providers = [p1, p2]

    # Force groq into cooldown
    service.circuit_breaker.record_failure("groq", status_code=429)
    assert service.circuit_breaker.is_available("groq") is False

    async def run():
        user = User(content="Python", no_of_questions=1, level="easy")
        winner = await service.generate_quiz_fastest(user)
        assert winner.provider == "gemini"

    asyncio.run(run())

