import time
import pytest
from circuit_breaker import ProviderCircuitBreaker

def test_circuit_breaker_initial_state():
    cb = ProviderCircuitBreaker(failure_threshold=3, cooldown_seconds=10.0)
    assert cb.is_available("gemini") is True
    status = cb.get_status()
    assert status == {}

def test_circuit_breaker_consecutive_failures_trips_open():
    cb = ProviderCircuitBreaker(failure_threshold=3, cooldown_seconds=5.0)

    # 1st failure
    cb.record_failure("groq", status_code=500, error_msg="Server Error")
    assert cb.is_available("groq") is True

    # 2nd failure
    cb.record_failure("groq", status_code=502, error_msg="Bad Gateway")
    assert cb.is_available("groq") is True

    # 3rd failure (hits threshold)
    cb.record_failure("groq", status_code=503, error_msg="Service Unavailable")
    assert cb.is_available("groq") is False

    status = cb.get_status()
    assert status["groq"]["state"] == "OPEN"
    assert status["groq"]["consecutive_failures"] == 3
    assert status["groq"]["cooldown_remaining_sec"] > 0

def test_circuit_breaker_429_trips_immediately():
    cb = ProviderCircuitBreaker(failure_threshold=5, cooldown_seconds=10.0)

    # 1 single 429 rate limit
    cb.record_failure("openrouter", status_code=429, error_msg="Rate limit exceeded")
    assert cb.is_available("openrouter") is False

    status = cb.get_status()
    assert status["openrouter"]["state"] == "OPEN"
    assert status["openrouter"]["cooldown_remaining_sec"] > 0

def test_circuit_breaker_cooldown_to_half_open_and_recovery():
    # Cooldown duration 0.1s for fast testing
    cb = ProviderCircuitBreaker(failure_threshold=2, cooldown_seconds=0.1)

    cb.record_failure("gemini", status_code=500)
    cb.record_failure("gemini", status_code=500)
    assert cb.is_available("gemini") is False

    # Wait for cooldown to expire
    time.sleep(0.15)

    # Calling is_available transitions from OPEN to HALF_OPEN
    assert cb.is_available("gemini") is True
    status = cb.get_status()
    assert status["gemini"]["state"] == "HALF_OPEN"

    # Successful response closes circuit
    cb.record_success("gemini", latency=0.45)
    assert cb.is_available("gemini") is True
    status = cb.get_status()
    assert status["gemini"]["state"] == "CLOSED"
    assert status["gemini"]["consecutive_failures"] == 0
    assert status["gemini"]["wins"] == 1
    assert status["gemini"]["avg_latency_sec"] == 0.45

