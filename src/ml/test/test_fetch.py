#!/usr/bin/env python3
"""
Tests for data/fetch_historical.py.

Unit tests mock HTTP calls so they run offline.
URL and currency validation tests catch real API mismatches.
"""

import csv
import json
import os
import sys
from datetime import date
from unittest.mock import patch, MagicMock
from urllib.parse import urlparse, parse_qs

# Add paths so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data')))

import fetch_historical as fh


def _make_frankfurter_response(from_ccy: str, to_ccy: str, dates_rates: dict[str, float]) -> dict:
    """Build a fake Frankfurter timeseries response."""
    return {
        "amount": 1.0,
        "base": from_ccy,
        "start_date": min(dates_rates.keys()),
        "end_date": max(dates_rates.keys()),
        "rates": {d: {to_ccy: r} for d, r in dates_rates.items()},
    }


# ── Currency validation ─────────────────────────────────────────────────────

class TestCurrencyValidation:
    """Ensure all configured corridors use Frankfurter-supported currencies."""

    def test_all_base_currencies_supported(self):
        for base in fh.CORRIDORS:
            assert base in fh.SUPPORTED_CURRENCIES, (
                f"Base currency '{base}' is not supported by Frankfurter. "
                f"Supported: {sorted(fh.SUPPORTED_CURRENCIES)}"
            )

    def test_all_target_currencies_supported(self):
        for base, targets in fh.CORRIDORS.items():
            for target in targets:
                assert target in fh.SUPPORTED_CURRENCIES, (
                    f"Target currency '{target}' (in {base} corridors) is not supported. "
                    f"Supported: {sorted(fh.SUPPORTED_CURRENCIES)}"
                )

    def test_no_same_currency_pairs(self):
        for base, targets in fh.CORRIDORS.items():
            assert base not in targets, f"{base}/{base} is an invalid self-pair"

    def test_validate_corridors_passes(self):
        """The runtime validation function should not raise."""
        fh.validate_corridors()

    def test_validate_corridors_rejects_bad_currency(self):
        """Should raise ValueError if a corridor uses an unsupported currency."""
        bad_corridors = {"EUR": ["MAD"]}  # MAD is not ECB-tracked
        with patch.object(fh, "CORRIDORS", bad_corridors):
            try:
                fh.validate_corridors()
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "MAD" in str(e)


# ── URL construction ────────────────────────────────────────────────────────

class TestUrlConstruction:
    """Verify URLs match the Frankfurter v1 API spec."""

    def test_url_has_v1_prefix(self):
        url = fh._build_timeseries_url("EUR", "USD", date(2024, 1, 1), date(2024, 12, 31))
        parsed = urlparse(url)
        assert parsed.path.startswith("/v1/"), f"URL path must start with /v1/, got: {parsed.path}"

    def test_url_uses_base_param_not_from(self):
        url = fh._build_timeseries_url("GBP", "INR", date(2024, 1, 1), date(2024, 6, 1))
        params = parse_qs(urlparse(url).query)
        assert "base" in params, f"Expected 'base' param, got: {list(params.keys())}"
        assert params["base"] == ["GBP"]
        assert "from" not in params, "'from' is not a valid Frankfurter param (use 'base')"

    def test_url_uses_symbols_param_not_to(self):
        url = fh._build_timeseries_url("EUR", "USD", date(2024, 1, 1), date(2024, 6, 1))
        params = parse_qs(urlparse(url).query)
        assert "symbols" in params, f"Expected 'symbols' param, got: {list(params.keys())}"
        assert params["symbols"] == ["USD"]
        assert "to" not in params, "'to' is not a valid Frankfurter param (use 'symbols')"

    def test_url_date_range_format(self):
        url = fh._build_timeseries_url("EUR", "USD", date(2020, 3, 15), date(2021, 3, 14))
        path = urlparse(url).path
        assert "2020-03-15..2021-03-14" in path, f"Date range not in path: {path}"

    def test_base_url_points_to_frankfurter(self):
        assert "api.frankfurter.dev" in fh.BASE_URL


# ── Corridor fetching ───────────────────────────────────────────────────────

class TestFetchCorridor:
    def test_single_chunk(self):
        fake_data = _make_frankfurter_response("EUR", "USD", {
            "2024-01-02": 1.1050,
            "2024-01-03": 1.1075,
            "2024-01-04": 1.1020,
        })

        with patch.object(fh, "_fetch_json", return_value=fake_data):
            rows = fh.fetch_corridor("EUR", "USD", date(2024, 1, 2), date(2024, 1, 4))

        assert len(rows) == 3
        assert all(r["from_currency"] == "EUR" for r in rows)
        assert all(r["to_currency"] == "USD" for r in rows)
        assert {r["date"] for r in rows} == {"2024-01-02", "2024-01-03", "2024-01-04"}

    def test_multiple_chunks(self):
        call_count = 0

        def mock_fetch(url, retries=3):
            nonlocal call_count
            call_count += 1
            return _make_frankfurter_response("EUR", "USD", {
                f"2024-0{min(call_count, 9)}-01": 1.08 + call_count * 0.001,
            })

        with patch.object(fh, "_fetch_json", side_effect=mock_fetch):
            with patch.object(fh, "REQUEST_DELAY", 0):
                rows = fh.fetch_corridor("EUR", "USD", date(2023, 1, 1), date(2024, 12, 31))

        assert call_count >= 2, "Should have made at least 2 chunk requests for a 2-year range"
        assert len(rows) == call_count

    def test_passes_correct_url_to_fetch(self):
        captured_urls: list[str] = []

        def capture_fetch(url, retries=3):
            captured_urls.append(url)
            return _make_frankfurter_response("EUR", "USD", {"2024-06-01": 1.08})

        with patch.object(fh, "_fetch_json", side_effect=capture_fetch):
            fh.fetch_corridor("EUR", "USD", date(2024, 6, 1), date(2024, 6, 1))

        assert len(captured_urls) == 1
        url = captured_urls[0]
        assert "/v1/" in url, f"Missing /v1/ in URL: {url}"
        params = parse_qs(urlparse(url).query)
        assert params.get("base") == ["EUR"]
        assert params.get("symbols") == ["USD"]

    def test_handles_api_failure(self):
        with patch.object(fh, "_fetch_json", return_value=None):
            with patch.object(fh, "REQUEST_DELAY", 0):
                rows = fh.fetch_corridor("EUR", "USD", date(2024, 1, 1), date(2024, 1, 5))

        assert rows == []


# ── CSV output ──────────────────────────────────────────────────────────────

class TestMainCSVOutput:
    def test_writes_csv_with_correct_columns(self, tmp_path):
        csv_path = tmp_path / "historical_rates.csv"

        fake_data = _make_frankfurter_response("EUR", "USD", {
            "2024-06-01": 1.0850,
        })

        with (
            patch.object(fh, "_fetch_json", return_value=fake_data),
            patch.object(fh, "REQUEST_DELAY", 0),
            patch.object(fh, "OUTPUT_FILE", str(csv_path)),
            patch.object(fh, "OUTPUT_DIR", str(tmp_path)),
        ):
            fh.main()

        assert csv_path.exists()

        with open(csv_path) as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ["date", "from_currency", "to_currency", "rate"]
            rows = list(reader)

        assert len(rows) > 0
        for row in rows:
            assert row["date"]
            assert row["from_currency"]
            assert row["to_currency"]
            assert float(row["rate"]) > 0

    def test_includes_required_corridors(self, tmp_path):
        """CSV must include EUR/USD, GBP/INR, USD/PHP (the app corridors Frankfurter supports)."""
        csv_path = tmp_path / "historical_rates.csv"

        def fake_fetch(url, retries=3):
            params = parse_qs(urlparse(url).query)
            from_ccy = params.get("base", ["EUR"])[0]
            to_ccy = params.get("symbols", ["USD"])[0]
            return _make_frankfurter_response(from_ccy, to_ccy, {
                "2024-06-01": 10.5,
            })

        with (
            patch.object(fh, "_fetch_json", side_effect=fake_fetch),
            patch.object(fh, "REQUEST_DELAY", 0),
            patch.object(fh, "OUTPUT_FILE", str(csv_path)),
            patch.object(fh, "OUTPUT_DIR", str(tmp_path)),
            patch.object(fh, "START_DATE", date(2024, 6, 1)),
        ):
            fh.main()

        with open(csv_path) as f:
            rows = list(csv.DictReader(f))

        corridors = {f"{r['from_currency']}/{r['to_currency']}" for r in rows}
        assert "EUR/USD" in corridors, f"EUR/USD missing, got: {corridors}"
        assert "GBP/INR" in corridors, f"GBP/INR missing, got: {corridors}"
        assert "USD/PHP" in corridors, f"USD/PHP missing, got: {corridors}"
        assert "USD/MXN" in corridors, f"USD/MXN missing, got: {corridors}"
        assert "USD/BRL" in corridors, f"USD/BRL missing, got: {corridors}"


# ── Retry logic ─────────────────────────────────────────────────────────────

class TestFetchJson:
    def test_retries_on_failure(self):
        mock_urlopen = MagicMock(side_effect=Exception("connection refused"))

        with (
            patch.object(fh, "httpx", None),
            patch("urllib.request.urlopen", mock_urlopen),
        ):
            result = fh._fetch_json("http://example.com/test", retries=2)

        assert result is None
        assert mock_urlopen.call_count == 2


# ── Configuration ───────────────────────────────────────────────────────────

class TestConfiguration:
    def test_required_app_corridors_configured(self):
        """The corridors that overlap between the app and Frankfurter must be present."""
        assert "USD" in fh.CORRIDORS.get("EUR", [])
        assert "INR" in fh.CORRIDORS.get("GBP", [])
        assert "PHP" in fh.CORRIDORS.get("USD", [])
        assert "MXN" in fh.CORRIDORS.get("USD", [])
        assert "BRL" in fh.CORRIDORS.get("USD", [])

    def test_start_date_is_1999(self):
        assert fh.START_DATE == date(1999, 1, 4)

    def test_sufficient_corridor_count(self):
        """Should have a good number of corridors for ML training."""
        total = sum(len(targets) for targets in fh.CORRIDORS.values())
        assert total >= 10, f"Only {total} corridors — need at least 10 for useful ML training"


if __name__ == "__main__":
    import pytest
    pytest.main(["-v", __file__])