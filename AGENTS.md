# AI Agent Instructions

These are the common instructions for any AI agent or assistant working in this
repository — including **Claude** (Claude Code, claude.ai), **ChatGPT / Codex**,
and **Cursor**. Read them before making any change.

This file is the single source of truth for agent rules. `CLAUDE.md`,
`.cursor/rules/`, and any other tool-specific rule file import or reference it —
do not duplicate rules, extend them here. For the fuller contribution policy
(architecture compliance, QA expectations, oral-defense rules), see
[`CONTRIBUTING.md`](CONTRIBUTING.md): follow it wherever it goes deeper, but the
git & commit rules below always apply.

## Git & commit rules

If you are an AI agent and you want to create a commit, you are **disallowed** to:

**a) Push to the `main` branch without creating a Pull Request first.**
   Always work on a dedicated branch and open a PR. `main` must only ever be
   updated through a reviewed and merged PR — never via a direct push.

**b) Commit citations and authorship**
   Do not add `Co-Authored-By:` trailers, `Co-authored-by` lines, "Generated with"
   footers, or any other attribution naming the AI agent (Claude, ChatGPT, Cursor,
   Copilot, etc.) in commit messages or PR descriptions. Commits are authored by
   the human running the tool.

## Commits, branches & pull requests

- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/),
  e.g. `feat: add peer discovery` or `fix(api): handle empty payload`.
- **Branches** follow [Conventional Branch](https://conventional-branch.github.io/),
  e.g. `feature/peer-discovery` or `fix/empty-payload`.
- **Explain the change** — every contribution briefly explains what it does, in
  the commit body, the PR description, or both.
- **Pull requests** use [`.github/pull_request_template.md`](.github/pull_request_template.md).

## General guidance

- Keep changes scoped to what was requested; ask before large or destructive edits.
- Match the existing style, structure, and language of the files you touch
  (project documentation is primarily in French).
- Write clear, conventional commit messages describing *what* and *why*.
- AI-generated code gets the same review as any other; you must be able to
  explain every submitted line.
- Never paste project credentials, `.env` contents, or graded deliverable text
  into an AI tool.
