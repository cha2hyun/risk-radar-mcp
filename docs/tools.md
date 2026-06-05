# Tools

## get_quote

Returns the latest available quote from yfinance.

```json
{"symbol": "btc"}
```

## get_quotes

Returns latest available quotes for multiple symbols in one batched yfinance request.

```json
{"symbols": ["btc", "qqq", "vix", "005930", "TQQQ"]}
```

Numeric six-digit Korean tickers are normalized to Yahoo Finance KOSPI symbols by default,
for example `005930` becomes `005930.KS`.

## value_positions

Estimates live market value and unrealized P/L for a list of positions.

```json
{
  "valuation_currency": "KRW",
  "positions": [
    {
      "account_id": "toss_main",
      "account_name": "Toss Main",
      "name": "Samsung Electronics",
      "ticker": "005930",
      "quantity": 25,
      "currency": "KRW",
      "cost_basis_snapshot": 6795655
    },
    {
      "account_id": "toss_main",
      "account_name": "Toss Main",
      "name": "TQQQ",
      "ticker": "TQQQ",
      "quantity": 4,
      "currency": "USD",
      "cost_basis_snapshot_krw": 512013
    }
  ]
}
```

Supported cost-basis fields:

- `cost_basis_snapshot`
- `avg_cost_per_share`
- `cost_basis_snapshot_krw`
- `avg_cost_per_share_krw`

Only `KRW` valuation totals are currently supported. USD positions are converted with `KRW=X`.

## get_ohlcv

Returns OHLCV records.

```json
{"symbol": "qqq", "period": "6mo", "interval": "1d", "limit": 120}
```

## get_indicators

Returns OHLCV records enriched with common technical indicators.

```json
{"symbol": "btc", "period": "1y", "interval": "1d"}
```

## get_market_snapshot

Returns the default BTC/Nasdaq/risk dashboard universe.

## get_news

Returns basic Yahoo Finance news for a ticker.

```json
{"symbol": "tqqq", "limit": 10}
```
