import json
import re
from typing import Any, Dict, List, Set
from settings import Quiz, Question

class QuizValidationError(Exception):
    """Raised when an AI-generated quiz fails validation."""
    pass

def extract_json_payload(raw_text: str) -> str:
    """Extracts the JSON payload from raw LLM output, handling markdown fences or preamble."""
    if not raw_text or not raw_text.strip():
        raise QuizValidationError("Empty response received from AI provider")

    text = raw_text.strip()

    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        text = match.group(1).strip()

    # Extract substring between first '{' and last '}'
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace >= first_brace:
        text = text[first_brace:last_brace + 1]

    return text

def validate_quiz_response(raw_input: Any, requested_count: int) -> Quiz:
    """
    Validates that the AI response matches Quizwise requirements:
    1. Correct JSON structure.
    2. Requested number of questions.
    3. Required question fields.
    4. Valid answer options (no duplicates, at least 2 for mcq/multiple_answer).
    5. Correct answer references (answers must exist in options).
    6. Unique question IDs.
    7. Compatibility with existing Quizwise schema.

    Returns the validated Quiz object or raises QuizValidationError.
    """
    if isinstance(raw_input, dict):
        data = raw_input
    elif isinstance(raw_input, str):
        cleaned = extract_json_payload(raw_input)
        try:
            data = json.loads(cleaned)
        except Exception as err:
            raise QuizValidationError(f"Invalid JSON syntax: {err}") from err
    else:
        raise QuizValidationError(f"Expected dict or JSON string, got {type(raw_input).__name__}")

    if not isinstance(data, dict):
        raise QuizValidationError("Root JSON value must be an object/dict")

    # 1. Topic validation
    topic = data.get("topic")
    if not isinstance(topic, str) or not topic.strip():
        raise QuizValidationError("Missing or empty 'topic' string")

    # 2. Questions list and requested count
    questions = data.get("questions")
    if not isinstance(questions, list):
        raise QuizValidationError("Missing or non-list 'questions' field")

    if len(questions) != requested_count:
        raise QuizValidationError(
            f"Question count mismatch: requested {requested_count}, received {len(questions)}"
        )

    valid_types = {"mcq", "multiple_answer", "code", "theory"}
    valid_difficulties = {"easy", "medium", "hard"}
    seen_ids: Set[str] = set()

    # 3. Individual question validation
    for idx, q in enumerate(questions, start=1):
        if not isinstance(q, dict):
            raise QuizValidationError(f"Question #{idx} must be a dictionary")

        # 3a. Unique question ID validation
        q_id = q.get("id")
        if not q_id or not isinstance(q_id, (str, int)):
            raise QuizValidationError(f"Question #{idx} is missing a required 'id'")
        str_id = str(q_id).strip()
        if not str_id:
            raise QuizValidationError(f"Question #{idx} has an empty 'id'")
        if str_id in seen_ids:
            raise QuizValidationError(f"Duplicate question ID '{str_id}' detected at question #{idx}")
        seen_ids.add(str_id)
        q["id"] = str_id

        # 3b. Required question fields
        q_text = q.get("question")
        if not isinstance(q_text, str) or not q_text.strip():
            raise QuizValidationError(f"Question #{idx} ('{str_id}') missing required 'question' text")

        concept = q.get("concept")
        if not isinstance(concept, str) or not concept.strip():
            raise QuizValidationError(f"Question #{idx} ('{str_id}') missing required 'concept'")

        q_type = q.get("type")
        if q_type not in valid_types:
            raise QuizValidationError(
                f"Question #{idx} ('{str_id}') has invalid type '{q_type}'. Allowed: {sorted(valid_types)}"
            )

        difficulty = q.get("difficulty")
        if difficulty not in valid_difficulties:
            raise QuizValidationError(
                f"Question #{idx} ('{str_id}') has invalid difficulty '{difficulty}'. Allowed: {sorted(valid_difficulties)}"
            )

        description = q.get("description")
        if not isinstance(description, str) or not description.strip():
            raise QuizValidationError(f"Question #{idx} ('{str_id}') missing required 'description'")

        answer = q.get("answer")
        if not isinstance(answer, list) or len(answer) == 0:
            raise QuizValidationError(f"Question #{idx} ('{str_id}') must have a non-empty 'answer' list")
        if any(not isinstance(a, str) or not a.strip() for a in answer):
            raise QuizValidationError(f"Question #{idx} ('{str_id}') contains invalid or empty answer values")

        # 3c. Options & Answer References validation
        options = q.get("options")
        if q_type in ("mcq", "multiple_answer"):
            if not isinstance(options, list) or len(options) < 2:
                raise QuizValidationError(
                    f"Question #{idx} ('{str_id}') of type '{q_type}' must have at least 2 options"
                )

            # Check for empty options and duplicates
            opt_set: Set[str] = set()
            for opt in options:
                if not isinstance(opt, str) or not opt.strip():
                    raise QuizValidationError(f"Question #{idx} ('{str_id}') contains empty option string")
                norm_opt = opt.strip().casefold()
                if norm_opt in opt_set:
                    raise QuizValidationError(
                        f"Question #{idx} ('{str_id}') contains duplicate options: '{opt}'"
                    )
                opt_set.add(norm_opt)

            # Validate that every answer maps to an existing option
            for ans in answer:
                norm_ans = ans.strip().casefold()
                if norm_ans not in opt_set:
                    raise QuizValidationError(
                        f"Question #{idx} ('{str_id}') answer '{ans}' does not match any listed option"
                    )

            if q_type == "mcq" and len(answer) != 1:
                raise QuizValidationError(
                    f"Question #{idx} ('{str_id}') is 'mcq' but contains {len(answer)} answers (expected 1)"
                )
        else:
            # For code and theory types
            if options is not None and not isinstance(options, list):
                q["options"] = None

    # 4. Pydantic schema validation
    try:
        return Quiz.model_validate(data)
    except Exception as exc:
        raise QuizValidationError(f"Schema compatibility error: {exc}") from exc

