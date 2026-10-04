"""Conservative classification of terminal Codex CLI provider failures.

This module only labels failures which the CLI itself reported in an ``error``
or ``turn.failed`` event (or in stderr when no event contains the signal).
It deliberately does not inspect prompts, agent messages, or output content,
and it never retries, changes accounts, or changes models.
"""
from __future__ import annotations

import json
from typing import Any


GLOBAL_PROVIDER_FAILURES = frozenset({
    "MODEL_PROVIDER_QUOTA_EXHAUSTED",
    "MODEL_PROVIDER_AUTH_REQUIRED",
    "MODEL_PROVIDER_RATE_LIMITED",
})


def _decoded_error_value(value: Any) -> Any:
    """Decode a CLI error payload embedded as a JSON string, if it is one."""
    if not isinstance(value, str):
        return value
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError):
        return value
    return decoded if isinstance(decoded, (dict, list)) else value


def _error_details(value: Any) -> tuple[set[int], set[str], list[str]]:
    """Extract status, explicit error code, and messages from one error payload."""
    statuses: set[int] = set()
    codes: set[str] = set()
    messages: list[str] = []

    def visit(item: Any) -> None:
        item = _decoded_error_value(item)
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if not isinstance(item, dict):
            return
        status = item.get("status")
        if isinstance(status, int) and not isinstance(status, bool):
            statuses.add(status)
        for key in ("code", "type"):
            code = item.get(key)
            if isinstance(code, str):
                codes.add(code.casefold())
        message = item.get("message")
        if isinstance(message, str):
            messages.append(message)
            nested = _decoded_error_value(message)
            if nested is not message:
                visit(nested)
        error = item.get("error")
        if isinstance(error, (dict, list, str)):
            visit(error)

    visit(value)
    return statuses, codes, messages


def _provider_failure(statuses: set[int], codes: set[str], messages: list[str]) -> str | None:
    """Recognize only documented, unambiguous provider signals."""
    if any("you've hit your usage limit" in message.casefold().replace("’", "'")
           for message in messages):
        return "MODEL_PROVIDER_QUOTA_EXHAUSTED"
    if 429 in statuses or "rate_limit_exceeded" in codes:
        return "MODEL_PROVIDER_RATE_LIMITED"
    if (401 in statuses or "invalid_api_key" in codes or
            any("login required" in message.casefold() for message in messages)):
        return "MODEL_PROVIDER_AUTH_REQUIRED"
    return None


def _event_failure(events: bytes) -> str | None:
    """Inspect only ``error`` and ``turn.failed`` JSONL records from the CLI."""
    for raw_line in events.splitlines():
        try:
            event = json.loads(raw_line)
        except (UnicodeDecodeError, ValueError):
            continue
        if not isinstance(event, dict) or event.get("type") not in {"error", "turn.failed"}:
            continue
        failure = _provider_failure(*_error_details(event))
        if failure is not None:
            return failure
    return None


def _stderr_failure(stderr: bytes) -> str | None:
    """Use stderr only as a fallback for the same narrow, literal signals."""
    try:
        text = stderr.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None
    normalized = text.casefold().replace("’", "'")
    if "you've hit your usage limit" in normalized:
        return "MODEL_PROVIDER_QUOTA_EXHAUSTED"
    if "rate_limit_exceeded" in normalized:
        return "MODEL_PROVIDER_RATE_LIMITED"
    if "invalid_api_key" in normalized or "login required" in normalized:
        return "MODEL_PROVIDER_AUTH_REQUIRED"
    # A bare numeric 401/429 in arbitrary stderr text is too weak to classify.
    return None


def classify_provider_failure(events: bytes, stderr: bytes, returncode: int | None) -> str | None:
    """Return a global provider failure or a generic process failure.

    A zero exit status is never relabeled from incidental diagnostic text.
    An absent exit status remains unclassified, because it does not establish a
    nonzero process failure.  No action is taken based on the classification.
    """
    if returncode is None or returncode == 0:
        return None
    failure = _event_failure(events) or _stderr_failure(stderr)
    if failure is not None:
        return failure
    if isinstance(returncode, int) and not isinstance(returncode, bool) and returncode != 0:
        return "MODEL_PROCESS_FAILED"
    return None
