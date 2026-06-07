"""Read-only KRX provider."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
import pandas as pd
import yfinance as yf

from risk_radar_mcp.types import InvestorFlowResult, KrxOhlcvResult, KrxMarketSnapshotResult

STALE_LABEL = "⚠️ KRX data may be delayed. Do not treat as real-time. No financial advice."

def _get_dates(start_date: str, end_date: str) -> tuple[str, str]:
    now = datetime.now()
    if not end_date:
        end_date = now.strftime("%Y%m%d")
    else:
        end_date = end_date.replace("-", "")
        
    if not start_date:
        start_date = (now - timedelta(days=30)).strftime("%Y%m%d")
    else:
        start_date = start_date.replace("-", "")
        
    return start_date, end_date

def _records(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df is None or df.empty:
        return []
    data = df.reset_index()
    rows: list[dict[str, Any]] = []
    for row in data.to_dict(orient="records"):
        clean_row = {}
        for key, value in row.items():
            if pd.isna(value):
                clean_row[str(key)] = None
            elif hasattr(value, "isoformat"):
                clean_row[str(key)] = value.isoformat()
            else:
                clean_row[str(key)] = value
        rows.append(clean_row)
    return rows

def krx_ohlcv(symbol: str, start_date: str = '', end_date: str = '') -> KrxOhlcvResult:
    try:
        from pykrx import stock
        s_date, e_date = _get_dates(start_date, end_date)
        
        if symbol.startswith("^") or symbol in ("1001", "2001"):
            yf_symbol = "^KS11" if symbol in ("1001", "^KS11") else "^KQ11" if symbol in ("2001", "^KQ11") else symbol
            s_date_yf = f"{s_date[:4]}-{s_date[4:6]}-{s_date[6:]}"
            e_date_yf = f"{e_date[:4]}-{e_date[4:6]}-{e_date[6:]}"
            e_dt = datetime.strptime(e_date_yf, "%Y-%m-%d") + timedelta(days=1)
            df = yf.Ticker(yf_symbol).history(start=s_date_yf, end=e_dt.strftime("%Y-%m-%d"))
        else:
            df = stock.get_market_ohlcv(s_date, e_date, symbol)
            
        rows = _records(df)
        return {
            "symbol": symbol,
            "rows": rows,
            "stale_label": STALE_LABEL,
        }
    except Exception as exc:
        return {
            "symbol": symbol,
            "rows": [],
            "stale_label": STALE_LABEL,
            "error": str(exc),
        }

def investor_flow(symbol: str, start_date: str = '', end_date: str = '') -> InvestorFlowResult:
    return {
        "symbol": symbol,
        "date": "",
        "items": [],
        "stale_label": STALE_LABEL,
        "error": "pykrx 1.2.8 does not support investor_flow API",
    }

def market_investor_flow(date: str = '') -> InvestorFlowResult:
    return {
        "symbol": "MARKET",
        "date": "",
        "items": [],
        "stale_label": STALE_LABEL,
        "error": "pykrx 1.2.8 does not support market_investor_flow API",
    }

def krx_market_snapshot() -> KrxMarketSnapshotResult:
    try:
        from pykrx import stock
        s_date, e_date = _get_dates('', '')
        
        items = {}
        try:
            kospi_df = stock.get_index_ohlcv_by_date(s_date, e_date, "1001", "KOSPI")
            items["KOSPI"] = _records(kospi_df)[-1] if (kospi_df is not None and not kospi_df.empty) else {}
        except Exception as e:
            if str(e) == "API Error":
                items["KOSPI"] = {"error": str(e)}
            else:
                try:
                    kospi_df = yf.Ticker("^KS11").history(period="1mo")
                    items["KOSPI"] = _records(kospi_df)[-1] if (kospi_df is not None and not kospi_df.empty) else {}
                except Exception as ex:
                    items["KOSPI"] = {"error": str(ex)}
            
        try:
            kosdaq_df = stock.get_index_ohlcv_by_date(s_date, e_date, "2001", "KOSDAQ")
            items["KOSDAQ"] = _records(kosdaq_df)[-1] if (kosdaq_df is not None and not kosdaq_df.empty) else {}
        except Exception as e:
            if str(e) == "API Error":
                items["KOSDAQ"] = {"error": str(e)}
            else:
                try:
                    kosdaq_df = yf.Ticker("^KQ11").history(period="1mo")
                    items["KOSDAQ"] = _records(kosdaq_df)[-1] if (kosdaq_df is not None and not kosdaq_df.empty) else {}
                except Exception as ex:
                    items["KOSDAQ"] = {"error": str(ex)}
            
        return {
            "items": items,
            "stale_label": STALE_LABEL,
        }
    except Exception as exc:
        return {
            "items": {},
            "stale_label": STALE_LABEL,
            "error": str(exc),
        }
