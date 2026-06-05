FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV RISK_RADAR_HOST=0.0.0.0
ENV RISK_RADAR_PORT=8765

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir uv
RUN uv sync --no-dev

EXPOSE 8765

CMD ["uv", "run", "--no-dev", "risk-radar-mcp"]
