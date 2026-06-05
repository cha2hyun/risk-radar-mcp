"""Technical indicator helpers built on pandas."""

from __future__ import annotations

import pandas as pd


def _series(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df:
        raise ValueError(f"missing column: {name}")
    return pd.to_numeric(df[name], errors="coerce")


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of an OHLCV dataframe with common indicators."""

    out = df.copy()
    close = _series(out, "Close")
    high = _series(out, "High")
    low = _series(out, "Low")
    volume = _series(out, "Volume")

    for window in (20, 50, 100, 200):
        out[f"sma_{window}"] = close.rolling(window).mean()
        out[f"ema_{window}"] = close.ewm(span=window, adjust=False).mean()

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    out["rsi_14"] = 100 - (100 / (1 + rs))

    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    out["macd"] = ema_12 - ema_26
    out["macd_signal"] = out["macd"].ewm(span=9, adjust=False).mean()
    out["macd_hist"] = out["macd"] - out["macd_signal"]

    sma_20 = close.rolling(20).mean()
    std_20 = close.rolling(20).std()
    out["bb_mid"] = sma_20
    out["bb_upper"] = sma_20 + (std_20 * 2)
    out["bb_lower"] = sma_20 - (std_20 * 2)

    prev_close = close.shift(1)
    tr = pd.concat(
        [
            high - low,
            (high - prev_close).abs(),
            (low - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    out["atr_14"] = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()

    direction = close.diff().apply(lambda value: 1 if value > 0 else -1 if value < 0 else 0)
    out["obv"] = (volume * direction).fillna(0).cumsum()

    return out


def latest_indicator_snapshot(df: pd.DataFrame) -> dict[str, float | str | None]:
    """Return the latest row as a JSON-friendly indicator snapshot."""

    enriched = add_indicators(df)
    latest = enriched.dropna(how="all").tail(1)
    if latest.empty:
        return {}
    row = latest.iloc[0]
    result: dict[str, float | str | None] = {}
    for key, value in row.items():
        if pd.isna(value):
            result[str(key)] = None
        elif hasattr(value, "isoformat"):
            result[str(key)] = value.isoformat()
        else:
            result[str(key)] = float(value) if isinstance(value, (int, float)) else str(value)
    return result
