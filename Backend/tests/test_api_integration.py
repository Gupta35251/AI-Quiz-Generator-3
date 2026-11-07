import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from settings import Quiz, Question
from ai_service import ProviderResult
import database
from api import app
from firebase_auth import verify_firebase_token

client = TestClient(app)

SAMPLE_GENERATED_QUIZ = Quiz(
    topic="Python Data Structures",
    questions=[
        Question(
            id="q1",
            question="Which type is immutable?",
            concept="Mutability",
            type="mcq",
            options=["list", "tuple", "dict", "set"],
            answer=["tuple"],
            description="Tuples cannot be changed once created.",
            difficulty="easy"
        ),
        Question(
            id="q2",
            question="Which types are key-value mappings?",
            concept="Dictionaries",
            type="multiple_answer",
            options=["dict", "defaultdict", "list", "tuple"],
            answer=["dict", "defaultdict"],
            description="dict and defaultdict store keys and values.",
            difficulty="medium"
        )
    ]
)

@pytest.fixture(autouse=True)
def override_auth_and_db(monkeypatch):
    app.dependency_overrides[verify_firebase_token] = lambda: {
        "uid": "test_user_123",
        "email": "tester@quizwise.com",
        "name": "Tester"
    }

    sessions_db = {}
    history_db = []
    weak_db = {}

    def mock_create_user(uid, email, name=None):
        return uid

    def mock_create_quiz_session(session_id, user_id, date, quiz, metadata=None):
        sessions_db[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "date": date,
            "quiz": quiz,
            "metadata": metadata,
            "submitted": False
        }

    def mock_get_quiz_session(session_id, user_id):
        return sessions_db.get(session_id)

    def mock_mark_quiz_session_submitted(session_id, user_id):
        sess = sessions_db.get(session_id)
        if not sess or sess.get("submitted"):
            return False
        sess["submitted"] = True
        return True

    def mock_save_quiz(user_id, date, quiz, results, score, metadata=None):
        entry_id = f"hist_{len(history_db) + 1}"
        history_db.append({
            "id": entry_id,
            "user_id": user_id,
            "date": date,
            "quiz": quiz,
            "results": results,
            "score": score,
            "metadata": metadata
        })
        return entry_id

    def mock_record_concept_result(user_id, concept, is_correct):
        curr = weak_db.get(concept, {"concept": concept, "correct_count": 0, "wrong_count": 0})
        if is_correct:
            curr["correct_count"] += 1
        else:
            curr["wrong_count"] += 1
        weak_db[concept] = curr

    def mock_get_weak_concepts(user_id):
        return [v for v in weak_db.values() if v["wrong_count"] > 0]

    def mock_get_all_history(user_id):
        return history_db

    def mock_get_history_by_id(hist_id, user_id):
        for h in history_db:
            if h["id"] == hist_id:
                return h
        return None

    def mock_get_last_weekly_quiz(user_id):
        return None

    def mock_save_weekly_quiz(user_id, session_id):
        pass

    monkeypatch.setattr("api.create_user", mock_create_user)
    monkeypatch.setattr("api.create_quiz_session", mock_create_quiz_session)
    monkeypatch.setattr("api.get_quiz_session", mock_get_quiz_session)
    monkeypatch.setattr("api.mark_quiz_session_submitted", mock_mark_quiz_session_submitted)
    monkeypatch.setattr("api.save_quiz", mock_save_quiz)
    monkeypatch.setattr("api.record_concept_result", mock_record_concept_result)
    monkeypatch.setattr("api.get_weak_concepts", mock_get_weak_concepts)
    monkeypatch.setattr("api.get_all_history", mock_get_all_history)
    monkeypatch.setattr("api.get_history_by_id", mock_get_history_by_id)
    monkeypatch.setattr("api.get_last_weekly_quiz", mock_get_last_weekly_quiz)
    monkeypatch.setattr("api.save_weekly_quiz", mock_save_weekly_quiz)

    yield

    app.dependency_overrides.clear()

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}

def test_api_provider_status():
    res = client.get("/api/providers/status", headers={"Authorization": "Bearer fake_token"})
    assert res.status_code == 200
    data = res.json()
    assert "gemini" in data
    assert "groq" in data
    assert "openrouter" in data
    # Ensure no secrets or API keys are leaked in response
    data_str = json.dumps(data)
    assert "api_key" not in data_str.lower()
    assert "secret" not in data_str.lower()

def test_generate_and_submit_quiz_flow():
    mock_result = ProviderResult(
        provider="groq",
        model="llama-3.3-70b-versatile",
        quiz=SAMPLE_GENERATED_QUIZ,
        latency=0.32
    )

    with patch("api.generate_answer_async", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_result

        # 1. Generate Quiz
        payload = {"content": "Python Data Structures", "no_of_questions": 2, "level": "easy"}
        res = client.post("/api/quiz/generate", json=payload, headers={"Authorization": "Bearer fake_token"})
        assert res.status_code == 200
        gen_data = res.json()
        assert "session_id" in gen_data
        session_id = gen_data["session_id"]
        quiz = gen_data["quiz"]
        assert quiz["topic"] == "Python Data Structures"
        assert len(quiz["questions"]) == 2

        # Verify answers are hidden in safe quiz
        assert "answer" not in quiz["questions"][0]
        assert "description" not in quiz["questions"][0]

        # Verify performance metadata is returned
        assert gen_data.get("metadata", {}).get("winning_provider") == "groq"
        assert gen_data.get("metadata", {}).get("model") == "llama-3.3-70b-versatile"

        # 2. Submit Answers
        # Submit correct answers: q1: ["tuple"], q2: ["dict", "defaultdict"]
        sub_payload = {
            "session_id": session_id,
            "answers": [["tuple"], ["dict", "defaultdict"]]
        }
        res_sub = client.post("/api/quiz/submit", json=sub_payload, headers={"Authorization": "Bearer fake_token"})
        assert res_sub.status_code == 200
        sub_data = res_sub.json()
        assert sub_data["score"] == 2
        assert sub_data["total"] == 2
        assert sub_data["results"][0]["is_correct"] is True
        assert sub_data["results"][1]["is_correct"] is True

        # 3. Duplicate submission prevention (HTTP 409)
        res_dup = client.post("/api/quiz/submit", json=sub_payload, headers={"Authorization": "Bearer fake_token"})
        assert res_dup.status_code == 409

        # 4. History check
        hist_res = client.get("/api/history", headers={"Authorization": "Bearer fake_token"})
        assert hist_res.status_code == 200
        items = hist_res.json()["items"]
        assert len(items) == 1
        assert items[0]["score"] == 2
