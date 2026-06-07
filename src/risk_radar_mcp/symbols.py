"""Symbol normalization and default market snapshot universe."""

import os

DEFAULT_EXCHANGE_SUFFIX = os.getenv("RISK_RADAR_DEFAULT_EXCHANGE", ".KS")

ALIASES: dict[str, str] = {
    "btc": "BTC-USD",
    "bitcoin": "BTC-USD",
    "eth": "ETH-USD",
    "ethereum": "ETH-USD",
    "qqq": "QQQ",
    "tqqq": "TQQQ",
    "spy": "SPY",
    "nasdaq": "^IXIC",
    "ixic": "^IXIC",
    "ndx": "^NDX",
    "vix": "^VIX",
    "dxy": "DX-Y.NYB",
    "dollar": "DX-Y.NYB",
    "us10y": "^TNX",
    "tnx": "^TNX",
    "gold": "GC=F",
    "oil": "CL=F",
    "wti": "CL=F",
    "usdkrw": "KRW=X",
    "krw": "KRW=X",
}

MARKET_SNAPSHOT_SYMBOLS: dict[str, str] = {
    "btc": "BTC-USD",
    "eth": "ETH-USD",
    "qqq": "QQQ",
    "tqqq": "TQQQ",
    "nasdaq": "^IXIC",
    "ndx": "^NDX",
    "vix": "^VIX",
    "dxy": "DX-Y.NYB",
    "us10y": "^TNX",
    "gold": "GC=F",
    "oil": "CL=F",
    "usdkrw": "KRW=X",
}


def normalize_symbol(symbol: str) -> str:
    """Normalize user-facing aliases to Yahoo Finance symbols."""

    value = symbol.strip()
    if not value:
        raise ValueError("symbol must not be empty")
    alias = ALIASES.get(value.lower())
    if alias:
        return alias
    if len(value) == 6 and value.isdigit():
        return f"{value}{DEFAULT_EXCHANGE_SUFFIX}"
    return value.upper()
