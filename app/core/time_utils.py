from datetime import datetime, timezone
from typing import Optional


def to_naive_utc(value: Optional[datetime]) -> Optional[datetime]:
    """
    Canonical normalization for datetimes stored in TIMESTAMP WITHOUT TIME
    ZONE columns.

    - None stays None.
    - An aware datetime is converted to UTC and its tzinfo is removed.
    - A naive datetime is taken as already UTC.

    The result never depends on the server's or database session's local
    time zone.
    """
    if value is None:
        return None
    if value.tzinfo is not None and value.utcoffset() is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value.replace(tzinfo=None)