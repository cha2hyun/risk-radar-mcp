from typing import Any

from risk_radar_mcp.providers import yfinance_provider


def test_value_positions_krw_with_usd_fx(monkeypatch) -> None:
    def fake_quotes(symbols: list[str]) -> dict[str, Any]:
        prices = {
            "005930": {"symbol": "005930.KS", "last_price": 80000, "status": "ok"},
            "TQQQ": {"symbol": "TQQQ", "last_price": 100, "status": "ok"},
        }
        return {
            "source": "test",
            "count": len(symbols),
            "items": [
                {
                    "input_symbol": symbol,
                    "as_of": "2026-06-05",
                    **prices[symbol],
                }
                for symbol in symbols
            ],
        }

    def fake_quote(symbol: str) -> dict[str, Any]:
        assert symbol == "usdkrw"
        return {"symbol": "KRW=X", "last_price": 1400}

    monkeypatch.setattr(yfinance_provider, "quotes", fake_quotes)
    monkeypatch.setattr(yfinance_provider, "quote", fake_quote)

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
