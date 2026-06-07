"""Risk Radar MCP server."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from fastmcp import FastMCP

from risk_radar_mcp.providers import yfinance_provider
from risk_radar_mcp.providers import fred_provider
from risk_radar_mcp import portfolio

mcp = FastMCP(
    name="risk-radar-mcp",
    instructions=(
        "Read-only market data MCP. Never execute trades, access brokerage accounts, "
        "or present market outcomes as certainty."
    ),
)


@mcp.tool
def get_quote(symbol: str) -> dict[str, Any]:
    """Get the latest available quote for a symbol or alias."""

    return yfinance_provider.quote(symbol)


@mcp.tool
def get_quotes(symbols: list[str]) -> dict[str, Any]:
    """Get latest available quotes for multiple symbols in one batched request."""

    return yfinance_provider.quotes(symbols)


@mcp.tool
def value_positions(
    positions: list[dict[str, Any]],
    valuation_currency: str = "KRW",
) -> dict[str, Any]:
    """Estimate live position values from a list of portfolio positions.

    Each position should include ticker or symbol, quantity, currency, and optional
    cost-basis fields such as cost_basis_snapshot, cost_basis_snapshot_krw,
    avg_cost_per_share, or avg_cost_per_share_krw.
    """

    return portfolio.value_positions(
        positions,
        valuation_currency=valuation_currency,
    )


@mcp.tool
def get_ohlcv(
    symbol: str,
    period: str = "6mo",
    interval: str = "1d",
    limit: int = 120,
) -> dict[str, Any]:
    """Get OHLCV history from Yahoo Finance.

    Common period values: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max.
    Common interval values: 1m, 5m, 15m, 30m, 1h, 1d, 1wk, 1mo.
    """

    safe_limit = max(1, min(limit, 500))
    return yfinance_provider.ohlcv(symbol, period=period, interval=interval, limit=safe_limit)


@mcp.tool
def get_indicators(symbol: str, period: str = "1y", interval: str = "1d") -> dict[str, Any]:
    """Get OHLCV plus common indicators: MA, EMA, RSI, MACD, Bollinger, ATR, OBV."""

    return yfinance_provider.indicators(symbol, period=period, interval=interval)


@mcp.tool
def get_market_snapshot() -> dict[str, Any]:
    """Get a BTC/Nasdaq/macro-proxy risk snapshot."""

    return yfinance_provider.market_snapshot()


@mcp.tool
def get_news(symbol: str, limit: int = 10) -> dict[str, Any]:
    """Get recent Yahoo Finance news for a symbol."""

    safe_limit = max(1, min(limit, 25))
    return yfinance_provider.news(symbol, limit=safe_limit)


@mcp.tool
def get_macro_series(
    series_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Fetch historical FRED macro series data.

    Common series: FEDFUNDS, DGS10, DGS2, T10Y2Y, CPIAUCSL, UNRATE,
    PAYEMS, M2SL, BAMLH0A0HYM2, NFCI.
    Dates in 'YYYY-MM-DD' format. Default: last 1 year.
    Requires FRED_API_KEY env var.
    """
    return fred_provider.get_macro_series(series_id, start_date, end_date)


@mcp.tool
def get_macro_latest(series_ids: list[str]) -> dict[str, Any]:
    """Get the latest observation for one or more FRED macro series.

    Requires FRED_API_KEY env var.
    """
    return fred_provider.get_macro_latest(series_ids)


@mcp.tool
def get_macro_snapshot() -> dict[str, Any]:
    """Get a snapshot of key FRED macro indicators for risk assessment.

    Covers: Fed funds, Treasury yields, spread, CPI, unemployment,
    payrolls, M2, high-yield spread, and financial conditions.
    Requires FRED_API_KEY env var.
    """
    return fred_provider.get_macro_snapshot()


@mcp.tool
def get_risk_dashboard() -> dict[str, Any]:
    """Combine market snapshot (yfinance) with macro snapshot (FRED).

    Returns a consolidated risk dashboard with both market and macro views.
    FRED portion fails gracefully when FRED_API_KEY is not set.
    """
    market = yfinance_provider.market_snapshot()

    try:
        macro = fred_provider.get_macro_snapshot()
    except Exception as exc:
        macro = {"error": str(exc), "snapshot": {}}

    return {
        "market": market,
        "macro": macro,
        "generated_at": datetime.now().isoformat(),
        "stale_label": (
            "⚠️ Market data may be delayed. Macro data is delayed and revised. "
            "Do not treat as real-time. No financial advice."
        ),
    }


def main() -> None:
    """Run the MCP server."""

    host = os.getenv("RISK_RADAR_HOST", "0.0.0.0")
    port = int(os.getenv("RISK_RADAR_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port, path="/mcp")


if __name__ == "__main__":
    main()
