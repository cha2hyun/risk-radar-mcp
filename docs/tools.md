# Tools

## get_quote

Returns the latest available quote from yfinance.

```json
{"symbol": "btc"}
```

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
