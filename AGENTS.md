# risk-radar-mcp

## Ownership

- Domain owner: `hermes-investing`
- Implementation orchestrator: `hermes-coding`
- Repository: `/Users/agent/code/risk-radar-mcp`

## Coding Policy

- Use Codex CLI for source-code changes.
- Use Gemini CLI only when Codex CLI is unavailable due to quota, authentication, or rate limits.
- Preserve unrelated changes and review the diff before reporting completion.
- Do not commit, tag, release, or push unless the user explicitly requests it.

## Hard Boundaries

- Read-only market and risk data only.
- No trade execution, broker login, or account access.
- Do not commit secrets, tokens, private endpoints, `.env` files, or runtime logs.
- Do not modify portfolio holdings unless the user explicitly provides the change.

## Domain Context

- Roadmap: `/Users/agent/agent-workspace/profiles/investing/runbooks/risk-radar-mcp-roadmap.md`
- Portfolio source: `/Users/agent/agent-workspace/profiles/investing/data/portfolio.yaml`
