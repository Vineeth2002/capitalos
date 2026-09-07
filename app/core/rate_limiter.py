import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request

_WINDOW_SECONDS = 3600
_MAX_REQUESTS = 5

_lock = Lock()
_request_log = defaultdict(list)


def reset_rate_limiter():
    # Test-only helper. Clears all in-memory rate limit state so automated
    # tests don't interfere with each other. Never called from any
    # production code path or endpoint.
    with _lock:
        _request_log.clear()


def _get_client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def enforce_challenge_rate_limit(request: Request):
    # Simple in-memory sliding-window limiter, scoped to a single process.
    # Appropriate for the current single-instance Render deployment. Not
    # designed to survive multiple server instances or restarts - if the
    # app ever scales beyond one instance, this needs to move to a shared
    # store, but that is out of scope for the current validation stage.
    ip = _get_client_ip(request)
    now = time.time()

    with _lock:
        timestamps = _request_log[ip]
        cutoff = now - _WINDOW_SECONDS
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= _MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail=(
                    "Rate limit exceeded: maximum "
                    + str(_MAX_REQUESTS)
                    + " challenge requests per IP per hour. "
                    "Please try again later."
                ),
            )

        timestamps.append(now)