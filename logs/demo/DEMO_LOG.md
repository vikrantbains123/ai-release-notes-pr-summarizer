# Demo Log

A chronological, plain-language record of how this project was built —
decisions made, why, and what was done — kept as raw material for a later
demo video or slide deck. Entries are added as the project progresses;
reorganize/trim into a script or slides whenever you're ready.

For token/dollar cost tracking (separate concern), see
[../cost/build/BUILD_LOG.md](../cost/build/BUILD_LOG.md) (cost of building)
and [../cost/runs/README.md](../cost/runs/README.md) (cost of running the tool).

**On the timestamps below:** entries that produced a file or directory use
that file's actual filesystem creation time (real, to the minute). Entries
that were pure discussion with no artifact created at the time (the earliest
ones, before the repo existed) are marked *(approx.)* and estimated from
session start — precise enough to see pacing, not precise to the second.

---

## 2026-09-12, ~16:32 PDT (approx.) — Project kickoff and idea

Started a new project: a tool that uses AI to generate release notes and PR
summaries for a given window of time. Decided on the core shape through a
few quick decisions:

- **Data source:** GitHub only, via the GitHub API.
- **Language/runtime:** Python CLI.
- **LLM:** Anthropic Claude API.
- **Output:** writes a local Markdown file, with an optional flag to also
  publish/update a GitHub Release.

## 2026-09-12, ~16:40 PDT (approx.) — Choosing spec-driven development

Decided to build this using **spec-driven development** rather than jumping
straight to code — writing a spec and a plan first, then generating tasks,
then implementing from those tasks. Chose to use GitHub's **Spec Kit**
toolchain for this (slash commands like `/constitution`, `/specify`, `/plan`,
`/tasks`, `/implement`, run through Claude Code) rather than hand-rolled
markdown docs.

## 2026-09-12, ~16:50 PDT (approx.) — Creating the GitHub repository

Worked through the repo-creation form on GitHub together, choosing:

- **Name:** `ai-release-notes-pr-summarizer`
- **Description:** written to double as a portfolio signal — states what the
  tool does and names the stack (Python, Claude API) so it reads well in a
  list of repos, not just to someone who opens it.
- **Template:** none — GitHub's "choose a template" dropdown refers to
  *template repositories* (repos explicitly marked as reusable boilerplate),
  which didn't apply here; Spec Kit would scaffold the project structure
  instead.
- **Initialized with:** a README, a Python `.gitignore`, and an MIT license,
  all created directly on GitHub.

## 2026-09-12, 16:53 PDT — Cloning the repo locally

Cloned the new repo directly into the existing local project folder (rather
than into a new subfolder) since the folder was empty and git allows cloning
into an empty directory:

```bash
git clone https://github.com/vikrantbains123/ai-release-notes-pr-summarizer.git .
```

The trailing `.` targets the *current* directory instead of git's default of
creating a new subfolder named after the repo. Result: `origin` remote,
`main` branch, and the README/.gitignore/LICENSE from GitHub, all in place
locally with one existing commit ("Initial commit").

## 2026-09-12, 16:59–17:00 PDT — Setting up cost-tracking logs

Decided to track two separate kinds of cost, in one shared `logs/` folder:

1. **Cost of *building* the project** — this Claude Code session's own token
   usage/cost. Claude Code doesn't expose this to the assistant
   programmatically, so it's logged manually: run `/cost` in the terminal at
   a milestone and record the numbers.
2. **Cost of *running* the finished tool** — every Anthropic API response
   includes token usage, so the CLI will compute and report an estimated
   cost per run, and can append each run's numbers to a local log for
   cumulative totals over time.

Landed on this structure:

```
logs/
└── cost/
    ├── build/
    │   └── BUILD_LOG.md   # manual milestone entries: date, milestone, model, cost, tokens
    └── runs/
        └── README.md      # documents the usage_log.jsonl format the tool writes at runtime
```

`usage_log.jsonl` (the actual generated run data) is git-ignored — only the
README describing its format is tracked — since it's local runtime data that
will differ per machine, similar to any other `.log` file.

Also added a **Model** column to `BUILD_LOG.md` after realizing the Claude
Code model in use (e.g. Sonnet 5 vs. Opus) significantly affects cost and
wasn't otherwise captured per entry.

## 2026-09-12, 17:30 PDT — Adding this demo log

Added `logs/demo/DEMO_LOG.md` (this file) as a running, dated narrative of
the build — separate from the cost logs — specifically so it can be turned
into a demo video script or slide deck later, without having to reconstruct
the story from git history and conversation scrollback.

## 2026-09-12, 17:33 PDT — Adding real timestamps to this log

Went back and added a timestamp to every entry above, so gaps between steps
can be quantified later (useful for demo pacing). Timestamps for entries that
created a file/folder were pulled from that file's actual filesystem creation
time (`stat -f "%SB"`) rather than guessed; the handful of entries from before
any file existed (kickoff, choosing Spec Kit, creating the GitHub repo) are
marked *(approx.)* since no artifact exists to timestamp precisely. Going
forward, new entries get a real timestamp at the time they're written.

## 2026-09-12, 17:37 PDT — Installing GitHub Spec Kit

Ran Spec Kit's installer to scaffold the spec-driven workflow for Claude
Code:

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init --here --integration claude --force --non-interactive
```

(The CLI's flag turned out to be `--integration claude`, not `--ai claude`
as first tried — `specify init --help` clarified this after the first
attempt errored.)

This added:
- `.claude/skills/` — the `/speckit-*` slash commands themselves
  (`speckit-constitution`, `speckit-specify`, `speckit-plan`,
  `speckit-tasks`, `speckit-implement`, plus optional
  `speckit-clarify`/`speckit-analyze`/`speckit-checklist`).
- `.specify/` — templates (spec/plan/tasks/checklist), the constitution
  template, helper scripts, and Spec Kit's own bookkeeping.

Spec Kit's installer warned that agent folders can end up holding local
credentials, so added a targeted `.gitignore` rule for
`.claude/settings.local.json` specifically — not the whole `.claude/`
folder, since the skills themselves need to stay tracked so the workflow
is reproducible for anyone who clones the repo.

Next step: run `/speckit-constitution` to establish the project's guiding
principles, then `/speckit-specify` for the baseline spec.

## 2026-09-12, 17:43 PDT — Ratifying the project constitution

Ran `/speckit-constitution` (via the `speckit-constitution` skill installed
above) to write `.specify/memory/constitution.md`. Rather than let the
principles be invented automatically, first answered three questions about
testing rigor, whether cost-tracking should be a hard rule vs. just a
feature, and how many principles to keep — landing on a deliberately small
set (4) for a solo/learning project:

1. **Test-First Development (NON-NEGOTIABLE)** — tests before
   implementation, GitHub/Anthropic API calls mocked in tests (no live
   network calls in the suite).
2. **Cost Transparency** — every Anthropic API call must report tokens and
   estimated cost, and log to `logs/cost/runs/usage_log.jsonl`; ties
   directly into the cost-tracking logs already set up.
3. **Simplicity & CLI-First** — one command, one job; no speculative
   abstractions (plugin systems, multi-provider support) until an actual
   spec calls for them.
4. **Secrets Never Committed** — tokens via env vars / git-ignored `.env`
   only.

Ratified as version 1.0.0, dated 2026-09-12. Next step: `/speckit-specify`
to write the baseline feature spec.

## 2026-09-12, 18:01 PDT — Writing the baseline feature spec

Ran `/speckit-specify` with a detailed description of the tool's core
behavior (repo + time window in, categorized AI summary out, optional
GitHub Release publish, cost reporting per the constitution). This is the
first feature, so it became `specs/001-release-notes-cli/spec.md`.

The spec deliberately stays at the WHAT/WHY level — no mention of Python,
Claude, or the GitHub REST API by name — since Spec Kit's model is that a
spec describes user-facing behavior and requirements, while HOW gets
decided in `/speckit-plan`. It's organized as three independently-testable
user stories, prioritized:

- **P1 — Generate notes for a date range** (the actual MVP)
- **P2 — Generate notes between two release points/tags** (common
  real-world release workflow)
- **P3 — Publish the summary as a draft GitHub Release** (convenience
  layer on top of P1/P2)

Plus 10 functional requirements, edge cases, key entities, and 5 measurable
success criteria. No `[NEEDS CLARIFICATION]` markers were needed — used
reasonable defaults instead (documented under Assumptions), such as: only
merged PRs count, a single default category taxonomy, single-user v1 scope,
and re-running the tool for the same window updates the existing draft
release rather than duplicating it.

The spec passed its own quality checklist
(`specs/001-release-notes-cli/checklists/requirements.md`) on the first
pass. One assumption is flagged there as worth double-checking with
`/speckit-clarify` before planning: the re-run/duplicate-release behavior.

Next step: `/speckit-plan` (optionally `/speckit-clarify` first) to turn
this into a technical plan.

## 2026-09-12, 18:12 PDT — Revising the spec: customer-facing notes

Confirmed the re-run/duplicate-release assumption from the spec as-is, then
revised the spec to require that generated notes be **customer-facing and
non-technical** rather than a raw restatement of PR titles. This surfaced a
real design fork: what happens to purely internal/technical PRs (refactors,
dependency bumps, CI changes) that have no customer-visible impact? Asked —
decided to keep them, but grouped into a separate, de-emphasized
"Other/Internal Changes" section rather than omitting them or mixing them
into the customer-facing categories.

Updated `spec.md`: reworded User Story 1, added FR-003 (plain-language,
customer-facing summary) and FR-003a (internal PRs go in their own
de-emphasized section), added a new edge case and success criterion
(SC-006: a non-technical customer can read the main summary without
hitting jargon), and updated the Assumptions to spell out the category
split and that classification is done by the AI step itself — no manual
tagging required. Re-validated against the requirements checklist; still
passes.

## 2026-09-12, 18:44 PDT — Running /speckit-clarify

Ran `/speckit-clarify` — explicitly not skipping this optional step, per
your instruction to go through every step in the flow. Scanned the spec
against Spec Kit's full ambiguity taxonomy (scope, data model, UX flow,
non-functional attributes, integrations, edge cases, terminology,
completion signals) and asked about the 3 highest-impact gaps found. Five
clarifications landed, added to spec.md as a new `## Clarifications`
section plus FR-011 through FR-017:

1. **Release identity & immutability** — the earlier "update the existing
   draft on re-run" assumption was actually replaced here: releases are
   now matched by version/tag, every generated document must show a header
   with release name/version/RC branch/commit tag+SHA, and — the real
   change — once notes exist for a release they are **immutable**: a
   re-run does not update or duplicate them, it skips and clearly reports
   that nothing changed (FR-011, FR-012, FR-013). This took two rounds to
   pin down precisely since the first answer bundled a few different
   things together.
2. **AI failure handling** — retry a small fixed number of times with
   backoff, then abort cleanly with no partial/misleading output rather
   than ever half-publish something (FR-014).
3. **Default time window** — defaults to the last 1 month if the user
   doesn't specify one (FR-015; briefly discussed as 2 weeks before
   settling on 1 month).
4. **Cross-run deduplication** — a PR already covered by an earlier
   summary must never be reported again, even across overlapping windows
   (FR-016) — volunteered alongside the default-window answer, not
   something I'd explicitly asked about, but clearly important.
5. **PR volume cap** — a reasonable soft cap per window (e.g. a few
   hundred PRs); exceeding it is a clear error rather than silent
   truncation or batching across multiple AI calls (FR-017). Applied the
   recommended default here after two attempts to get a direct answer
   both went to other topics instead — flagged that choice explicitly
   rather than silently assuming it.

Also added two new Key Entities (**Release Identity**,
**Summarization History**) and two new success criteria (SC-007: failed
runs never leave partial output; SC-008: no PR ever reported twice across
overlapping windows). Re-validated the requirements checklist — still
passes all items.

Next step: `/speckit-plan`.

## 2026-09-12, 19:18 PDT — Running /speckit-plan

Ran `/speckit-plan`, turning the spec into a technical plan. This is the
first step where implementation-level decisions actually get made — the
spec deliberately stayed tech-agnostic, so this is where Python, specific
libraries, and file layout enter the picture, grounded in the constitution.

Produced, under `specs/001-release-notes-cli/`:

- **plan.md** — Technical Context (Python 3.11+, `anthropic` SDK,
  `requests`, `python-dotenv`, `argparse`, `pytest`+`unittest.mock`, all
  justified individually per Simplicity & CLI-First), a Constitution Check
  table (all 4 principles PASS, re-checked again after design), and a
  single-project module layout: `config`, `window`, `github_client`,
  `release_identity`, `history`, `summarizer`, `cost`, `render`, each
  mapped to one Key Entity or responsibility from the spec.
- **research.md** — one Decision/Rationale/Alternatives entry per
  implementation choice (9 total: GitHub client library, Anthropic SDK,
  CLI parsing, retry/backoff approach for FR-014, Summarization History
  storage, Release Identity matching mechanism for FR-012, cost
  calculation approach, config loading, test mocking strategy). Consistent
  theme: prefer stdlib/one well-justified dependency over adding a heavier
  library, per the constitution.
- **data-model.md** — the 6 Key Entities from the spec (Pull Request, Time
  Window, Release Identity, Generated Summary, Usage Record,
  Summarization History) with concrete fields and validation rules traced
  back to specific FRs, plus a relationship diagram.
- **contracts/cli-interface.md** — since this is a CLI tool, its "contract"
  is its command-line interface: flags, exit codes, stdout/stderr rules,
  file-output guarantees, and the env-var configuration contract.
- **quickstart.md** — 5 runnable validation scenarios, one per user story
  plus the no-PRs-found and missing-credentials edge cases, including how
  to verify the re-run/immutability behavior and the cost log by hand.

No unresolved `NEEDS CLARIFICATION` markers — the constitution had already
pinned down language/platform/AI-provider, so Phase 0 research only needed
to resolve concrete implementation patterns, not open questions.

Next step: `/speckit-tasks` to turn this plan into a dependency-ordered
task list — the last step before any code gets written.

## 2026-09-12, 19:22 PDT — Running /speckit-tasks

Ran `/speckit-tasks`, generating `specs/001-release-notes-cli/tasks.md` —
34 tasks (T001-T034) across 6 phases. This is the last artifact before any
code gets written.

Because the constitution's Test-First principle is NON-NEGOTIABLE, tests
are not optional here (the template's default) — every implementation task
is paired with a test task that must be written and confirmed failing
first. Shape of the plan:

- **Setup (T001-T003)**: package skeleton, `pyproject.toml`, `.env.example`.
- **Foundational (T004-T018, blocking)**: turned out larger than a typical
  "foundational" phase, because several requirements apply to *every* run,
  not one story — cost transparency (FR-007), the release-identity header
  (FR-011), and cross-run dedup (FR-016) all had to be shared modules
  rather than owned by a single user story. Covers `config`, `window`,
  `history`, `release_identity`, `cost`, `render`, and the PR-fetch path
  of `github_client`, each as a test-then-implementation pair, plus shared
  mock fixtures for GitHub/Anthropic (`conftest.py`).
- **User Story 1 / MVP (T019-T023)**: summarizer (with the FR-014 retry
  logic) + the base CLI wiring date-range runs end to end.
- **User Story 2 (T024-T027)**: ref-pair resolution, extending the CLI.
- **User Story 3 (T028-T031)**: release check/create, extending the CLI
  with `--publish` and the immutability behavior.
- **Polish (T032-T034)**: manual quickstart run, README, a final
  constitution-compliance sweep (no live network calls in tests, every
  Anthropic call path exercises cost.py).

Noted in the plan: because Foundational absorbed most of the shared logic,
US2 and US3 turned out independent of each other (both only extend US1's
`cli.py` skeleton) and can be built in parallel once US1 exists.

Next step: `/speckit-analyze` (optional — not skipping it) to cross-check
spec/plan/tasks for gaps before `/speckit-implement` actually writes code.

## 2026-09-12, 19:30 PDT — Running /speckit-checklist

Ran `/speckit-checklist` — the other optional step, not skipped per your
instruction. Important distinction learned here: this checklist is a "unit
test for English," not a test plan — every item questions whether the
*requirements themselves* are complete/clear/consistent (e.g. "is X
quantified?"), never whether the *implementation* works ("verify X
happens"). That's enforced strongly enough by the skill that it explicitly
lists banned phrasing like "Verify," "Test," "Confirm X happens."

Asked which of 3 risk areas to focus on (security/secrets, cost &
release-immutability, or the CLI contract) — chose all three combined
rather than picking one, at standard (solo pre-implementation gate) depth.

Wrote `specs/001-release-notes-cli/checklists/pre-implementation.md` —
19 items (CHK001-CHK019) across those three categories, all unchecked
(review ownership belongs to you, not to me generating the list). Several
items surfaced real gaps worth resolving before implementing, e.g.:

- FR-014's retry count/backoff schedule isn't actually quantified anywhere
  yet (CHK007).
- Whether "regenerate" in FR-012 could be misread to also block the local
  file, not just the published release (CHK011).
- What happens to a `--publish` run that fails after the local file is
  written but before publishing completes (CHK019).

Next step: `/speckit-analyze` to cross-check spec/plan/tasks consistency,
then decide whether to resolve these checklist gaps before
`/speckit-implement`.

## 2026-09-12, 19:33 PDT — Resolving the 3 checklist gaps

Resolved all three gaps flagged by the pre-implementation checklist,
directly in `spec.md` (a new Clarifications sub-session), then propagated
the changes to `tasks.md` and both checklists so nothing was left
inconsistent:

1. **FR-014 retry count (CHK007)** — was "a small, fixed number of times,"
   now concretely 3 attempts total with exponential backoff starting at
   2 seconds (2s, then 4s). Updated the T019/T020 task descriptions to
   match the concrete numbers.
2. **FR-012 scope (CHK011)** — clarified that publish-immutability applies
   only to the *published release*, never the local file, which always
   regenerates. This was a real ambiguity, not just a wording nitpick — a
   naive implementation could easily have skipped local file writes too.
3. **Partial-success case (CHK019)** — added **FR-018**: if the local file
   writes successfully but the subsequent publish call then fails, the
   file stays (it's valid, complete output) and the run exits with an
   error that clearly distinguishes "generation succeeded, publishing
   failed" rather than a generic failure. Updated T028-T031 (the US3
   publish tasks) to test and implement this explicitly — `github_client.py`
   now needs a distinguishable error type for publish failures.

Checked off CHK007/CHK011/CHK019 in `pre-implementation.md` with a
resolution note each; the other 16 items remain open for now (not asked
about yet). Also updated `checklists/requirements.md`'s notes for
traceability. `spec.md` now has FR-001 through FR-018 (18 functional
requirements total).

Still haven't run `/speckit-analyze` — that's next, before
`/speckit-implement`.

## 2026-09-12, 19:58 PDT — Running /speckit-analyze + remediation

Ran `/speckit-analyze` — strictly read-only, cross-checking spec.md,
plan.md, and tasks.md (plus research.md, data-model.md,
contracts/cli-interface.md) against each other and against the
constitution. Found 7 issues, **0 critical**, split HIGH/MEDIUM/LOW:

- **C1 (HIGH)** — FR-017 (the PR-volume cap) had **zero tasks** behind it
  anywhere in tasks.md, despite being clarified and named in plan.md. A
  real "we wrote a requirement and then forgot to build it" gap.
- **I1 (HIGH)** — contracts/cli-interface.md's File output contract
  directly contradicted the newly-added FR-018: it said no local file
  survives *any* exit-1 failure, which is exactly wrong for the
  publish-fails-after-generation-succeeds case. Classic artifact staleness
  — the contract was written before FR-018 existed and never revisited.
- **U1 (MEDIUM)** — FR-017's cap was still "a reasonable soft cap... e.g.
  a few hundred," never actually quantified, unlike FR-014 which went
  through the same tightening process.
- **I2 (MEDIUM)** — research.md's retry/backoff decision still described
  the old vague "small fixed retry count," stale relative to FR-014's
  later 3-attempts/2s-4s quantification.
- **C2 (MEDIUM)** — FR-009 (no credential exposure) was only tested on the
  config-loading side; nothing asserted the *outputs* (usage_log.jsonl,
  error messages) stay clean.
- **I3 (LOW)** — FR-009 itself was scoped only to "files," while
  contracts/cli-interface.md had already (correctly) extended the same
  guarantee to stdout/stderr — spec.md hadn't caught up to its own contract.
- **C3 (LOW)** — SC-006 (customer readability) had no task calling it out
  by name, only the general manual quickstart pass.

Asked for and got approval to apply all 7 fixes. Applied:

- **spec.md**: FR-017 → concrete 300-PR cap; FR-009 → widened to cover
  stdout/stderr; added a third Clarifications sub-session recording both
  decisions.
- **tasks.md**: extended T017/T018 (PR-fetch) to cover the 300-PR cap
  check and to scrub the `Authorization` header from error messages;
  extended T013 (cost.py test) to assert no credential value leaks into
  `usage_log.jsonl`; extended T032 to explicitly eyeball SC-006 during the
  manual quickstart pass. No task renumbering needed — the cap check fit
  naturally into the existing fetch tasks rather than needing new ones.
- **contracts/cli-interface.md**: Exit-code-1 row and File output contract
  now explicitly carve out the FR-018 case instead of contradicting it.
- **research.md**: retry/backoff Decision now states the concrete numbers.

All artifacts should now be internally consistent. Next step:
`/speckit-implement` — this is the one where actual code finally gets
written.
