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
            try:
                idx_sym = "1001" if symbol == "^KS11" else "2001" if symbol == "^KQ11" else symbol.replace("^", "")
                df = stock.get_index_ohlcv(s_date, e_date, idx_sym)
            except Exception as e:
                raise Exception(f"get_index_ohlcv failed: {e}. Fallback to yfinance provider for index tickers (e.g., ^KS11).")
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
    try:
        from pykrx import stock
        s_date, e_date = _get_dates(start_date, end_date)
        df = stock.get_market_trading_value_by_investor(s_date, e_date, symbol)
        return {
            "symbol": symbol,
            "date": f"{s_date}-{e_date}",
            "items": _records(df),
            "stale_label": STALE_LABEL,
        }
    except Exception as exc:
        return {
            "symbol": symbol,
            "date": "",
            "items": [],
            "stale_label": STALE_LABEL,
            "error": f"pykrx investor flow API broken in 1.2.8: {exc}",
        }

def market_investor_flow(date: str = '') -> InvestorFlowResult:
    try:
        from pykrx import stock
        s_date, e_date = _get_dates(date, date)
        
        if hasattr(stock, "get_market_net_purchases_of_equities_by_investor"):
            method = stock.get_market_net_purchases_of_equities_by_investor
        else:
            method = stock.get_market_net_purchases_of_equities
            
        # KOSPI
        df_kospi = method(s_date, e_date, "KOSPI", "ALL")
        items_kospi = _records(df_kospi) if df_kospi is not None else []
        for item in items_kospi:
            item["market"] = "KOSPI"
            
        # KOSDAQ
        df_kosdaq = method(s_date, e_date, "KOSDAQ", "ALL")
        items_kosdaq = _records(df_kosdaq) if df_kosdaq is not None else []
        for item in items_kosdaq:
            item["market"] = "KOSDAQ"
            
        items = items_kospi + items_kosdaq
        
        return {
            "symbol": "MARKET",
            "date": s_date,
            "items": items,
            "stale_label": STALE_LABEL,
        }
    except Exception as exc:
        return {
            "symbol": "MARKET",
            "date": "",
            "items": [],
            "stale_label": STALE_LABEL,
            "error": str(exc),
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
