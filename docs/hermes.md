# Hermes

Run `risk-radar-mcp` locally, then add it to a Hermes profile:

```bash
hermes -p hermes-investing mcp add risk-radar --url http://127.0.0.1:8765/mcp
hermes -p hermes-investing mcp test risk-radar
hermes -p hermes-investing gateway restart
```

Recommended usage:

- Use `risk-radar` before making current price, chart, indicator, or market snapshot claims.
- Treat all results as informational data, not trade instructions.
- Cross-check important market data if precision matters.
