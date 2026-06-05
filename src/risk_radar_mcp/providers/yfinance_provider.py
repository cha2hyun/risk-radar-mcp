"""Read-only Yahoo Finance provider."""

from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from risk_radar_mcp.indicators import add_indicators, latest_indicator_snapshot
from risk_radar_mcp.symbols import MARKET_SNAPSHOT_SYMBOLS, normalize_symbol

ALLOWED_PERIODS = {
    "1d",
    "5d",
    "1mo",
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "ytd",
    "max",
}
ALLOWED_INTERVALS = {
    "1m",
    "2m",
    "5m",
    "15m",
    "30m",
    "60m",
    "90m",
    "1h",
    "1d",
    "5d",
    "1wk",
    "1mo",
    "3mo",
}


def _clean_float(value: Any) -> float | int | str | None:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, (int, float, str)):
        return value
    if hasattr(value, "item"):
        item = value.item()
        return item if isinstance(item, (int, float, str)) else str(item)
    return str(value)


def _records(df: pd.DataFrame, limit: int | None = None) -> list[dict[str, Any]]:
    data = df.tail(limit).copy() if limit else df.copy()
    data = data.reset_index()
    rows: list[dict[str, Any]] = []
    for row in data.to_dict(orient="records"):
        rows.append(
            {
                str(key): value.isoformat() if hasattr(value, "isoformat") else _clean_float(value)
                for key, value in row.items()
            }
        )
    return rows


def get_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    normalized = normalize_symbol(symbol)
    if period not in ALLOWED_PERIODS:
        raise ValueError(f"unsupported period: {period}")
    if interval not in ALLOWED_INTERVALS:
        raise ValueError(f"unsupported interval: {interval}")
    data = yf.Ticker(normalized).history(period=period, interval=interval, auto_adjust=False)
    if data.empty:
        raise ValueError(f"no data returned for symbol: {normalized}")
    return data


def quote(symbol: str) -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    ticker = yf.Ticker(normalized)
    hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
    if hist.empty:
        raise ValueError(f"no quote data returned for symbol: {normalized}")

    latest = hist.iloc[-1]
    previous_close = hist["Close"].iloc[-2] if len(hist) > 1 else None
    last_price = latest.get("Close")
    change = None
    change_percent = None
    if previous_close is not None and previous_close != 0:
        change = float(last_price - previous_close)
        change_percent = float((change / previous_close) * 100)

    info: dict[str, Any] = {}
    try:
        raw_info = ticker.fast_info
        info = {
            "currency": getattr(raw_info, "currency", None),
            "exchange": getattr(raw_info, "exchange", None),
            "timezone": getattr(raw_info, "timezone", None),
        }
    except Exception:
        info = {}

    return {
        "symbol": normalized,
        "source": "yfinance",
        "last_price": _clean_float(last_price),
        "previous_close": _clean_float(previous_close),
        "change": _clean_float(change),
        "change_percent": _clean_float(change_percent),
        "open": _clean_float(latest.get("Open")),
        "high": _clean_float(latest.get("High")),
        "low": _clean_float(latest.get("Low")),
        "volume": _clean_float(latest.get("Volume")),
        "as_of": latest.name.isoformat() if hasattr(latest.name, "isoformat") else str(latest.name),
        "metadata": info,
    }


def ohlcv(symbol: str, period: str = "6mo", interval: str = "1d", limit: int = 120) -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    data = get_history(normalized, period=period, interval=interval)
    return {
        "symbol": normalized,
        "source": "yfinance",
        "period": period,
        "interval": interval,
        "rows": _records(data, limit=limit),
    }


def indicators(symbol: str, period: str = "1y", interval: str = "1d") -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    data = get_history(normalized, period=period, interval=interval)
    enriched = add_indicators(data)
    return {
        "symbol": normalized,
        "source": "yfinance",
        "period": period,
        "interval": interval,
        "latest": latest_indicator_snapshot(data),
        "rows": _records(enriched, limit=60),
    }


def market_snapshot() -> dict[str, Any]:
    items = {}
    for alias, symbol in MARKET_SNAPSHOT_SYMBOLS.items():
        try:
            items[alias] = quote(symbol)
        except Exception as exc:  # Keep snapshot resilient.
            items[alias] = {
                "symbol": symbol,
                "source": "yfinance",
                "error": str(exc),
            }
    return {
        "source": "yfinance",
        "items": items,
        "note": "Yahoo Finance data may be delayed, incomplete, or unavailable.",
    }


def news(symbol: str, limit: int = 10) -> dict[str, Any]:
    normalized = normalize_symbol(symbol)
    ticker = yf.Ticker(normalized)
    try:
        raw_news = ticker.get_news(count=limit)
    except TypeError:
        raw_news = ticker.news[:limit]
    items = []
    for item in raw_news[:limit]:
        content = item.get("content", item)
        items.append(
            {
                "title": content.get("title") or item.get("title"),
                "publisher": content.get("provider", {}).get("displayName")
                if isinstance(content.get("provider"), dict)
                else item.get("publisher"),
                "link": content.get("canonicalUrl", {}).get("url")
                if isinstance(content.get("canonicalUrl"), dict)
                else item.get("link"),
                "published": content.get("pubDate") or item.get("providerPublishTime"),
            }
        )
    return {
        "symbol": normalized,
        "source": "yfinance",
        "items": items,
    }
