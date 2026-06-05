from risk_radar_mcp.symbols import normalize_symbol


def test_normalize_symbol_aliases() -> None:
    assert normalize_symbol("btc") == "BTC-USD"
    assert normalize_symbol("QQQ") == "QQQ"
    assert normalize_symbol("us10y") == "^TNX"
    assert normalize_symbol("005930") == "005930.KS"


def test_normalize_symbol_rejects_empty() -> None:
    try:
        normalize_symbol(" ")
    except ValueError as exc:
        assert "symbol must not be empty" in str(exc)
    else:
        raise AssertionError("expected ValueError")
