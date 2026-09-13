# Implementation Log: Release Notes & PR Summary Generation

Tracks `tasks.md`'s 34 tasks in execution order, mapped to user story and the
file(s) each one touches, plus the token/dollar cost of *building* each task
with Claude Code. This is a per-task drill-down of
[../../logs/cost/build/BUILD_LOG.md](../../logs/cost/build/BUILD_LOG.md),
which tracks cost at the milestone level across the whole project; this file
tracks it at the task level for this one feature.

**How to fill in Tokens/Est. Cost**: run `/cost` in the Claude Code terminal
right after a task (or small batch of tasks) is implemented and its tests
pass, then record the delta since the previous row.

| Order | Phase | Story | Task | What it does | File(s) touched | Tokens | Est. Cost |
|---|---|---|---|---|---|---|---|
| 1 | Setup | — | T001 | Create package + test dir skeleton | `src/ai_release_notes/` (new), `tests/{unit,integration,contract}/` (new) | | |
| 2 | Setup | — | T002 | Project metadata, entry point, deps | `pyproject.toml` | | |
| 3 | Setup | — | T003 | Document required env vars | `.env.example` | | |
| 4 | Foundational | — | T004 | Shared mock fixtures (GitHub + Anthropic) | `tests/conftest.py` | | |
| 5 | Foundational | — | T005 | Test: credential loading | `tests/unit/test_config.py` | | |
| 6 | Foundational | — | T006 | Impl: credential loading | `src/ai_release_notes/config.py` | | |
| 7 | Foundational | — | T007 | Test: time window resolution | `tests/unit/test_window.py` | | |
| 8 | Foundational | — | T008 | Impl: time window resolution | `src/ai_release_notes/window.py` | | |
| 9 | Foundational | — | T009 | Test: dedup history | `tests/unit/test_history.py` | | |
| 10 | Foundational | — | T010 | Impl: dedup history | `src/ai_release_notes/history.py` | | |
| 11 | Foundational | — | T011 | Test: release identity matching | `tests/unit/test_release_identity.py` | | |
| 12 | Foundational | — | T012 | Impl: release identity matching | `src/ai_release_notes/release_identity.py` | | |
| 13 | Foundational | — | T013 | Test: cost calc + no credential leak | `tests/unit/test_cost.py` | | |
| 14 | Foundational | — | T014 | Impl: cost calc + usage log writer | `src/ai_release_notes/cost.py` | | |
| 15 | Foundational | — | T015 | Test: Markdown rendering | `tests/unit/test_render.py` | | |
| 16 | Foundational | — | T016 | Impl: Markdown rendering | `src/ai_release_notes/render.py` | | |
| 17 | Foundational | — | T017 | Test: PR fetch + 300-cap + auth-header scrubbing | `tests/integration/test_github_client.py` | | |
| 18 | Foundational | — | T018 | Impl: PR fetch + cap check + scrubbing | `src/ai_release_notes/github_client.py` | | |
| **Checkpoint** | | | | Foundation complete — every module independently tested | | | |
| 19 | US1 (P1) | US1 | T019 | Test: summarizer + retry/backoff | `tests/integration/test_summarizer.py` | | |
| 20 | US1 | US1 | T020 | Impl: summarizer + retry/backoff | `src/ai_release_notes/summarizer.py` | | |
| 21 | US1 | US1 | T021 | Test: base CLI contract (date range) | `tests/contract/test_cli_date_range.py` | | |
| 22 | US1 | US1 | T022 | Impl: CLI entry point + date-range flags | `src/ai_release_notes/cli.py` | | |
| 23 | US1 | US1 | T023 | Wire dedup-history recording into the run | `src/ai_release_notes/cli.py` (extends T022) | | |
| **Checkpoint** | | | | MVP — date-range summaries work end-to-end | | | |
| 24 | US2 (P2) | US2 | T024 | Test: ref-pair resolution | `tests/integration/test_github_client.py` (extends T017) | | |
| 25 | US2 | US2 | T025 | Impl: ref-pair resolution | `src/ai_release_notes/github_client.py` (extends T018) | | |
| 26 | US2 | US2 | T026 | Test: ref-pair CLI contract | `tests/contract/test_cli_ref_range.py` | | |
| 27 | US2 | US2 | T027 | Impl: `--from-ref`/`--to-ref` flags | `src/ai_release_notes/cli.py` (extends T022) | | |
| **Checkpoint** | | | | US1 + US2 both independently functional | | | |
| 28 | US3 (P3) | US3 | T028 | Test: release check/create + publish-failure error | `tests/integration/test_github_client.py` (extends T017/T024) | | |
| 29 | US3 | US3 | T029 | Impl: release check/create | `src/ai_release_notes/github_client.py` (extends T018/T025) | | |
| 30 | US3 | US3 | T030 | Test: `--publish` CLI contract | `tests/contract/test_cli_publish.py` | | |
| 31 | US3 | US3 | T031 | Impl: `--publish` flag wiring | `src/ai_release_notes/cli.py` (extends T022/T027) | | |
| **Checkpoint** | | | | All 3 user stories independently functional | | | |
| 32 | Polish | — | T032 | Manual quickstart run (incl. SC-006 check) | *(verification only — see logs/cost/build/BUILD_LOG.md, logs/cost/runs/usage_log.jsonl)* | | |
| 33 | Polish | — | T033 | Real usage docs | `README.md` | | |
| 34 | Polish | — | T034 | Full-suite constitution compliance check | *(verification only)* | | |

## Notes

- Tokens/Est. Cost are for the cost of *building* each task with Claude Code
  (development-time cost) — not to be confused with the tool's own runtime
  cost-per-run, which is what `logs/cost/runs/usage_log.jsonl` tracks once
  the tool exists and is actually invoked.
- Rows are blank until each task is implemented; fill them in as
  `/speckit-implement` (or manual implementation) progresses through
  `tasks.md`.
