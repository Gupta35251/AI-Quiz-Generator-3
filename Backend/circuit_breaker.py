import time
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger("quizwise.circuit_breaker")

class ProviderCircuitBreaker:
    """
    Manages the health, cooldown, and failure tracking for AI providers.
    - Tracks consecutive failures and trips circuit to OPEN after threshold.
    - Immediately trips circuit to OPEN on HTTP 429 rate limit or quota errors.
    - Automatically allows a probe request after cooldown duration expires (HALF_OPEN).
    - Records success and performance statistics.
    """
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self._states: Dict[str, str] = {}                 # "CLOSED", "OPEN", "HALF_OPEN"
        self._consecutive_failures: Dict[str, int] = {}
        self._cooldown_until: Dict[str, float] = {}
        self._win_counts: Dict[str, int] = {}
        self._total_requests: Dict[str, int] = {}
        self._total_latencies: Dict[str, float] = {}

    def is_available(self, provider_name: str) -> bool:
        """Determines whether requests can be sent to this provider."""
        state = self._states.get(provider_name, "CLOSED")
        now = time.monotonic()

        if state == "OPEN":
            cooldown_time = self._cooldown_until.get(provider_name, 0.0)
            if now < cooldown_time:
                remaining = max(0, int(cooldown_time - now))
                logger.debug(f"Provider '{provider_name}' in cooldown ({remaining}s remaining)")
                return False

            # Cooldown duration elapsed, enter HALF_OPEN state to test recovery
            self._states[provider_name] = "HALF_OPEN"
            logger.info(f"Provider '{provider_name}' cooldown expired. State set to HALF_OPEN (probing).")
            return True

        return True

    def record_success(self, provider_name: str, latency: float):
        """Records a successful quiz generation."""
        self._states[provider_name] = "CLOSED"
        self._consecutive_failures[provider_name] = 0
        self._cooldown_until[provider_name] = 0.0

        self._win_counts[provider_name] = self._win_counts.get(provider_name, 0) + 1
        self._total_requests[provider_name] = self._total_requests.get(provider_name, 0) + 1
        self._total_latencies[provider_name] = self._total_latencies.get(provider_name, 0.0) + latency

    def record_failure(
        self,
        provider_name: str,
        status_code: Optional[int] = None,
        error_msg: Optional[str] = None
    ):
        """Records a provider failure, tripping the circuit if threshold or 429 is reached."""
        self._total_requests[provider_name] = self._total_requests.get(provider_name, 0) + 1
        fails = self._consecutive_failures.get(provider_name, 0) + 1
        self._consecutive_failures[provider_name] = fails

        is_quota = status_code in (429, 402, 403)
        if is_quota or fails >= self.failure_threshold:
            self._states[provider_name] = "OPEN"
            self._cooldown_until[provider_name] = time.monotonic() + self.cooldown_seconds
            reason = f"rate limit / quota error ({status_code})" if is_quota else f"{fails} consecutive failures"
            logger.warning(
                f"[CIRCUIT OPENED] Provider '{provider_name}' circuit opened due to {reason}. "
                f"Cooldown active for {self.cooldown_seconds}s."
            )
        else:
            logger.warning(
                f"Provider '{provider_name}' failure count: {fails}/{self.failure_threshold} "
                f"(status={status_code}): {error_msg}"
            )

    def get_status(self) -> Dict[str, Any]:
        """Returns health and performance metrics for all tracked providers."""
        all_providers = set(
            list(self._states.keys()) +
            list(self._total_requests.keys())
        )
        now = time.monotonic()
        report = {}
        for p in all_providers:
            wins = self._win_counts.get(p, 0)
            tot_lat = self._total_latencies.get(p, 0.0)
            state = self._states.get(p, "CLOSED")
            cooldown_rem = max(0, int(self._cooldown_until.get(p, 0.0) - now))
            report[p] = {
                "state": state,
                "consecutive_failures": self._consecutive_failures.get(p, 0),
                "total_requests": self._total_requests.get(p, 0),
                "wins": wins,
                "avg_latency_sec": round(tot_lat / wins, 3) if wins > 0 else 0.0,
                "cooldown_remaining_sec": cooldown_rem if state == "OPEN" else 0
            }
        return report

