from __future__ import annotations

import asyncio
import re
from typing import Final

import httpx

WEEK_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"<span[^>]*id=['\"]info33['\"][^>]*>\s*<b>(\d+)</b>\s*учебная\s+неделя",
    re.IGNORECASE,
)


async def fetch_current_week(url: str, *, timeout: float = 15.0) -> int:
    """Return the current academic week number from the specified URL."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)
        response.raise_for_status()

    match = WEEK_PATTERN.search(response.text)
    if not match:
        raise ValueError("Не удалось определить номер учебной недели на сайте БГАУ.")

    return int(match.group(1))


def fetch_current_week_sync(url: str, *, timeout: float = 15.0) -> int:
    """Synchronous wrapper around :func:`fetch_current_week`."""
    return asyncio.run(fetch_current_week(url, timeout=timeout))


__all__ = ["fetch_current_week", "fetch_current_week_sync"]
