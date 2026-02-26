"""Date utilities with clock-skew detection."""

import datetime
import email.utils

import httpx

# Maximum allowed clock skew before we distrust the local clock (48 hours).
_MAX_SKEW = datetime.timedelta(hours=48)

# Lightweight HEAD target – arXiv main page is small and always available.
_TIME_CHECK_URL = "https://arxiv.org/"


def get_current_date() -> datetime.date:
    """Return today's date, correcting for system clock skew if detected.

    Sends a lightweight HEAD request to arXiv and compares the ``Date``
    response header with the local clock.  If the local clock is more than
    48 hours ahead of the server, the server date is used instead.

    Falls back to the local clock on any network error.
    """
    local_now = datetime.datetime.now(tz=datetime.timezone.utc)

    try:
        resp = httpx.head(_TIME_CHECK_URL, timeout=5, follow_redirects=True)
        date_header = resp.headers.get("date")
        if date_header:
            parsed = email.utils.parsedate_to_datetime(date_header)
            server_now = parsed.astimezone(datetime.timezone.utc)
            skew = local_now - server_now
            if skew > _MAX_SKEW:
                # Local clock is in the future – use server time.
                return server_now.date()
    except Exception:
        pass

    return local_now.date()
