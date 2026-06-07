"""Read-only Yahoo Finance provider."""

from __future__ import annotations

import contextlib
import io
from typing import Any

import pandas as pd
import yfinance as yf

from risk_radar_mcp.indicators import add_indicators, latest_indicator_snapshot
from risk_radar_mcp.symbols import MARKET_SNAPSHOT_SYMBOLS, normalize_symbol
from risk_radar_mcp.types import QuoteResult, SnapshotResult
from risk_radar_mcp.exceptions import ProviderError

# Future classes will inherit from BaseProvider

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


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def get_history(symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
    normalized = normalize_symbol(symbol)
    if period not in ALLOWED_PERIODS:
        raise ValueError(f"unsupported period: {period}")
    if interval not in ALLOWED_INTERVALS:
        raise ValueError(f"unsupported interval: {interval}")
    try:
        data = yf.Ticker(normalized).history(period=period, interval=interval, auto_adjust=False)
    except Exception as exc:
        if isinstance(exc, (KeyError, TypeError, ValueError)):
            raise
        raise ProviderError(str(exc)) from exc
    if data.empty:
        raise ValueError(f"no data returned for symbol: {normalized}")
    return data


def _build_quote_dict(latest_row: Any, previous_close: Any, last_price: Any = None) -> dict[str, Any]:
    if last_price is None:
        last_price = latest_row.get("Close")
        
    last_price_float = _as_float(last_price)
    previous_close_float = _as_float(previous_close)
    change = None
    change_percent = None
    if last_price_float is not None and previous_close_float not in (None, 0):
        change = last_price_float - previous_close_float
        change_percent = (change / previous_close_float) * 100

    return {
        "last_price": _clean_float(last_price),
        "previous_close": _clean_float(previous_close),
        "change": _clean_float(change),
        "change_percent": _clean_float(change_percent),
        "open": _clean_float(latest_row.get("Open")),
        "high": _clean_float(latest_row.get("High")),
        "low": _clean_float(latest_row.get("Low")),
        "volume": _clean_float(latest_row.get("Volume")),
        "as_of": latest_row.name.isoformat() if hasattr(latest_row.name, "isoformat") else str(latest_row.name),
    }


def quote(symbol: str) -> QuoteResult:
    normalized = normalize_symbol(symbol)
    ticker = yf.Ticker(normalized)
    try:
        hist = ticker.history(period="5d", interval="1d", auto_adjust=False)
    except Exception as exc:
        if isinstance(exc, (KeyError, TypeError, ValueError)):
            raise
        raise ProviderError(str(exc)) from exc
    if hist.empty:
        raise ValueError(f"no quote data returned for symbol: {normalized}")

    latest = hist.iloc[-1]
    previous_close = hist["Close"].iloc[-2] if len(hist) > 1 else None
    last_price = latest.get("Close")
    info: dict[str, Any] = {}
    try:
        raw_info = ticker.fast_info
        fast_last_price = _as_float(getattr(raw_info, "last_price", None))
        if fast_last_price is None:
            fast_last_price = _as_float(getattr(raw_info, "lastPrice", None))
        if _as_float(last_price) is None and fast_last_price is not None:
            last_price = fast_last_price
        fast_previous_close = _as_float(getattr(raw_info, "regular_market_previous_close", None))
        if fast_previous_close is None:
            fast_previous_close = _as_float(getattr(raw_info, "regularMarketPreviousClose", None))
        if _as_float(previous_close) is None and fast_previous_close is not None:
            previous_close = fast_previous_close
        info = {
            "currency": getattr(raw_info, "currency", None),
            "exchange": getattr(raw_info, "exchange", None),
            "timezone": getattr(raw_info, "timezone", None),
        }
    except Exception as exc:
        if isinstance(exc, (KeyError, TypeError, ValueError)):
            raise
        raise ProviderError(str(exc)) from exc

    base = _build_quote_dict(latest, previous_close, last_price=last_price)

    return {
        "symbol": normalized,
        "source": "yfinance",
        **base,
        "metadata": info,
    }


def _quote_from_history(input_symbol: str, normalized: str, data: pd.DataFrame) -> dict[str, Any]:
    clean = data.dropna(subset=["Close"], how="all")
    if clean.empty:
        raise ValueError(f"no quote data returned for symbol: {normalized}")

    latest = clean.iloc[-1]
    previous_close = clean["Close"].iloc[-2] if len(clean) > 1 else None

    base = _build_quote_dict(latest, previous_close)

    return {
        "input_symbol": input_symbol,
        "symbol": normalized,
        "source": "yfinance",
        **base,
    }


def _download_quote_history(symbols: list[str]) -> dict[str, pd.DataFrame]:
    if not symbols:
        return {}

    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            raw = yf.download(
                tickers=symbols,
                period="5d",
                interval="1d",
                auto_adjust=False,
                progress=False,
                threads=True,
                group_by="ticker",
            )
    except Exception as exc:
        if isinstance(exc, (KeyError, TypeError, ValueError)):
            raise
        raise ProviderError(str(exc)) from exc
    if raw.empty:
        return {}

    if isinstance(raw.columns, pd.MultiIndex):
        return {
            symbol: raw[symbol].dropna(how="all")
            for symbol in symbols
            if symbol in raw.columns.get_level_values(0)
        }
    return {symbols[0]: raw.dropna(how="all")}


def quotes(symbols: list[str]) -> QuoteResult:
    if not symbols:
        raise ValueError("symbols must not be empty")
    if len(symbols) > 200:
        raise ValueError("symbols limit exceeded: max 200")

    normalized_by_input = [(symbol, normalize_symbol(symbol)) for symbol in symbols]
    unique_symbols = list(dict.fromkeys(normalized for _, normalized in normalized_by_input))
    history_by_symbol = _download_quote_history(unique_symbols)

    items: list[dict[str, Any]] = []
    for input_symbol, normalized in normalized_by_input:
        try:
            data = history_by_symbol.get(normalized)
            if data is None or data.empty:
                raise ValueError(f"no quote data returned for symbol: {normalized}")
            latest_close = data.iloc[-1].get("Close")
            if _as_float(latest_close) is None:
                item = quote(input_symbol)
                item["input_symbol"] = input_symbol
            else:
                item = _quote_from_history(input_symbol, normalized, data)
            item["status"] = "ok"
        except ProviderError as exc:
            item = {
                "input_symbol": input_symbol,
                "symbol": normalized,
                "source": "yfinance",
                "status": "error",
                "error": str(exc),
            }
        items.append(item)

    return {
        "source": "yfinance",
        "count": len(items),
        "items": items,
        "note": "Yahoo Finance data may be delayed, incomplete, or unavailable.",
    }


# Re-export for backward compatibility



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


def market_snapshot() -> SnapshotResult:
    items = {}
    for alias, symbol in MARKET_SNAPSHOT_SYMBOLS.items():
        try:
            items[alias] = quote(symbol)
        except ProviderError as exc:  # Keep snapshot resilient.
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
    except Exception as exc:
        if isinstance(exc, (KeyError, TypeError, ValueError)):
            raise
        raise ProviderError(str(exc)) from exc
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
