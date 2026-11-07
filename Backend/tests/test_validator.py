import json
import pytest
from validator import validate_quiz_response, extract_json_payload, QuizValidationError

def test_extract_json_markdown():
    wrapped = "```json\n{\"topic\": \"Python\", \"questions\": []}\n```"
    cleaned = extract_json_payload(wrapped)
    assert json.loads(cleaned) == {"topic": "Python", "questions": []}

def test_extract_json_preamble():
    text = "Here is your quiz:\n{\"topic\": \"Data\", \"questions\": []}\nEnjoy studying!"
    cleaned = extract_json_payload(text)
    assert json.loads(cleaned) == {"topic": "Data", "questions": []}

def test_valid_quiz_response():
    payload = {
        "topic": "Python Basics",
        "questions": [
            {
                "id": "q1",
                "question": "What is Python?",
                "concept": "Python Intro",
                "type": "mcq",
                "options": ["Snake", "Programming Language", "Car", "Animal"],
                "answer": ["Programming Language"],
                "description": "Python is a high-level programming language.",
                "difficulty": "easy"
            },
            {
                "id": "q2",
                "question": "Which of these are built-in Python sequence types?",
                "concept": "Data Types",
                "type": "multiple_answer",
                "options": ["list", "tuple", "set", "dict"],
                "answer": ["list", "tuple"],
                "description": "Lists and tuples are sequences.",
                "difficulty": "medium"
            },
            {
                "id": "q3",
                "question": "Write a function that returns True.",
                "concept": "Functions",
                "type": "code",
                "options": None,
                "answer": ["def fn(): return True"],
                "description": "Simple python function.",
                "difficulty": "easy"
            }
        ]
    }
    quiz = validate_quiz_response(json.dumps(payload), requested_count=3)
    assert quiz.topic == "Python Basics"
    assert len(quiz.questions) == 3
    assert quiz.questions[0].id == "q1"
    assert quiz.questions[0].type == "mcq"

def test_reject_question_count_mismatch():
    payload = {
        "topic": "Math",
        "questions": [
            {
                "id": "q1",
                "question": "2+2?",
                "concept": "Addition",
                "type": "mcq",
                "options": ["3", "4", "5", "6"],
                "answer": ["4"],
                "description": "2+2=4",
                "difficulty": "easy"
            }
        ]
    }
    with pytest.raises(QuizValidationError, match="Question count mismatch"):
        validate_quiz_response(payload, requested_count=5)

def test_reject_duplicate_question_ids():
    payload = {
        "topic": "Math",
        "questions": [
            {
                "id": "q1",
                "question": "1+1?",
                "concept": "Addition",
                "type": "mcq",
                "options": ["1", "2", "3", "4"],
                "answer": ["2"],
                "description": "1+1=2",
                "difficulty": "easy"
            },
            {
                "id": "q1",
                "question": "2+2?",
                "concept": "Addition",
                "type": "mcq",
                "options": ["3", "4", "5", "6"],
                "answer": ["4"],
                "description": "2+2=4",
                "difficulty": "easy"
            }
        ]
    }
    with pytest.raises(QuizValidationError, match="Duplicate question ID"):
        validate_quiz_response(payload, requested_count=2)

def test_reject_mcq_answer_not_in_options():
    payload = {
        "topic": "Geography",
        "questions": [
            {
                "id": "q1",
                "question": "Capital of France?",
                "concept": "Capitals",
                "type": "mcq",
                "options": ["London", "Berlin", "Madrid", "Rome"],
                "answer": ["Paris"],  # Paris not in options!
                "description": "Paris is the capital of France.",
                "difficulty": "easy"
            }
        ]
    }
    with pytest.raises(QuizValidationError, match="does not match any listed option"):
        validate_quiz_response(payload, requested_count=1)

def test_reject_mcq_multiple_answers():
    payload = {
        "topic": "Science",
        "questions": [
            {
                "id": "q1",
                "question": "Which is water?",
                "concept": "Chemistry",
                "type": "mcq",
                "options": ["H2O", "CO2", "NaCl", "O2"],
                "answer": ["H2O", "CO2"],  # mcq must have exactly 1
                "description": "H2O is water",
                "difficulty": "easy"
            }
        ]
    }
    with pytest.raises(QuizValidationError, match="contains 2 answers \\(expected 1\\)"):
        validate_quiz_response(payload, requested_count=1)

def test_reject_duplicate_options():
    payload = {
        "topic": "Trivia",
        "questions": [
            {
                "id": "q1",
                "question": "Pick A",
                "concept": "Alphabet",
                "type": "mcq",
                "options": ["Option 1", "Option 1", "Option 2", "Option 3"],
                "answer": ["Option 1"],
                "description": "Duplicate options",
                "difficulty": "easy"
            }
        ]
    }
    with pytest.raises(QuizValidationError, match="duplicate options"):
        validate_quiz_response(payload, requested_count=1)

def test_reject_invalid_type():
    payload = {
        "topic": "Trivia",
        "questions": [
            {
                "id": "q1",
                "question": "What?",
                "concept": "General",
                "type": "true_false",  # Invalid type
                "options": ["True", "False"],
                "answer": ["True"],
                "description": "desc",
                "difficulty": "easy"
            }
        ]
    }
    with pytest.raises(QuizValidationError, match="invalid type"):
        validate_quiz_response(payload, requested_count=1)

