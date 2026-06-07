"""Portfolio valuation logic."""

from __future__ import annotations

import os
from typing import Any

from risk_radar_mcp.providers import yfinance_provider
from risk_radar_mcp.symbols import normalize_symbol

SUPPORTED_VALUATION_CURRENCIES = os.getenv("RISK_RADAR_VALUATION_CURRENCIES", "KRW").split(",")


def _cost_basis_native(position: dict[str, Any], quantity: float, currency: str) -> float | None:
    cost_currency = str(position.get("cost_currency") or currency).upper()
    direct = yfinance_provider._as_float(position.get("cost_basis_snapshot"))
    if direct is not None and cost_currency == currency:
        return direct

    avg_cost = yfinance_provider._as_float(position.get("avg_cost_per_share"))
    if avg_cost is not None:
        return avg_cost * quantity

    cost_key = f"cost_basis_snapshot_{currency.lower()}"
    direct_currency = yfinance_provider._as_float(position.get(cost_key))
    if direct_currency is not None:
        return direct_currency
    return None


def _cost_basis_krw(position: dict[str, Any], quantity: float, currency: str) -> float | None:
    direct_krw = yfinance_provider._as_float(position.get("cost_basis_snapshot_krw"))
    if direct_krw is not None:
        return direct_krw

    avg_krw = yfinance_provider._as_float(position.get("avg_cost_per_share_krw"))
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
    if valuation_currency not in SUPPORTED_VALUATION_CURRENCIES:
        raise ValueError(f"only {SUPPORTED_VALUATION_CURRENCIES} valuation_currencies are currently supported")

    symbols = [str(position.get("ticker") or position.get("symbol") or "") for position in positions]
    quote_result = yfinance_provider.quotes(symbols)
    quote_by_input = {item["input_symbol"]: item for item in quote_result["items"]}

    usdkrw = None
    if any(str(position.get("currency", "")).upper() == "USD" for position in positions):
        try:
            usdkrw_quote = yfinance_provider.quote("usdkrw")
            usdkrw = yfinance_provider._as_float(usdkrw_quote.get("last_price"))
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
        quantity = yfinance_provider._as_float(position.get("quantity")) or 0.0
        currency = str(position.get("currency") or "").upper()
        account_id = str(position.get("account_id") or "unassigned")
        account_name = position.get("account_name")

        last_price = yfinance_provider._as_float(quote_item.get("last_price"))
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
                "last_price": yfinance_provider._clean_float(last_price),
                "market_value_native": yfinance_provider._clean_float(market_value_native),
                "market_value_krw": yfinance_provider._clean_float(market_value_krw),
                "cost_basis_native": yfinance_provider._clean_float(cost_basis_native),
                "cost_basis_krw": yfinance_provider._clean_float(cost_basis_krw),
                "unrealized_pl_krw": yfinance_provider._clean_float(unrealized_pl_krw),
                "unrealized_pl_percent": yfinance_provider._clean_float(unrealized_pl_percent),
                "quote_status": quote_item.get("status"),
                "quote_error": quote_item.get("error"),
                "as_of": quote_item.get("as_of"),
            }
        )

    clean_totals = {key: yfinance_provider._clean_float(value) for key, value in totals.items()}
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
        "fx": {"USD/KRW": yfinance_provider._clean_float(usdkrw)},
        "totals": clean_totals,
        "accounts": list(by_account.values()),
        "positions": valued_positions,
        "note": "Read-only estimate. Yahoo Finance data may be delayed, incomplete, or unavailable.",
    }
