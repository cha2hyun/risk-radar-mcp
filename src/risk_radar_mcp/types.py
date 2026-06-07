from typing import Any, TypedDict

class ErrorResult(TypedDict, total=False):
    error: str

class QuoteResult(TypedDict, total=False):
    symbol: str
    source: str
    last_price: Any
    previous_close: Any
    change: Any
    change_percent: Any
    open: Any
    high: Any
    low: Any
    volume: Any
    as_of: str
    metadata: dict[str, Any]
    input_symbol: str
    status: str
    error: str
    count: int
    items: Any
    note: str

class SnapshotResult(TypedDict, total=False):
    source: str
    items: dict[str, Any]
    note: str

class MacroLatestResult(TypedDict, total=False):
    results: dict[str, Any]
    stale_label: str
    fetched_at: str
    error: str

class MacroSeriesResult(TypedDict, total=False):
    series_id: str
    description: str
    count: int
    data: list[dict[str, Any]]
    stale_label: str
    latest_date: str | None
    latest_value: float | None
    error: str

class MacroSnapshotResult(TypedDict, total=False):
    snapshot: dict[str, Any]
    stale_label: str
    fetched_at: str
    error: str

class DashboardResult(TypedDict, total=False):
    market: Any
    macro: Any
    generated_at: str
    stale_label: str
    error: str
