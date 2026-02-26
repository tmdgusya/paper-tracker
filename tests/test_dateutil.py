"""Tests for the dateutil module."""

import datetime
from unittest.mock import MagicMock, patch

from paper_tracker.dateutil import get_current_date, get_current_datetime, _MAX_SKEW


class TestGetCurrentDate:
    """Test cases for get_current_date()."""

    @patch("paper_tracker.dateutil.httpx.head")
    def test_returns_server_date_when_clock_ahead(self, mock_head: MagicMock) -> None:
        """When local clock is far in the future, use server date."""
        server_time = "Tue, 22 Jul 2025 12:00:00 GMT"
        mock_resp = MagicMock()
        mock_resp.headers = {"date": server_time}
        mock_head.return_value = mock_resp

        # Simulate a local clock set to 2026
        fake_local = datetime.datetime(2026, 2, 26, 12, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("paper_tracker.dateutil.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fake_local
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = get_current_date()

        assert result == datetime.date(2025, 7, 22)

    @patch("paper_tracker.dateutil.httpx.head")
    def test_returns_local_date_when_clock_ok(self, mock_head: MagicMock) -> None:
        """When local clock is reasonable, use local date."""
        server_time = "Tue, 22 Jul 2025 12:00:00 GMT"
        mock_resp = MagicMock()
        mock_resp.headers = {"date": server_time}
        mock_head.return_value = mock_resp

        fake_local = datetime.datetime(2025, 7, 22, 14, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("paper_tracker.dateutil.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fake_local
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = get_current_date()

        assert result == datetime.date(2025, 7, 22)

    @patch("paper_tracker.dateutil.httpx.head", side_effect=Exception("network error"))
    def test_falls_back_to_local_on_network_error(self, mock_head: MagicMock) -> None:
        """On network failure, fall back to local clock."""
        result = get_current_date()
        # Should not raise; returns some date
        assert isinstance(result, datetime.date)

    @patch("paper_tracker.dateutil.httpx.head")
    def test_falls_back_when_no_date_header(self, mock_head: MagicMock) -> None:
        """When server response has no Date header, fall back to local clock."""
        mock_resp = MagicMock()
        mock_resp.headers = {}
        mock_head.return_value = mock_resp

        result = get_current_date()
        assert isinstance(result, datetime.date)


class TestGetCurrentDatetime:
    """Test cases for get_current_datetime()."""

    @patch("paper_tracker.dateutil.httpx.head")
    def test_returns_server_datetime_when_clock_ahead(self, mock_head: MagicMock) -> None:
        """When local clock is far in the future, use server datetime."""
        server_time = "Tue, 22 Jul 2025 12:00:00 GMT"
        mock_resp = MagicMock()
        mock_resp.headers = {"date": server_time}
        mock_head.return_value = mock_resp

        fake_local = datetime.datetime(2026, 2, 26, 12, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("paper_tracker.dateutil.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fake_local
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = get_current_datetime()

        assert isinstance(result, datetime.datetime)
        assert result.year == 2025
        assert result.month == 7
        assert result.day == 22

    @patch("paper_tracker.dateutil.httpx.head")
    def test_returns_utc_aware_datetime(self, mock_head: MagicMock) -> None:
        """Returned datetime should be timezone-aware (UTC)."""
        server_time = "Tue, 22 Jul 2025 12:00:00 GMT"
        mock_resp = MagicMock()
        mock_resp.headers = {"date": server_time}
        mock_head.return_value = mock_resp

        fake_local = datetime.datetime(2025, 7, 22, 14, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("paper_tracker.dateutil.datetime") as mock_dt:
            mock_dt.datetime.now.return_value = fake_local
            mock_dt.timezone = datetime.timezone
            mock_dt.timedelta = datetime.timedelta
            result = get_current_datetime()

        assert result.tzinfo is not None
