import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 3600
_MAX_REQUESTS = 5

_lock = Lock()
_request_log = defaultdict(list)


def reset_rate_limiter():
    # Test-only helper. Clears all in-memory rate limit state (across every
    # scope) so automated tests don't interfere with each other. Never
    # called from any production code path or endpoint.
    with _lock:
        _request_log.clear()


def _get_client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def _enforce(scope: str, request: Request):
    # Simple in-memory sliding-window limiter, scoped to a single process
    # AND to a named endpoint (scope), so /challenge and /reasoning-intake
    # each get their own independent 5-per-hour budget. Appropriate for the
    # current single-instance Render deployment - not designed to survive
    # multiple server instances or restarts.
    ip = _get_client_ip(request)
    key = scope + ":" + ip
    now = time.time()

    with _lock:
        timestamps = _request_log[key]
        cutoff = now - _WINDOW_SECONDS
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= _MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Rate limit exceeded: maximum "
                    + str(_MAX_REQUESTS)
                    + " requests per IP per hour for this endpoint. "
                    "Please try again later."
                ),
            )

        timestamps.append(now)


def enforce_challenge_rate_limit(request: Request):
    _enforce("challenge", request)


def enforce_intake_rate_limit(request: Request):
    _enforce("reasoning_intake", request)