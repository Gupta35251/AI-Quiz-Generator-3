import uuid
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from settings import User, Quiz, QuizResult
from llm import generate_answer_async, evaluate_answer_async, check_answer
from ai_service import ai_service
from firebase_auth import verify_firebase_token
from database import (init_db, create_user, create_quiz_session, get_quiz_session,
    mark_quiz_session_submitted, save_quiz, get_all_history, get_history_by_id,
    record_concept_result, get_weak_concepts, get_last_weekly_quiz, save_weekly_quiz)

logger = logging.getLogger("quizwise.api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    status = ai_service.get_provider_status()
    logger.info(f"Quizwise API started. Configured AI providers: {status}")
    yield

app = FastAPI(title="Quizwise API", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[
    "http://localhost:5173", "http://127.0.0.1:5173",
    "https://ai-quiz-generator-2.vercel.app"
], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class GenerateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    no_of_questions: int = Field(ge=1, le=30)
    level: Literal["easy", "medium", "hard"]

class SubmitRequest(BaseModel):
    session_id: str
    answers: list[list[str]]

def get_current_user(token=Depends(verify_firebase_token)):
    uid = token.get("uid")
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid Firebase user token")
    email = token.get("email", "")
    create_user(uid, email, token.get("name"))
    return {"id": uid, "uid": uid, "email": email, "name": token.get("name")}

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/auth/me")
def current_user(user=Depends(get_current_user)):
    return {"user": user}

@app.get("/api/providers/status")
def provider_status(user=Depends(get_current_user)):
    """Returns AI provider health and performance statistics."""
    return ai_service.get_provider_status()

def make_safe_quiz(quiz):
    """Sanitizes quiz object before sending to frontend (removes answers and explanations)."""
    return {
        "topic": quiz.topic,
        "questions": [{
            "id": getattr(q, "id", None),
            "question": q.question,
            "type": q.type,
            "options": q.options,
            "difficulty": q.difficulty,
            "concept": getattr(q, "concept", None)
        } for q in quiz.questions]
    }

async def create_quiz_for_user(payload, user_id):
    request = User(
        content=payload.content.strip(),
        no_of_questions=payload.no_of_questions,
        level=payload.level
    )
    result = await generate_answer_async(request)
    quiz = result.quiz

    if quiz is None or not quiz.questions:
        raise HTTPException(
            status_code=502,
            detail="The AI could not generate a quiz. Please try again."
        )

    topic = (quiz.topic or "").strip()
    if not topic or topic.lower() in {"quiz", "questions"}:
        topic = payload.content.strip().replace("\n", " ")
    quiz.topic = topic[:100]

    session_id = str(uuid.uuid4())
    quiz_date = datetime.now(timezone.utc).isoformat(timespec="seconds")
    metadata = {
        "winning_provider": result.provider,
        "model": result.model,
        "latency_ms": round(result.latency * 1000, 2)
    }

    create_quiz_session(session_id, user_id, quiz_date, quiz.model_dump(), metadata=metadata)
    return {
        "session_id": session_id,
        "quiz": make_safe_quiz(quiz),
        "metadata": metadata
    }

@app.post("/api/quiz/generate")
async def generate_quiz(payload: GenerateRequest, user=Depends(get_current_user)):
    try:
        return await create_quiz_for_user(payload, user["id"])
    except HTTPException:
        raise
    except Exception as exc:
        traceback.print_exc()
        raise HTTPException(
            status_code=502,
            detail="Quiz generation failed. Please try again."
        ) from exc

@app.post("/api/quiz/submit")
async def submit_quiz(payload: SubmitRequest, user=Depends(get_current_user)):
    uid = user["id"]
    stored = get_quiz_session(payload.session_id, uid)
    if not stored:
        raise HTTPException(
            status_code=404,
            detail="Quiz session not found. Please generate a new quiz."
        )
    if stored.get("submitted"):
        raise HTTPException(status_code=409, detail="This quiz has already been submitted.")

    quiz = Quiz.model_validate(stored["quiz"])
    if len(payload.answers) != len(quiz.questions):
        raise HTTPException(
            status_code=400,
            detail="Please submit an answer for every question."
        )

    results = []
    for question, raw in zip(quiz.questions, payload.answers):
        answer = [str(x).strip() for x in raw if str(x).strip()]
        if question.type in ("mcq", "multiple_answer"):
            correct = check_answer(question, answer)
            result = QuizResult(
                question=question.question,
                is_correct=correct,
                user_answer=answer,
                correct_answer=question.answer,
                description=question.description
            )
        else:
            try:
                evaluation = await evaluate_answer_async(question, answer)
                if evaluation is None:
                    raise RuntimeError("AI evaluation returned no result")
                result = QuizResult(
                    question=question.question,
                    is_correct=evaluation.is_correct,
                    user_answer=evaluation.user_answer,
                    correct_answer=evaluation.correct_answer,
                    description=evaluation.description
                )
            except Exception as exc:
                raise HTTPException(
                    status_code=502,
                    detail="Could not evaluate an answer. Please try again."
                ) from exc
        results.append(result)

    if not mark_quiz_session_submitted(payload.session_id, uid):
        raise HTTPException(status_code=409, detail="This quiz has already been submitted.")

    score = sum(1 for r in results if r.is_correct)
    metadata = stored.get("metadata")
    save_quiz(
        uid,
        stored["date"],
        quiz.model_dump(),
        [r.model_dump() for r in results],
        score,
        metadata=metadata
    )

    for question, result in zip(quiz.questions, results):
        record_concept_result(
            uid,
            getattr(question, "concept", None) or quiz.topic,
            result.is_correct
        )

    return {
        "score": score,
        "total": len(results),
        "results": [r.model_dump() for r in results]
    }

@app.get("/api/history")
def history(user=Depends(get_current_user)):
    return {"items": get_all_history(user["id"])}

@app.get("/api/history/{quiz_id}")
def history_item(quiz_id: str, user=Depends(get_current_user)):
    item = get_history_by_id(quiz_id, user["id"])
    if not item:
        raise HTTPException(status_code=404, detail="Quiz history entry not found.")
    return item

@app.get("/api/weak-concepts")
def weak_concepts(user=Depends(get_current_user)):
    return {"items": get_weak_concepts(user["id"])}

@app.post("/api/weekly-quiz/generate")
async def generate_weekly_quiz(user=Depends(get_current_user)):
    uid = user["id"]
    last = get_last_weekly_quiz(uid)
    if last:
        last_date = datetime.fromisoformat(last["created_at"])
        if last_date.tzinfo is None:
            last_date = last_date.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) - last_date < timedelta(days=7):
            return {
                "message": "Your weekly quiz has already been generated.",
                "available_after": (last_date + timedelta(days=7)).isoformat(timespec="seconds")
            }

    weak = get_weak_concepts(uid)
    if not weak:
        raise HTTPException(
            status_code=400,
            detail="Complete a quiz first so we can identify concepts to practise."
        )

    concepts = [item["concept"] for item in weak[:5]]
    request = GenerateRequest(
        content="Create a practice quiz focusing on these concepts the learner needs to improve: " + ", ".join(concepts),
        no_of_questions=10,
        level="medium"
    )
    generated = await create_quiz_for_user(request, uid)
    save_weekly_quiz(uid, generated["session_id"])
    return {
        "message": "Weekly practice quiz generated successfully.",
        "weak_concepts": concepts,
        **generated
    }
