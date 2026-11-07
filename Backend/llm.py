import asyncio
import logging
from typing import List, Any
from settings import User, Evaluation, Quiz
from ai_service import ai_service, ProviderResult

logger = logging.getLogger("quizwise.llm")

async def generate_answer_async(user: User) -> ProviderResult:
    """Concurrent fastest-response quiz generation across all enabled AI providers."""
    return await ai_service.generate_quiz_fastest(user)

def generate_answer(user: User) -> Quiz:
    """
    Synchronous backward-compatible wrapper for quiz generation.
    Returns the winning Quiz object.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Running inside an active event loop without await: use a thread executor
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            result = pool.submit(asyncio.run, ai_service.generate_quiz_fastest(user)).result()
            return result.quiz
    else:
        result = asyncio.run(ai_service.generate_quiz_fastest(user))
        return result.quiz

async def evaluate_answer_async(question: Any, user_answer: List[str]) -> Evaluation:
    """Asynchronous evaluation of learner's answer with provider fallback."""
    return await ai_service.evaluate_answer(question, user_answer)

def evaluate_answer(question: Any, user_answer: List[str]) -> Evaluation:
    """Synchronous backward-compatible wrapper for answer evaluation."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, ai_service.evaluate_answer(question, user_answer)).result()
    else:
        return asyncio.run(ai_service.evaluate_answer(question, user_answer))

def check_answer(question: Any, user_answer: List[str]) -> bool:
    """
    Checks multiple choice or multiple answer questions deterministically.
    Compares normalized expected answers with user submitted answers.
    """
    expected = {str(answer).strip().casefold() for answer in getattr(question, "answer", [])}
    given = {str(answer).strip().casefold() for answer in user_answer if str(answer).strip()}
    return bool(expected) and expected == given
