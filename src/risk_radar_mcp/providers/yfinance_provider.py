"""Read-only Yahoo Finance provider."""

from __future__ import annotations

import contextlib
import io
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


def _quote_from_history(input_symbol: str, normalized: str, data: pd.DataFrame) -> dict[str, Any]:
    clean = data.dropna(subset=["Close"], how="all")
    if clean.empty:
        raise ValueError(f"no quote data returned for symbol: {normalized}")

    latest = clean.iloc[-1]
    previous_close = clean["Close"].iloc[-2] if len(clean) > 1 else None
    last_price = latest.get("Close")
    change = None
    change_percent = None
    if previous_close is not None and previous_close != 0:
        change = float(last_price - previous_close)
        change_percent = float((change / previous_close) * 100)

    return {
        "input_symbol": input_symbol,
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
    }


def _download_quote_history(symbols: list[str]) -> dict[str, pd.DataFrame]:
    if not symbols:
        return {}

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
    if raw.empty:
        return {}

    if isinstance(raw.columns, pd.MultiIndex):
        return {
            symbol: raw[symbol].dropna(how="all")
            for symbol in symbols
            if symbol in raw.columns.get_level_values(0)
        }
    return {symbols[0]: raw.dropna(how="all")}


def quotes(symbols: list[str]) -> dict[str, Any]:
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
            item = _quote_from_history(input_symbol, normalized, data)
            item["status"] = "ok"
        except Exception as exc:
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


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _cost_basis_native(position: dict[str, Any], quantity: float, currency: str) -> float | None:
    cost_currency = str(position.get("cost_currency") or currency).upper()
    direct = _as_float(position.get("cost_basis_snapshot"))
    if direct is not None and cost_currency == currency:
        return direct

    avg_cost = _as_float(position.get("avg_cost_per_share"))
    if avg_cost is not None:
        return avg_cost * quantity

    cost_key = f"cost_basis_snapshot_{currency.lower()}"
    direct_currency = _as_float(position.get(cost_key))
    if direct_currency is not None:
        return direct_currency
    return None


def _cost_basis_krw(position: dict[str, Any], quantity: float, currency: str) -> float | None:
    direct_krw = _as_float(position.get("cost_basis_snapshot_krw"))
    if direct_krw is not None:
        return direct_krw

    avg_krw = _as_float(position.get("avg_cost_per_share_krw"))
    if avg_krw is not None:
        return avg_krw * quantity

    if currency == "KRW":
        return _cost_basis_native(position, quantity, currency)
    return None


def value_positions(
    positions: list[dict[str, Any]],
    valuation_currency: str = "KRW",
) -> dict[str, Any]:
    if not positions:
        raise ValueError("positions must not be empty")
    if len(positions) > 200:
        raise ValueError("positions limit exceeded: max 200")

    valuation_currency = valuation_currency.upper()
    if valuation_currency != "KRW":
        raise ValueError("only KRW valuation_currency is currently supported")

    symbols = [str(position.get("ticker") or position.get("symbol") or "") for position in positions]
    quote_result = quotes(symbols)
    quote_by_input = {item["input_symbol"]: item for item in quote_result["items"]}

    usdkrw = None
    if any(str(position.get("currency", "")).upper() == "USD" for position in positions):
        try:
            usdkrw_quote = quote("usdkrw")
            usdkrw = _as_float(usdkrw_quote.get("last_price"))
        except Exception:
            usdkrw = None

    valued_positions: list[dict[str, Any]] = []
    totals: dict[str, Any] = {
        "market_value_krw": 0.0,
        "cost_basis_krw": 0.0,
        "unrealized_pl_krw": 0.0,
        "cash_krw": 0.0,
        "positions": len(positions),
        "missing_market_value_count": 0,
        "missing_cost_basis_count": 0,
        "missing_unrealized_pl_count": 0,
    }
    by_account: dict[str, dict[str, Any]] = {}

    for position in positions:
        input_symbol = str(position.get("ticker") or position.get("symbol") or "")
        quote_item = quote_by_input.get(input_symbol, {})
        quantity = _as_float(position.get("quantity")) or 0.0
        currency = str(position.get("currency") or "").upper()
        account_id = str(position.get("account_id") or "unassigned")
        account_name = position.get("account_name")

        last_price = _as_float(quote_item.get("last_price"))
        market_value_native = last_price * quantity if last_price is not None else None
        market_value_krw = None
        if market_value_native is not None:
            if currency == "KRW":
                market_value_krw = market_value_native
            elif currency == "USD" and usdkrw is not None:
                market_value_krw = market_value_native * usdkrw

        cost_basis_native = _cost_basis_native(position, quantity, currency)
        cost_basis_krw = _cost_basis_krw(position, quantity, currency)
        unrealized_pl_krw = (
            market_value_krw - cost_basis_krw
            if market_value_krw is not None and cost_basis_krw is not None
            else None
        )
        unrealized_pl_percent = (
            (unrealized_pl_krw / cost_basis_krw) * 100
            if unrealized_pl_krw is not None and cost_basis_krw not in (None, 0)
            else None
        )

        account = by_account.setdefault(
            account_id,
            {
                "account_id": account_id,
                "account_name": account_name,
                "market_value_krw": 0.0,
                "cost_basis_krw": 0.0,
                "unrealized_pl_krw": 0.0,
                "positions": 0,
                "missing_market_value_count": 0,
                "missing_cost_basis_count": 0,
                "missing_unrealized_pl_count": 0,
            },
        )
        account["positions"] += 1

        for key, value in (
            ("market_value_krw", market_value_krw),
            ("cost_basis_krw", cost_basis_krw),
            ("unrealized_pl_krw", unrealized_pl_krw),
        ):
            if value is None:
                missing_key = f"missing_{key.removesuffix('_krw')}_count"
                totals[missing_key] += 1
                account[missing_key] += 1
            else:
                totals[key] += value
                account[key] += value

        valued_positions.append(
            {
                "account_id": account_id,
                "account_name": account_name,
                "name": position.get("name"),
                "input_symbol": input_symbol,
                "symbol": quote_item.get("symbol") or normalize_symbol(input_symbol),
                "quantity": quantity,
                "price_currency": currency,
                "last_price": _clean_float(last_price),
                "market_value_native": _clean_float(market_value_native),
                "market_value_krw": _clean_float(market_value_krw),
                "cost_basis_native": _clean_float(cost_basis_native),
                "cost_basis_krw": _clean_float(cost_basis_krw),
                "unrealized_pl_krw": _clean_float(unrealized_pl_krw),
                "unrealized_pl_percent": _clean_float(unrealized_pl_percent),
                "quote_status": quote_item.get("status"),
                "quote_error": quote_item.get("error"),
                "as_of": quote_item.get("as_of"),
            }
        )

    clean_totals = {key: _clean_float(value) for key, value in totals.items()}
    clean_totals["market_value_complete"] = totals["missing_market_value_count"] == 0
    clean_totals["cost_basis_complete"] = totals["missing_cost_basis_count"] == 0
    clean_totals["unrealized_pl_complete"] = totals["missing_unrealized_pl_count"] == 0
    for account in by_account.values():
        account["market_value_complete"] = account["missing_market_value_count"] == 0
        account["cost_basis_complete"] = account["missing_cost_basis_count"] == 0
        account["unrealized_pl_complete"] = account["missing_unrealized_pl_count"] == 0
    return {
        "source": "yfinance",
        "valuation_currency": valuation_currency,
        "fx": {"USD/KRW": _clean_float(usdkrw)},
        "totals": clean_totals,
        "accounts": list(by_account.values()),
        "positions": valued_positions,
        "note": "Read-only estimate. Yahoo Finance data may be delayed, incomplete, or unavailable.",
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
