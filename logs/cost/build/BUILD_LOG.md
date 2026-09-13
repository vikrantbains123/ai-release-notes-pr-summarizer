# Build Log

Tracks the cost of *building* this project with Claude Code — i.e. this
development session's own token usage and cost, not the tool's runtime cost
(see [../runs/README.md](../runs/README.md) for that).

Claude Code doesn't expose session cost to the assistant programmatically, so
these entries are recorded manually: run `/cost` in the Claude Code terminal
at a milestone and log the numbers it reports here.

## How to log an entry

1. Run `/cost` in the terminal.
2. Add a row to the table below with the date, milestone, the Claude Code
   model active during that session (shown in the terminal / `/model`), and
   the numbers `/cost` reports (total cost, total tokens).

## Log

| Date       | Milestone                          | Model              | Total Cost | Total Tokens | Notes |
|------------|-------------------------------------|---------------------|-----------:|-------------:|-------|
| 2026-09-12 | Project kickoff, repo created        | claude-sonnet-5     | —          | —            | Repo created on GitHub, cloned locally, logging structure set up. Baseline `/cost` not yet captured. |
