# mos-copywriting-skills

The Copywriting Blueprint for Claude Code: research the reader, write the copy, then pressure-test it before it ships. Three skills, run in order.

Built by [The Vibe Marketing Lab](https://www.skool.com/the-vibe-marketing-lab) for the MarketingOS engine (`pipx install marketing-os`).

> `/mos-copywriting` applies frameworks from published works by Joseph Sugarman, Dan Kennedy, David Ogilvy, John Caples and Gary Halbert. Independent implementation, not affiliated with or endorsed by those authors or their estates.

## What's in here

| # | Skill | What it does | Time |
|---|-------|--------------|------|
| 1 | `/mos-copy-research` | Runs the 6-step research ladder and builds a compounding Research Bank of real reader language | ~10-20 min |
| 2 | `/mos-copywriting` | Writes headlines, ads, emails, landing pages, sales letters and VSLs from distilled classic frameworks. Also reviews existing copy | ~3-8 min |
| 3 | `/mos-proofread` | QA pass: ordered single-lens reviews (strategy, structure, clarity, cut, voice, mechanics, read-aloud) returning line-referenced rewrites | ~2-5 min |

`/mos-copywriting` gates on real reader language, so `/mos-copy-research` is not optional for anything high-stakes. The research compounds: every run appends to an Avatar Knowledge Log and re-synthesises the Research Bank, so the second sales page starts further ahead than the first.

## Prerequisites

1. **Claude Code** with a Claude Pro or Max subscription.
2. **Your business files** in the project you run from: `reference/core/audience.md` and `reference/core/offer.md` at minimum. `/mos-copy-research` writes its bank to `business/offer/copy-research-bank.md` and the avatar log under `business/audience/_shared/`.

## Install

Skills live in `~/.claude/skills/`. This repo keeps them under version control and links them into place, so a `git pull` is all an update takes.

```bash
git clone https://github.com/the-vibe-marketing-lab/mos-copywriting-skills.git ~/Desktop/mos-copywriting-skills
cd ~/Desktop/mos-copywriting-skills
bash setup.sh
```

`setup.sh` links every skill folder in this repo into `~/.claude/skills/` (a symlink on macOS and Linux, a directory junction on Windows via Git Bash). Restart any open Claude Code session, then type `/mos-copywriting` to confirm it loads.

**Updating:** `cd ~/Desktop/mos-copywriting-skills && git pull`. The links point at the clone, so that's it. Updates are announced in the Skool community.

**Other packs:** this is one of the `mos-*-skills` packs that accompany the [MarketingOS engine](https://github.com/the-vibe-marketing-lab/marketing-os). The full list is in the [marketing-os-skills](https://github.com/the-vibe-marketing-lab/marketing-os-skills) README.

## How to use

1. **`/mos-copy-research`** before writing anything important. Tell it which offer and which reader. It works down the ladder (your own files, testimonials, reviews, forums, competitor copy, interviews) and locks the One Reader, the transformation map and the exact phrases you'll write with.
2. **`/mos-copywriting`** with the surface you need: "write the landing page for X", "five headlines for this email", "review this ad". It reads the Research Bank first and tells you if the bank is too thin to write from.
3. **`/mos-proofread`** on the draft: "proofread this", "is this ready to ship". You get a scored pass per lens and rewrites you can apply line by line.

## Tips

- Paste the actual draft, not a description of it. The proofreader works on words.
- Keep `reference/proof/testimonials.md` real. Invented testimonials poison the Research Bank.
- One reader per piece of copy. If the skill asks who it's for, that's the most important question you'll answer.
