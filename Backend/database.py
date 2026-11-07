from datetime import datetime, timezone
from hashlib import sha256
from firebase_service import db

def _user(uid):
    return db.collection("users").document(str(uid))

def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def init_db():
    pass

def create_user(user_id, email, name=None):
    _user(user_id).set({"uid": user_id, "email": (email or "").lower().strip(),
                        "name": name, "created_at": _now()}, merge=True)
    return user_id

def find_user_by_id(user_id):
    snap = _user(user_id).get()
    return snap.to_dict() if snap.exists else None

def create_quiz_session(session_id, user_id, date, quiz, metadata=None):
    doc_data = {
        "session_id": session_id, "user_id": str(user_id), "date": date,
        "quiz": quiz, "submitted": False
    }
    if metadata:
        doc_data["metadata"] = metadata
    _user(user_id).collection("quiz_sessions").document(session_id).set(doc_data)

def get_quiz_session(session_id, user_id):
    snap = _user(user_id).collection("quiz_sessions").document(session_id).get()
    return snap.to_dict() if snap.exists else None

def mark_quiz_session_submitted(session_id, user_id):
    ref = _user(user_id).collection("quiz_sessions").document(session_id)
    snap = ref.get()
    if not snap.exists or snap.to_dict().get("submitted"):
        return False
    ref.update({"submitted": True})
    return True

def save_quiz(user_id, date, quiz, results, score, metadata=None):
    ref = _user(user_id).collection("quiz_history").document()
    doc_data = {
        "date": date, "quiz": quiz, "results": results, "score": score,
        "created_at": _now()
    }
    if metadata:
        doc_data["metadata"] = metadata
    ref.set(doc_data)
    return ref.id

def get_all_history(user_id):
    docs = _user(user_id).collection("quiz_history").order_by(
        "created_at", direction="DESCENDING").stream()
    result = []
    for doc in docs:
        item = doc.to_dict()
        item["id"] = doc.id
        result.append(item)
    return result

def get_history_by_id(history_id, user_id):
    snap = _user(user_id).collection("quiz_history").document(str(history_id)).get()
    if not snap.exists:
        return None
    item = snap.to_dict()
    item["id"] = snap.id
    return item

def record_concept_result(user_id, concept, is_correct):
    concept = (concept or "General").strip() or "General"
    ref = _user(user_id).collection("weak_concepts").document(
        sha256(concept.encode("utf-8")).hexdigest())
    snap = ref.get()
    old = snap.to_dict() if snap.exists else {}
    correct = int(old.get("correct_count", 0)) + int(bool(is_correct))
    wrong = int(old.get("wrong_count", 0)) + int(not bool(is_correct))
    ref.set({"concept": concept, "correct_count": correct,
             "wrong_count": wrong, "last_attempt": _now()})

def get_weak_concepts(user_id):
    items = [d.to_dict() for d in _user(user_id).collection("weak_concepts").stream()]
    items = [x for x in items if int(x.get("wrong_count", 0)) > 0]
    items.sort(key=lambda x: (int(x.get("wrong_count", 0)) /
        max(int(x.get("correct_count", 0)) + int(x.get("wrong_count", 0)), 1),
        int(x.get("wrong_count", 0))), reverse=True)
    return items

def get_last_weekly_quiz(user_id):
    docs = _user(user_id).collection("weekly_quizzes").order_by(
        "created_at", direction="DESCENDING").limit(1).stream()
    for doc in docs:
        return doc.to_dict()
    return None

def save_weekly_quiz(user_id, session_id):
    _user(user_id).collection("weekly_quizzes").document().set({
        "session_id": session_id, "created_at": _now()})
