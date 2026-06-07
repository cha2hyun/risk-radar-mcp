"""FRED macro data provider.

FRED (Federal Reserve Economic Data) provides official US and international
economic time series. All data is delayed/revised — this provider always
labels responses with staleness notes.

FRED API key: free from https://fred.stlouisfed.org/docs/api/api_key.html
Set as FRED_API_KEY environment variable.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from risk_radar_mcp.types import (
    MacroLatestResult,
    MacroSeriesResult,
    MacroSnapshotResult,
)
from risk_radar_mcp.exceptions import ProviderError

# Future classes will inherit from BaseProvider

FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Series used by get_macro_snapshot() and get_risk_dashboard()
MACRO_SNAPSHOT_SERIES: dict[str, str] = {
    "FEDFUNDS": "연방기금금리 (Fed Funds Rate)",
    "DGS10": "미국 10년물 국채금리",
    "DGS2": "미국 2년물 국채금리",
    "T10Y2Y": "10년-2년 스프레드",
    "CPIAUCSL": "소비자물가지수 (CPI)",
    "UNRATE": "실업률",
    "PAYEMS": "비농업고용 (Nonfarm Payrolls)",
    "M2SL": "M2 통화량",
    "BAMLH0A0HYM2": "하이일드 스프레드 (OAS)",
    "NFCI": "국가 금융여건 지수 (NFCI)",
}


def _check_api_key() -> None:
    if not FRED_API_KEY:
        raise RuntimeError(
            "FRED_API_KEY is not set. Get a free key at "
            "https://fred.stlouisfed.org/docs/api/api_key.html "
            "and set it in your .env file."
        )


def _fred_client():
    """Lazy-import fredapi so import errors only happen on first use."""
    _check_api_key()
    from fredapi import Fred

    return Fred(api_key=FRED_API_KEY)


def _stale_label(series_id: str) -> str:
    """Return a staleness disclaimer for the given series."""
    return (
        f"⚠️ FRED macro data is delayed and revised. "
        f"The reported value for {series_id} may not reflect the most recent release. "
        f"Do not treat as real-time."
    )


def get_macro_series(
    series_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> MacroSeriesResult:
    """Fetch historical FRED series data.

    Args:
        series_id: FRED series identifier (e.g. 'DGS10', 'UNRATE').
        start_date: Optional 'YYYY-MM-DD' start (default: 1 year ago).
        end_date: Optional 'YYYY-MM-DD' end (default: today).

    Returns:
        Dict with series_id, description, staleness label, and data list.
    """
    try:
        fred = _fred_client()
        if start_date is None:
            start_date = (date.today() - timedelta(days=365)).isoformat()
        if end_date is None:
            end_date = date.today().isoformat()

        try:
            series_info = fred.get_series_info(series_id)
            df: pd.DataFrame = fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date,
            )
        except Exception as exc:
            if isinstance(exc, (KeyError, TypeError, ValueError)):
                raise
            raise ProviderError(str(exc)) from exc

        description = (
            series_info.get("title", series_id) if series_info is not None else series_id
        )
        if df.empty:
            return {
                "series_id": series_id,
                "description": str(description),
                "count": 0,
                "data": [],
                "stale_label": _stale_label(series_id),
            }

        data: list[dict[str, Any]] = []
        for idx, value in df.items():
            if pd.isna(value):
                continue
            data.append(
                {
                    "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                    "value": round(float(value), 4),
                }
            )

        return {
            "series_id": series_id,
            "description": str(description),
            "count": len(data),
            "latest_date": data[-1]["date"] if data else None,
            "latest_value": data[-1]["value"] if data else None,
            "data": data,
            "stale_label": _stale_label(series_id),
        }
    except RuntimeError as exc:
        return {"error": str(exc)}
    except ProviderError as exc:
        return {"error": f"Failed to fetch series {series_id}: {exc}"}


def get_macro_latest(series_ids: list[str]) -> MacroLatestResult:
    """Fetch the latest observation for each FRED series.

    Args:
        series_ids: List of FRED series identifiers.

    Returns:
        Dict mapping each series_id to its latest value and metadata.
    """
    try:
        fred = _fred_client()
        results: dict[str, Any] = {}
        for sid in series_ids:
            try:
                try:
                    series_info = fred.get_series_info(sid)
                    df = fred.get_series(sid, sort_order="desc").head(1)
                except Exception as exc:
                    if isinstance(exc, (KeyError, TypeError, ValueError)):
                        raise
                    raise ProviderError(str(exc)) from exc
                description = (
                    series_info.get("title", sid) if series_info is not None else sid
                )
                last_updated = (
                    series_info.get("last_updated", None) if series_info is not None else None
                )
                if df.empty:
                    results[sid] = {
                        "description": str(description),
                        "value": None,
                        "date": None,
                        "last_updated": str(last_updated) if last_updated else None,
                    }
                else:
                    idx = df.index[0]
                    results[sid] = {
                        "description": str(description),
                        "value": round(float(df.iloc[0]), 4),
                        "date": idx.isoformat() if hasattr(idx, "isoformat") else str(idx),
                        "last_updated": str(last_updated) if last_updated else None,
                    }
            except ProviderError as exc:
                results[sid] = {"error": str(exc)}

        return {
            "results": results,
            "stale_label": "⚠️ FRED macro data is delayed and revised. Do not treat as real-time.",
            "fetched_at": datetime.now().isoformat(),
        }
    except RuntimeError as exc:
        return {"error": str(exc)}
    except ProviderError as exc:
        return {"error": f"Failed to fetch macro latest: {exc}"}


def get_macro_snapshot() -> MacroSnapshotResult:
    """Fetch latest values for key macro risk indicators.

    Returns a snapshot of the 10 candidate series defined in MACRO_SNAPSHOT_SERIES.
    """
    series_ids = list(MACRO_SNAPSHOT_SERIES.keys())
    latest = get_macro_latest(series_ids)

    enriched: dict[str, Any] = {}
    for sid, info in MACRO_SNAPSHOT_SERIES.items():
        entry = latest.get("results", {}).get(sid, {})
        enriched[sid] = {
            "label": info,
            "value": entry.get("value"),
            "date": entry.get("date"),
            "last_updated": entry.get("last_updated"),
            "error": entry.get("error"),
        }

    return {
        "snapshot": enriched,
        "stale_label": "⚠️ FRED macro data is delayed and revised. Do not treat as real-time.",
        "fetched_at": latest.get("fetched_at", datetime.now().isoformat()),
    }



