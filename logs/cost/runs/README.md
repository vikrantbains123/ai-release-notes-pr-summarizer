# Runs Log

Tracks the cost of *running* the tool itself — i.e. the Anthropic API token
usage each time the CLI generates release notes or PR summaries. For the cost
of building this project with Claude Code, see
[../build/BUILD_LOG.md](../build/BUILD_LOG.md).

## Format

Each run appends one JSON line to `usage_log.jsonl` (created automatically on
first run; not committed to the repo — see `.gitignore`):

```json
{"timestamp": "2026-09-12T10:00:00Z", "repo": "owner/name", "since": "2026-09-01", "until": "2026-09-12", "model": "claude-...", "input_tokens": 12450, "output_tokens": 890, "estimated_cost_usd": 0.04}
```

| Field                | Meaning                                              |
|-----------------------|-------------------------------------------------------|
| `timestamp`           | UTC time the run finished                             |
| `repo`                | GitHub repo the run summarized                        |
| `since` / `until`     | The date window passed to the CLI                     |
| `model`               | Claude model used                                     |
| `input_tokens`        | Total input tokens across all API calls in the run    |
| `output_tokens`       | Total output tokens across all API calls in the run   |
| `estimated_cost_usd`  | Computed from the model's published per-token pricing |

This file is a placeholder for now — the CLI will write to
`usage_log.jsonl` once the cost-tracking feature is implemented.
