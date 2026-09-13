# Quickstart: Validating Release Notes & PR Summary Generation

A runnable validation guide proving the feature works end-to-end, mapped to
the three user stories in spec.md. Full CLI contract:
[contracts/cli-interface.md](./contracts/cli-interface.md). Entity details:
[data-model.md](./data-model.md).

## Prerequisites

- Python 3.11+
- A GitHub repository you can read (and, for the publish scenario, create
  releases on)
- A GitHub personal access token and an Anthropic API key

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

cat > .env <<'EOF'
GITHUB_TOKEN=ghp_...
ANTHROPIC_API_KEY=sk-ant-...
EOF
```

(`.env` is already git-ignored per the project constitution's Secrets Never
Committed principle.)

## Scenario 1 — Date range (User Story 1, P1)

```bash
ai-release-notes --repo <owner>/<name> --since 2026-08-01 --until 2026-08-31
```

**Expected**: `RELEASE_NOTES.md` is created containing a customer-facing,
categorized summary of pull requests merged in August 2026, plus a printed
cost summary (tokens + estimated USD). Re-running with the same range
produces no duplicate entries for PRs already reported (FR-016).

## Scenario 2 — No PRs in range

```bash
ai-release-notes --repo <owner>/<name> --since 2020-01-01 --until 2020-01-02
```

**Expected**: Exit code 0; a clear "no pull requests found in this window"
message; no misleading empty-looking summary file is produced as if changes
existed (FR-006).

## Scenario 3 — Reference/tag range (User Story 2, P2)

```bash
ai-release-notes --repo <owner>/<name> --from-ref v1.2.0 --to-ref v1.3.0
```

**Expected**: Same categorized output as Scenario 1, scoped to PRs merged
between the two refs. Using a ref that doesn't exist exits with code 1 and a
clear error naming the invalid ref.

## Scenario 4 — Publish as a release (User Story 3, P3)

```bash
ai-release-notes --repo <owner>/<name> --from-ref v1.2.0 --to-ref v1.3.0 --publish
```

**Expected**: A GitHub Release is created for the resolved Release Identity
(version/tag), with the header (release name, version, RC branch, commit
SHA) followed by the same categorized content.

**Then, run the identical command again**:

**Expected**: Exit code 0; local file is (re)written, but the tool reports
that notes already exist for this release and does **not** create or modify
any release (FR-012, FR-013) — verify by checking the release's "updated"
timestamp on GitHub is unchanged.

## Scenario 5 — Missing credentials

```bash
unset ANTHROPIC_API_KEY
ai-release-notes --repo <owner>/<name>
```

**Expected**: Exit code 1; a clear, actionable stderr message naming the
missing credential (FR-008) — no stack trace as the only output, and no
partial `RELEASE_NOTES.md` left behind.

## Verifying cost tracking

After any successful run, check that a new line was appended to
`logs/cost/runs/usage_log.jsonl` matching the schema in
[`logs/cost/runs/README.md`](../../logs/cost/runs/README.md), and that the
same tokens/cost were printed to stdout during the run (FR-007).
