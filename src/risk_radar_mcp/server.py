"""Risk Radar MCP server."""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP

from risk_radar_mcp.providers import yfinance_provider

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


def main() -> None:
    """Run the MCP server."""

    host = os.getenv("RISK_RADAR_HOST", "0.0.0.0")
    port = int(os.getenv("RISK_RADAR_PORT", "8765"))
    mcp.run(transport="http", host=host, port=port, path="/mcp")


if __name__ == "__main__":
    main()
