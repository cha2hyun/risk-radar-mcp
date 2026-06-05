# risk-radar-mcp

Read-only MCP server for market quotes, technical indicators, macro data, and risk-on/off snapshots.

`risk-radar-mcp` is designed for AI agents that need lightweight market context without broker access or trade execution. It focuses on BTC, Nasdaq, volatility, dollar, rates, commodities, and macro-risk proxies.

## Features

- Yahoo Finance/yfinance quote lookup
- OHLCV history
- Technical indicators: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV
- BTC/Nasdaq risk snapshot
- Basic ticker news
- Local HTTP MCP runtime
- Docker-friendly and `uv`-friendly

## Safety

This project is read-only.

- No trading
- No broker login
- No account access
- No portfolio management
- No financial advice

Market data may be delayed, incomplete, inaccurate, or unavailable. Use this project for research and informational workflows only.

## Quick Start

Install dependencies with `uv`:

```bash
uv sync
uv run risk-radar-mcp
```

The default HTTP MCP endpoint is:

```txt
http://127.0.0.1:8765/mcp
```

Docker:

```bash
docker build -t risk-radar-mcp .
docker run --rm -p 8765:8765 risk-radar-mcp
```

## Tools

- `get_quote(symbol)`
- `get_ohlcv(symbol, period, interval, limit)`
- `get_indicators(symbol, period, interval)`
- `get_market_snapshot()`
- `get_news(symbol, limit)`

## Common Symbols

- `btc` -> `BTC-USD`
- `eth` -> `ETH-USD`
- `qqq` -> `QQQ`
- `tqqq` -> `TQQQ`
- `nasdaq` -> `^IXIC`
- `ndx` -> `^NDX`
- `vix` -> `^VIX`
- `dxy` -> `DX-Y.NYB`
- `us10y` -> `^TNX`
- `gold` -> `GC=F`
- `oil` -> `CL=F`
- `usdkrw` -> `KRW=X`

## Roadmap

- V1: yfinance quotes, OHLCV, indicators, and market snapshot
- V1.5: optional FRED official macro data
- V2: Korea market data and investor flow where available

## License

MIT

---

# risk-radar-mcp 한국어

시장 현재가, 보조지표, 매크로 데이터, 리스크온/리스크오프 스냅샷을 제공하는 read-only MCP 서버입니다.

`risk-radar-mcp`는 브로커 계좌 접근이나 매매 실행 없이, AI 에이전트가 가벼운 시장 컨텍스트를 조회할 수 있도록 설계되었습니다. BTC, 나스닥, 변동성, 달러, 금리, 원자재, 매크로 리스크 프록시에 집중합니다.

## 기능

- Yahoo Finance/yfinance 기반 현재가 조회
- OHLCV 히스토리
- 보조지표: SMA, EMA, RSI, MACD, Bollinger Bands, ATR, OBV
- BTC/나스닥 리스크 스냅샷
- 기본 티커 뉴스
- 로컬 HTTP MCP 실행
- Docker 및 `uv` 기반 실행 지원

## 안전 원칙

이 프로젝트는 read-only입니다.

- 매매 실행 없음
- 브로커 로그인 없음
- 계좌 접근 없음
- 포트폴리오 관리 없음
- 투자 조언 아님

시장 데이터는 지연되거나, 누락되거나, 부정확하거나, 일시적으로 사용할 수 없을 수 있습니다. 연구 및 정보 확인 용도로만 사용하세요.

## 빠른 시작

`uv`로 의존성을 설치하고 실행합니다.

```bash
uv sync
uv run risk-radar-mcp
```

기본 HTTP MCP endpoint는 다음과 같습니다.

```txt
http://127.0.0.1:8765/mcp
```

Docker:

```bash
docker build -t risk-radar-mcp .
docker run --rm -p 8765:8765 risk-radar-mcp
```

## 도구

- `get_quote(symbol)`
- `get_ohlcv(symbol, period, interval, limit)`
- `get_indicators(symbol, period, interval)`
- `get_market_snapshot()`
- `get_news(symbol, limit)`

## 주요 심볼

- `btc` -> `BTC-USD`
- `eth` -> `ETH-USD`
- `qqq` -> `QQQ`
- `tqqq` -> `TQQQ`
- `nasdaq` -> `^IXIC`
- `ndx` -> `^NDX`
- `vix` -> `^VIX`
- `dxy` -> `DX-Y.NYB`
- `us10y` -> `^TNX`
- `gold` -> `GC=F`
- `oil` -> `CL=F`
- `usdkrw` -> `KRW=X`

## 로드맵

- V1: yfinance 현재가, OHLCV, 보조지표, 시장 스냅샷
- V1.5: 선택적 FRED 공식 매크로 데이터
- V2: 가능한 범위의 한국 시장 데이터 및 투자자 수급

## 라이선스

MIT
