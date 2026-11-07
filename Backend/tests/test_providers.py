import json
import asyncio
import httpx
import pytest
from unittest.mock import AsyncMock, patch

from settings import User, Question
from ai_service import GeminiProvider, GroqProvider, OpenRouterProvider
from validator import QuizValidationError

SAMPLE_QUIZ_DICT = {
    "topic": "Python Functions",
    "questions": [
        {
            "id": "q1",
            "question": "How do you define a function in Python?",
            "concept": "Function definition",
            "type": "mcq",
            "options": ["def my_func():", "function my_func():", "fn my_func()", "func my_func():"],
            "answer": ["def my_func():"],
            "description": "Python uses the def keyword.",
            "difficulty": "easy"
        }
    ]
}

SAMPLE_USER = User(content="Python Functions", no_of_questions=1, level="easy")

def test_gemini_provider_success():
    provider = GeminiProvider()
    provider.api_key = "test_gemini_key"
    provider.enabled = True

    gemini_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": json.dumps(SAMPLE_QUIZ_DICT)}]
                }
            }
        ]
    }

    mock_response = httpx.Response(
        status_code=200,
        json=gemini_response_data,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com")
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                quiz = await provider.generate_quiz(SAMPLE_USER, client)
                assert quiz.topic == "Python Functions"
                assert len(quiz.questions) == 1
                assert quiz.questions[0].id == "q1"

                # Verify URL has api key
                called_url = mock_post.call_args[0][0]
                assert "key=test_gemini_key" in called_url

    asyncio.run(run_test())

def test_gemini_provider_rate_limit_429():
    provider = GeminiProvider()
    provider.api_key = "test_gemini_key"

    mock_response = httpx.Response(
        status_code=429,
        text="Resource Exhausted",
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com")
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                with pytest.raises(httpx.HTTPStatusError):
                    await provider.generate_quiz(SAMPLE_USER, client)

    asyncio.run(run_test())

def test_groq_provider_success():
    provider = GroqProvider()
    provider.api_key = "test_groq_key"
    provider.enabled = True

    groq_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(SAMPLE_QUIZ_DICT)
                }
            }
        ]
    }

    mock_response = httpx.Response(
        status_code=200,
        json=groq_response_data,
        request=httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                quiz = await provider.generate_quiz(SAMPLE_USER, client)
                assert quiz.topic == "Python Functions"
                assert quiz.questions[0].id == "q1"

                # Verify Authorization header
                called_headers = mock_post.call_args[1].get("headers", {})
                assert called_headers.get("Authorization") == "Bearer test_groq_key"

    asyncio.run(run_test())

def test_openrouter_provider_success():
    provider = OpenRouterProvider()
    provider.api_key = "test_openrouter_key"
    provider.enabled = True

    openrouter_response_data = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(SAMPLE_QUIZ_DICT)
                }
            }
        ]
    }

    mock_response = httpx.Response(
        status_code=200,
        json=openrouter_response_data,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    )

    async def run_test():
        async with httpx.AsyncClient() as client:
            with patch.object(client, "post", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = mock_response
                quiz = await provider.generate_quiz(SAMPLE_USER, client)
                assert quiz.topic == "Python Functions"

                # Verify OpenRouter headers
                called_headers = mock_post.call_args[1].get("headers", {})
                assert called_headers.get("Authorization") == "Bearer test_openrouter_key"
                assert "HTTP-Referer" in called_headers

    asyncio.run(run_test())

