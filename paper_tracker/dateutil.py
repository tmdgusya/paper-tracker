"""Date utilities with clock-skew detection."""

import datetime
import email.utils

import httpx

# Maximum allowed clock skew before we distrust the local clock (48 hours).
_MAX_SKEW = datetime.timedelta(hours=48)

# Lightweight HEAD target – arXiv main page is small and always available.
_TIME_CHECK_URL = "https://arxiv.org/"


def _get_server_time() -> datetime.datetime | None:
    """Fetch current time from an HTTP server's Date header.

    Returns:
        Server datetime in UTC, or None on any failure.
    """
    try:
        resp = httpx.head(_TIME_CHECK_URL, timeout=5, follow_redirects=True)
        date_header = resp.headers.get("date")
        if date_header:
            parsed = email.utils.parsedate_to_datetime(date_header)
            return parsed.astimezone(datetime.timezone.utc)
    except Exception:
        pass
    return None


def _resolve_time() -> datetime.datetime:
    """Return the best-effort current UTC datetime, correcting for clock skew.

    Compares the local clock with a server time source.  If the local clock
    is more than 48 hours ahead, the server time is returned instead.
    Falls back to the local clock on any network error.
    """
    local_now = datetime.datetime.now(tz=datetime.timezone.utc)
    server_now = _get_server_time()

    if server_now is not None:
        skew = local_now - server_now
        if skew > _MAX_SKEW:
            return server_now

    return local_now


def get_current_date() -> datetime.date:
    """Return today's date, correcting for system clock skew if detected.

    Sends a lightweight HEAD request to arXiv and compares the ``Date``
    response header with the local clock.  If the local clock is more than
    48 hours ahead of the server, the server date is used instead.

    Falls back to the local clock on any network error.
    """
    return _resolve_time().date()


def get_current_datetime() -> datetime.datetime:
    """Return the current UTC datetime, correcting for system clock skew.

    Same logic as :func:`get_current_date` but returns a full
    :class:`datetime.datetime` (timezone-aware, UTC).
    """
    return _resolve_time()
