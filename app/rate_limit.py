from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class InMemoryRateLimiter:
    def __init__(
        self,
        *,
        window_seconds: int = 60,
        max_requests_per_window: int = 6,
        min_interval_seconds: float = 2.0,
        max_question_length: int = 4000,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_requests_per_window = max_requests_per_window
        self.min_interval_seconds = min_interval_seconds
        self.max_question_length = max_question_length

        self._history: dict[int, deque[float]] = defaultdict(deque)
        self._last_seen: dict[int, float] = {}
        self._in_flight: set[int] = set()
        self._lock = asyncio.Lock()

    async def acquire(self, user_key: int, question: str) -> tuple[bool, str | None]:
        now = time.monotonic()
        if len(question) > self.max_question_length:
            return (
                False,
                f"Слишком длинный вопрос. Максимум {self.max_question_length} символов.",
            )

        async with self._lock:
            if user_key in self._in_flight:
                return (
                    False,
                    "У Вас уже есть запрос в обработке. Дождитесь ответа и отправьте следующий вопрос.",
                )

            last_seen = self._last_seen.get(user_key, 0.0)
            min_interval_left = self.min_interval_seconds - (now - last_seen)
            if min_interval_left > 0:
                wait_seconds = max(1, int(min_interval_left) + 1)
                return (
                    False,
                    f"Слишком часто. Повторите через {wait_seconds} сек.",
                )

            history = self._history[user_key]
            cutoff = now - self.window_seconds
            while history and history[0] < cutoff:
                history.popleft()

            if len(history) >= self.max_requests_per_window:
                retry_after = max(1, int(self.window_seconds - (now - history[0])) + 1)
                return (
                    False,
                    f"Лимит запросов исчерпан. Повторите через {retry_after} сек.",
                )

            history.append(now)
            self._last_seen[user_key] = now
            self._in_flight.add(user_key)

        return True, None

    async def release(self, user_key: int) -> None:
        async with self._lock:
            self._in_flight.discard(user_key)

