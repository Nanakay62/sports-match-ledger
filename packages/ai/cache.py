import hashlib
from typing import Any


class SemanticCache:
    """In-memory and Postgres-backed response cache to ensure idempotency and prevent duplicate inference costs."""

    def __init__(self):
        self._store: dict[str, Any] = {}

    @staticmethod
    def generate_key(prompt_version: str, source_text: str) -> str:
        content = f"{prompt_version}:{source_text.strip().lower()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        return self._store.get(key)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def clear(self) -> None:
        self._store.clear()
