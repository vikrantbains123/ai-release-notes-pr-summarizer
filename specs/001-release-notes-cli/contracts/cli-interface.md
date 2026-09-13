# CLI Interface Contract: Release Notes & PR Summary Generation

This is the tool's only user-facing interface — one command, documented here
as its contract for `/speckit-tasks` and `/speckit-implement` to build
against. Flag names are illustrative of the required inputs/outputs from
spec.md; exact spelling may be finalized during implementation without
changing this contract's meaning.

## Command

```text
ai-release-notes --repo <owner/name> [window options] [output options] [--publish]
```

## Window options (mutually exclusive; FR-001, FR-015)

| Flag | Required | Notes |
|---|---|---|
| `--since <date> --until <date>` | No | Explicit date range |
| `--from-ref <ref> --to-ref <ref>` | No | Explicit reference/tag pair |
| *(none)* | — | Defaults to the last 1 month ending now (FR-015) |

Supplying both a date range and a ref pair is a usage error (exit code 2,
message naming the conflict) — resolved before any network call is made.

## Output options

| Flag | Required | Default | Notes |
|---|---|---|---|
| `--output <path>` | No | `RELEASE_NOTES.md` | Destination for the local Markdown file (FR-004, FR-010) |
| `--publish` | No | off | Opt-in to also publish as a GitHub Release (FR-005) |

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success — includes the "no PRs found" case (FR-006) and the "notes already exist, skipped" case (FR-013); both are successful, reported outcomes, not errors |
| 1 | Runtime failure: invalid/missing credentials (FR-008), AI call failed after retries (FR-014), PR volume exceeds the 300-PR cap (FR-017), invalid ref (User Story 2 Acceptance Scenario 2), or generation succeeded but `--publish` failed (FR-018) — this last cause is reported distinctly from the others (see File output contract below) |
| 2 | Usage error: conflicting/invalid CLI arguments |

## Stdout/stderr contract

- Human-readable progress and the final cost summary (FR-007) go to **stdout**.
- Errors (exit codes 1 and 2) go to **stderr** with a clear, actionable
  message (FR-008) — never a raw stack trace as the only output.
- No credential value ever appears in stdout, stderr, or the generated file
  (FR-009).

## File output contract

- On success, `<output path>` is written containing the Generated Summary
  (header + customer-facing categories + de-emphasized internal section),
  per data-model.md.
- On the "notes already exist for this release" outcome (FR-012/FR-013), the
  local file is still (re)written — immutability applies to the *published
  release*, not the local file (see spec Clarifications) — but nothing is
  published.
- On an exit-code-1 failure *other than* FR-018's case, no local file is
  written or left partially written (SC-007) and no release is created or
  modified.
- On the FR-018 case specifically (generation succeeded, `--publish` then
  failed), the local file — already written successfully — is left in place
  as valid output; only the release is not created or modified. This is the
  one exit-code-1 outcome where a local file legitimately remains.

## Configuration contract (not CLI flags — env vars / `.env`, FR-009)

| Variable | Required | Purpose |
|---|---|---|
| `GITHUB_TOKEN` | Yes | Read access always; write/release access only needed when `--publish` is used |
| `ANTHROPIC_API_KEY` | Yes | Claude API access |

Missing or invalid values fail fast with exit code 1 before any GitHub or
Anthropic call is attempted.
