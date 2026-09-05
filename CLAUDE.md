# mos-copywriting-skills — Public Shared Repo

This repo is shared with The Vibe Marketing Lab community members. It is PUBLIC.

The Copywriting Blueprint: research it, write it, pressure-test it. This pack sits alongside the MarketingOS engine (`pipx install marketing-os`) and the other `mos-*-skills` packs.

---

## Security Rules (CRITICAL)

Every commit is visible to community members.

- **NEVER commit API keys, tokens, secrets, passwords, or credentials** — not in code, not in comments, not in examples
- **NEVER commit hardcoded file paths** containing usernames or machine-specific paths (e.g. `/mnt/c/Users/<name>/...`, `/Users/<name>/...`)
- **NEVER reference `.env` files with real values** — only env var NAMES as setup instructions (e.g. "set `GOOGLE_API_KEY` in your environment")
- **NEVER commit personal data** — emails, member lists, client info, business details
- **NEVER reference private repos** by path or content

**Before every commit, verify:**
1. `grep -r "API_KEY\|TOKEN\|SECRET\|PASSWORD\|sk-\|AIza" --include="*.md"` returns only env var name references, never values
2. `grep -r "/mnt/c/Users\|/Users/" --include="*.md"` returns zero results
3. No `.env`, `.env.*`, or credential files are staged

---

## What This Repo Contains

Run in order:
1. `mos-copy-research` — 6-step research ladder + compounding Research Bank of real reader language
2. `mos-copywriting` — writes headlines, ads, emails, landing pages, sales letters and VSLs from distilled classic frameworks
3. `mos-proofread` — ordered single-lens QA passes, line-referenced rewrites

`mos-copywriting` gates on real reader language, so `mos-copy-research` is not optional for high-stakes surfaces.

Each skill is a flat top-level folder with a `SKILL.md` (the skill prompt) and, where needed, `references/` (frameworks) or `scripts/` (deterministic tools). `setup.sh` links every top-level skill folder into `~/.claude/skills/`.

## Editing Rules

- Skills must work on any machine — relative paths and env var references only
- Skills sit at the top level of this repo; a nested skill folder is invisible to Claude Code
- Keep README.md current when adding or renaming a skill, then re-run `setup.sh`
- Test every skill without any private infrastructure before pushing

> **Third-party framework rule.** `mos-copywriting` draws on published works by Joseph Sugarman, Dan Kennedy, David Ogilvy, John Caples and Gary Halbert. Every `references/` file carries its own `Source:` line and the SKILL.md carries an independent-implementation notice. Do NOT add verbatim extracts or redistributable reproductions of those books.
