# Docker

Build:

```bash
docker build -t risk-radar-mcp .
```

Run:

```bash
docker run --rm -p 8765:8765 risk-radar-mcp
```

Endpoint:

```txt
http://127.0.0.1:8765/mcp
```

Runtime environment:

```bash
docker run --rm \
  -e RISK_RADAR_HOST=0.0.0.0 \
  -e RISK_RADAR_PORT=8765 \
  -p 8765:8765 \
  risk-radar-mcp
```
