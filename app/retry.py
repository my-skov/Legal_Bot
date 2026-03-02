from __future__ import annotations

import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


def retry_call(
    fn: Callable[[], T],
    *,
    operation_name: str,
    max_attempts: int = 4,
    base_delay_seconds: float = 1.0,
) -> T:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt >= max_attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1)) + random.uniform(0.0, 0.3)
            logger.warning(
                "%s failed (attempt %s/%s). Retry in %.2fs. Error: %s",
                operation_name,
                attempt,
                max_attempts,
                delay,
                exc,
            )
            time.sleep(delay)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"Unexpected retry state for operation: {operation_name}")

