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
   Always work on a dedicated branch and open a PR towards `main` once the work
   is ready. `main` must only ever be updated through a reviewed and merged PR —
   never via a direct push. See [Branches & pull requests](#branches--pull-requests)
   for when a PR is (and is not) expected.

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

## Branches & pull requests

Reviewers read every PR by hand: do not make them open PRs with nothing to
review, and do not leave a trail of throwaway branches behind.

### Branches

- **Check before you create.** Run `git branch -a` first. If a branch already
  exists for the feature or issue, keep working on it.
- **One branch per feature / issue, not per step.** Split a feature into steps
  with commits on the same branch, not with a chain of stacked branches
  (`feat/x` → `feat/x-part2` → `feat/x-part3` …).
- **Clean up.** Once a branch is merged, delete it locally (`git branch -d
  <branch>`) and remotely.

### Pull requests

- **Only open a PR to merge into `main`** (protected, PR mandatory) **or into
  a branch owned by someone else.** Merging one of the user's own branches into
  another of their own branches is done locally, without a PR:

  ```sh
  git switch feat/frontend-scaffold && git merge feat/landing-grid
  ```

- **A PR is a complete unit of work** — typically a whole feature or issue made
  of several meaningful commits. Keep committing on the branch until the work
  is done, then open one PR. Single-commit or draft PRs are not useful to
  review; they are only acceptable towards `main` for a truly isolated change
  (e.g. a standalone fix).
- **If unsure whether a PR is warranted, ask the user** before opening it.

## General guidance

- Keep changes scoped to what was requested; ask before large or destructive edits.
- Match the existing style, structure, and language of the files you touch
  (project documentation is primarily in French).
- Write clear, conventional commit messages describing *what* and *why*.
- AI-generated code gets the same review as any other; you must be able to
  explain every submitted line.
- Never paste project credentials, `.env` contents, or graded deliverable text
  into an AI tool.
