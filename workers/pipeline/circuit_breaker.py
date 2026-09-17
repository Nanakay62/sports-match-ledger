"""Domain Circuit Breaker.

Provides host-level fault tolerance for feed poller and scrapers.
Trips OPEN on consecutive failures to protect upstream outlets and avoid wasting pipeline cycles.
Operates strictly at inference rung L0 (deterministic).
"""

import time
from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import urlparse


class CircuitState(StrEnum):
    CLOSED = "CLOSED"  # Normal operation, requests allowed
    OPEN = "OPEN"  # Failing, requests blocked until cooldown expires
    HALF_OPEN = "HALF_OPEN"  # Cooldown expired, testing recovery with single probe


@dataclass
class DomainEntry:
    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    opened_at: float = 0.0


class DomainCircuitBreaker:
    """In-memory domain circuit breaker tracking failure states per host."""

    def __init__(self, failure_threshold: int = 5, cooldown_seconds: float = 300.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._domains: dict[str, DomainEntry] = {}

    @staticmethod
    def extract_domain(url_or_domain: str) -> str:
        """Extracts normalized hostname from a URL or domain string."""
        if "://" in url_or_domain:
            parsed = urlparse(url_or_domain)
            host = parsed.hostname or parsed.netloc
            return host.lower().strip()
        return url_or_domain.split("/")[0].lower().strip()

    def _get_entry(self, domain: str) -> DomainEntry:
        if domain not in self._domains:
            self._domains[domain] = DomainEntry()
        return self._domains[domain]

    def can_request(self, url_or_domain: str) -> bool:
        """Determines if a request to this domain is permitted.

        Returns True if CLOSED or if OPEN cooldown has elapsed (transitioning to HALF_OPEN).
        Returns False if OPEN and cooldown has not elapsed.
        """
        domain = self.extract_domain(url_or_domain)
        entry = self._get_entry(domain)

        if entry.state == CircuitState.CLOSED:
            return True

        now = time.time()
        if entry.state == CircuitState.OPEN:
            if now - entry.opened_at >= self.cooldown_seconds:
                entry.state = CircuitState.HALF_OPEN
                return True
            return False

        if entry.state == CircuitState.HALF_OPEN:
            return True

        return True

    def record_success(self, url_or_domain: str) -> None:
        """Records a successful request, resetting failures and closing the circuit."""
        domain = self.extract_domain(url_or_domain)
        entry = self._get_entry(domain)
        entry.state = CircuitState.CLOSED
        entry.failures = 0
        entry.opened_at = 0.0

    def record_failure(self, url_or_domain: str) -> None:
        """Records a request failure, potentially tripping the circuit OPEN."""
        domain = self.extract_domain(url_or_domain)
        entry = self._get_entry(domain)

        if entry.state == CircuitState.HALF_OPEN:
            # Probe failed, trip immediately back to OPEN with fresh cooldown
            entry.state = CircuitState.OPEN
            entry.opened_at = time.time()
            return

        entry.failures += 1

        if entry.failures >= self.failure_threshold:
            entry.state = CircuitState.OPEN
            entry.opened_at = time.time()

    def get_state(self, url_or_domain: str) -> CircuitState:
        """Returns the current circuit state for a domain, evaluating cooldown expiration."""
        domain = self.extract_domain(url_or_domain)
        entry = self._get_entry(domain)
        if entry.state == CircuitState.OPEN:
            now = time.time()
            if now - entry.opened_at >= self.cooldown_seconds:
                entry.state = CircuitState.HALF_OPEN
                return CircuitState.HALF_OPEN
        return entry.state

    def reset(self, url_or_domain: str | None = None) -> None:
        """Resets the circuit breaker state for a specific domain or all domains."""
        if url_or_domain is not None:
            domain = self.extract_domain(url_or_domain)
            self._domains.pop(domain, None)
        else:
            self._domains.clear()


# Default singleton instance for workers
default_circuit_breaker = DomainCircuitBreaker()
