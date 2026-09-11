# AI Agent Instructions

These are the common instructions for any AI agent or assistant working in this
repository — including **Claude** (Claude Code, claude.ai), **ChatGPT / Codex**,
and **Cursor**. Read them before making any change.

This file is the single source of truth. `CLAUDE.md` and any tool-specific rule
files import or reference it — do not duplicate rules, extend them here.

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

## General guidance

- Keep changes scoped to what was requested; ask before large or destructive edits.
- Match the existing style, structure, and language of the files you touch
  (project documentation is primarily in French).
- Write clear, conventional commit messages describing *what* and *why*.
