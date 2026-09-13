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
