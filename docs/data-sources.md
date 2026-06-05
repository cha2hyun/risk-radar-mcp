# Data Sources

## V1

V1 uses `yfinance`, which accesses Yahoo Finance data.

Caveats:

- Yahoo Finance/yfinance is not an official exchange data feed.
- Data may be delayed, incomplete, inaccurate, revised, or unavailable.
- Use for informational and research workflows only.

## V1.5 Planned

FRED official macro data.

Expected caveats:

- Macro data is often monthly, weekly, or daily, not real-time.
- Macro releases can be revised.
- Values should be displayed with release dates.

## V2 Planned

Korea market data.

Expected caveats:

- Investor flow availability depends on source.
- If KIS is used, only market-data endpoints should be exposed.
- Broker, account, balance, or trade endpoints must not be exposed.
