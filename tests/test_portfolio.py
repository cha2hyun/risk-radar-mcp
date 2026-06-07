import pandas as pd
from unittest.mock import MagicMock
from risk_radar_mcp.providers import yfinance_provider


def test_value_positions_krw_with_usd_fx(monkeypatch) -> None:
    def fake_ticker(symbol: str):
        mock_ticker = MagicMock()
        if symbol == "KRW=X":
            class MockInfo:
                last_price = 1400
                currency = "KRW"
            mock_ticker.fast_info = MockInfo()
            df = pd.DataFrame(
                {"Close": [1400, 1400], "Open": [1400, 1400]},
                index=pd.date_range("2026-06-04", periods=2)
            )
            mock_ticker.history.return_value = df
        return mock_ticker

    monkeypatch.setattr("yfinance.Ticker", fake_ticker)

    def fake_download(tickers, **kwargs):
        if isinstance(tickers, list) and len(tickers) > 1:
            columns = pd.MultiIndex.from_product([["005930.KS", "TQQQ"], ["Close", "Open"]])
            df = pd.DataFrame(index=pd.date_range("2026-06-04", periods=2), columns=columns)
            df.loc[:, ("005930.KS", "Close")] = [80000, 80000]
            df.loc[:, ("TQQQ", "Close")] = [100, 100]
            return df
        return pd.DataFrame()

    monkeypatch.setattr("yfinance.download", fake_download)

    result = yfinance_provider.value_positions(
        [
            {
                "account_id": "main",
                "ticker": "005930",
                "name": "Samsung Electronics",
                "quantity": 2,
                "currency": "KRW",
                "cost_basis_snapshot": 100000,
            },
            {
                "account_id": "main",
                "ticker": "TQQQ",
                "quantity": 3,
                "currency": "USD",
                "cost_basis_snapshot_krw": 300000,
            },
        ]
    )

    assert result["fx"]["USD/KRW"] == 1400
    assert result["totals"]["market_value_krw"] == 580000
    assert result["totals"]["cost_basis_krw"] == 400000
    assert result["totals"]["unrealized_pl_krw"] == 180000
    assert result["positions"][1]["market_value_krw"] == 420000
