"""Tests for FRED macro provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from risk_radar_mcp.providers import fred_provider


class TestCheckApiKey:
    def test_raises_when_env_empty(self):
        with patch.object(fred_provider, "FRED_API_KEY", ""):
            with pytest.raises(RuntimeError, match="FRED_API_KEY is not set"):
                fred_provider._check_api_key()

    def test_passes_when_env_set(self):
        with patch.object(fred_provider, "FRED_API_KEY", "test-key"):
            fred_provider._check_api_key()  # should not raise


class TestStaleLabel:
    def test_includes_series_id(self):
        label = fred_provider._stale_label("DGS10")
        assert "DGS10" in label
        assert "delayed" in label.lower()


class TestGetMacroSeries:
    def test_error_when_no_key(self):
        with patch.object(fred_provider, "FRED_API_KEY", ""):
            result = fred_provider.get_macro_series("DGS10")
            assert "error" in result
            assert "FRED_API_KEY" in result["error"]

    def test_returns_data_when_key_set(self):
        mock_fred = MagicMock()
        mock_fred.get_series_info.return_value = {"title": "10-Year Treasury"}
        import pandas as pd

        mock_fred.get_series.return_value = pd.Series(
            [4.5, 4.6],
            index=pd.DatetimeIndex(["2025-01-01", "2025-01-02"]),
        )

        with patch.object(fred_provider, "FRED_API_KEY", "test-key"):
            with patch("fredapi.Fred", return_value=mock_fred):
                result = fred_provider.get_macro_series("DGS10")
                assert result["series_id"] == "DGS10"
                assert result["count"] == 2
                assert "stale_label" in result

    def test_empty_series(self):
        mock_fred = MagicMock()
        mock_fred.get_series_info.return_value = {"title": "Empty"}
        import pandas as pd

        mock_fred.get_series.return_value = pd.Series([], dtype=float)

        with patch.object(fred_provider, "FRED_API_KEY", "test-key"):
            with patch("fredapi.Fred", return_value=mock_fred):
                result = fred_provider.get_macro_series("EMPTY")
                assert result["count"] == 0


class TestGetMacroLatest:
    def test_error_when_no_key(self):
        with patch.object(fred_provider, "FRED_API_KEY", ""):
            result = fred_provider.get_macro_latest(["DGS10"])
            assert "error" in result

    def test_returns_results_when_key_set(self):
        mock_fred = MagicMock()
        mock_fred.get_series_info.return_value = {"title": "10Y", "last_updated": "2025-01-03"}
        import pandas as pd

        mock_fred.get_series.return_value = pd.Series(
            [4.6], index=pd.DatetimeIndex(["2025-01-02"])
        )

        with patch.object(fred_provider, "FRED_API_KEY", "test-key"):
            with patch("fredapi.Fred", return_value=mock_fred):
                result = fred_provider.get_macro_latest(["DGS10"])
                assert "results" in result
                assert result["results"]["DGS10"]["value"] == 4.6

    def test_handles_partial_failures(self):
        mock_fred = MagicMock()
        mock_fred.get_series_info.side_effect = [
            {"title": "10Y", "last_updated": "2025-01-03"},
            Exception("not found"),
        ]

        import pandas as pd

        mock_fred.get_series.return_value = pd.Series(
            [4.6], index=pd.DatetimeIndex(["2025-01-02"])
        )

        with patch.object(fred_provider, "FRED_API_KEY", "test-key"):
            with patch("fredapi.Fred", return_value=mock_fred):
                result = fred_provider.get_macro_latest(["DGS10", "BAD"])
                assert "results" in result
                assert result["results"]["DGS10"]["value"] == 4.6
                assert "error" in result["results"]["BAD"]


class TestGetMacroSnapshot:
    def test_returns_all_candidate_series(self):
        mock_fred = MagicMock()
        mock_fred.get_series_info.return_value = {"title": "Test", "last_updated": None}
        import pandas as pd

        mock_fred.get_series.return_value = pd.Series(
            [1.0], index=pd.DatetimeIndex(["2025-01-01"])
        )

        with patch.object(fred_provider, "FRED_API_KEY", "test-key"):
            with patch("fredapi.Fred", return_value=mock_fred):
                result = fred_provider.get_macro_snapshot()
                assert "snapshot" in result
                assert "stale_label" in result
                for sid in fred_provider.MACRO_SNAPSHOT_SERIES:
                    assert sid in result["snapshot"]


class TestGetRiskDashboard:
    def test_combines_market_and_macro(self):
        from risk_radar_mcp import server
        with patch.object(
            server.fred_provider, "get_macro_snapshot", return_value={"test": "macro"}
        ):
            with patch.object(
                server.yfinance_provider, "market_snapshot", return_value={"test": "market"}
            ):
                result = server.get_risk_dashboard()
                assert result["market"] == {"test": "market"}
                assert result["macro"] == {"test": "macro"}
                assert "stale_label" in result


class TestMacroSnapshotSeries:
    def test_has_expected_series(self):
        expected = {
            "FEDFUNDS",
            "DGS10",
            "DGS2",
            "T10Y2Y",
            "CPIAUCSL",
            "UNRATE",
            "PAYEMS",
            "M2SL",
            "BAMLH0A0HYM2",
            "NFCI",
        }
        assert set(fred_provider.MACRO_SNAPSHOT_SERIES.keys()) == expected
