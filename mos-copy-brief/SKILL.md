---
name: mos-copy-brief
description: >
  Build an SEO + GEO content brief as ONE markdown file: brief tables (client, content and
  publishing guidelines), a SERP-driven article outline with per-section writer guidelines,
  rare primary-source stats checked against the ranking pages, and what Google's AI Overview
  and ChatGPT cite for the keyword. Runs on DataForSEO + Firecrawl, falls back to Apify, and
  still works with no API keys. USE WHEN the user says "content brief", "copy brief", "SEO
  brief", "blog brief", "article brief", "brief for [keyword]", "write a brief", "plan an
  article", "what should this blog post cover", or wants a researched plan before writing a
  blog post, pillar page or landing page that needs to rank or get cited by AI. NOT FOR writing
  the article itself (run mos-copywriting on the approved brief), sales-page, ad or email copy
  with no search target (mos-copy-research then mos-copywriting), or proofreading (mos-proofread).
---

# mos-copy-brief

Produce a brief a writer (human or `/mos-copywriting`) can start from immediately: what to cover, in what order, at what length, with which links and stats, and where the angle is that the ranking pages miss.

**The deliverable is one markdown file:** `content/briefs/<YYYY-MM-DD>-<keyword-slug>-brief.md`. Research files go in a temp run folder and are not part of the output.

**Two rules that override everything else:**
1. **Never invent data.** A metric the run didn't measure is written `Not measured (<reason>)`, e.g. `Not measured (tier 2)` or `Not measured (DataForSEO returned none)`. A URL that isn't in the verified sitemap doesn't go in the brief.
2. **The brief is a review checkpoint.** Stop after saving it. Never start writing the article.

## Paths: read before running any command

The research script is `~/.claude/skills/mos-copy-brief/scripts/brief_research.py`. In the commands below:
- `<script>` = that path, expanded to an absolute path.
- `<brain>` = the brain's root folder (where its `.env` lives).
- `<run>` = the run folder, chosen once in Step 3 as a real absolute path.

**Shell variables don't survive between tool calls**, so never set `SCRIPT=` or `RUN=` once and reuse them. Write the full paths into every command, and start each one with `cd <brain> && ` so the script finds the `.env`.

---

## Tool tiers

| Job | Tier 1: DataForSEO + Firecrawl | Tier 2: Apify | Tier 3: free (no keys) |
|---|---|---|---|
| Google top 10, People Also Ask, AI Overview | `serp` (DataForSEO) | `serp` (Apify) | WebSearch (approximate order, no AI Overview) |
| Search volume, difficulty, CPC | `keywords` | Not measured | Not measured |
| Related / long-tail keywords | `keywords` + `autocomplete` | `autocomplete` + PAA + related searches | `autocomplete` + WebSearch |
| Competitor page content | `scrape` (Firecrawl) | `scrape` (Apify) | WebFetch |
| Cannibalisation check | `site` | `serp` (Apify) on a `site:` query | WebSearch `site:` query |
| ChatGPT answer + citations | `chatgpt` (DataForSEO) | `chatgpt` (Apify) | Member pastes it, or skip |
| Heading themes, gaps, word target | `themes` | `themes` | `themes` |
| Sitemap links, rare stats, outline | Same on every tier | Same | Same |

Typical spend: tier 1 is about $0.05-0.12 of DataForSEO credit plus 7-10 Firecrawl credits. Tier 2 is about $0.02 of Apify usage. Tier 3 is free. Mixed setups work job by job; the preflight `plan` picks the best working provider for each job.

---

## Step 0: Confirm the toolset (ALWAYS, before anything else)

1. Run `cd <brain> && python3 <script> preflight`. It checks each key with a live call and never prints key values.
2. **Always ask the member, even when keys are detected.** Use AskUserQuestion and show what preflight found:

   > "This brief works best with **DataForSEO** (keyword data + Google results) and **Firecrawl** (competitor pages). I found: DataForSEO <ok / missing / invalid>, Firecrawl <ok / missing / invalid, N credits>, Apify <ok / missing / invalid>. Which setup do you want to use?"

   Options:
   - **DataForSEO + Firecrawl (Recommended):** full brief with keyword numbers
   - **Apify only:** everything except search volume, difficulty and CPC
   - **Neither: free version:** Claude's own search; no keyword numbers, no automatic AI Overview

3. If they pick a tool preflight shows as missing or invalid, tell them exactly which variables to add to `<brain>/.env`, then re-run preflight:
   - DataForSEO: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` (API login from the DataForSEO dashboard, pay as you go)
   - Firecrawl: `FIRECRAWL_API_KEY` (free plan includes monthly credits)
   - Apify: `APIFY_TOKEN` (free plan includes a monthly usage credit)

   **Never ask the member to paste a key into the chat.**
4. **Lock the plan to their choice.** For "Apify only" run `preflight --use apify`; for the free version run `preflight --use free`. Use that output's `plan` for the rest of the run, and copy its `tier` and `not_measured` into the brief header. Say any `warning` (low Firecrawl credits) before starting.
5. **Every `serp`, `scrape` and `chatgpt` command passes `--provider` with the plan's value** (`plan.serp`, `plan.scrape`, `plan.chatgpt`) whenever that value is `dataforseo`, `firecrawl` or `apify`. The values `websearch`, `webfetch` and `paste-or-skip` mean the tier-3 manual path for that job. Never let the script choose on its own: a key can be present but broken.

## Step 1: Inputs (one message)

Ask for all of these in a single turn. Skip anything the member already gave.
- **Primary keyword**
- **Content type:** blog post, pillar page or landing page
- **New or optimisation** (optimisation: the live URL)
- **Target URL**, or "not live yet"
- **Country** for search results (read it from the brand files if they state a market, and confirm it). Supported codes: us, au, gb, ca, nz, ie, in, sg, za, ph, ae; any other country needs `--location-code`.

Don't ask for a title tag or meta description. The brief drafts three options of each.

## Step 2: Load brand context

Read whichever of these exist (MarketingOS brain first, older `reference/` layout as a fallback):

| Brief field | Brain file | Fallback |
|---|---|---|
| Customer Avatar | `business/audience/primary.md` (+ any other `business/audience/*.md`) | `reference/core/audience.md` |
| Tone of Voice | `business/brand/voice.md` | `reference/core/voice.md` |
| Brand + domain | `business/brand/brand.md` | `reference/core/soul.md` |
| USPs | `business/offers/*` | `reference/core/offer.md` |
| Proof | `business/proof/testimonials.md` | `reference/proof/testimonials.md` |
| Restrictions + goals | `business/strategy/strategy.md`, `business/strategy/goals.md` | project `CLAUDE.md` |
| Research Bank (reader language) | `business/offer/copy-research-bank.md` (singular `offer/`: that's where `/mos-copy-research` writes it) | none |
| Previous content | `content/` (list briefs and published pieces) | none |

If the avatar or voice file is missing or still a template, say so and suggest `/mos-onboard`. Leave the field as `Not provided: run /mos-onboard` rather than inventing brand details. Ask for the site domain if no file states it.

If a brand file names an offer or page (for example "link to the Growth System page"), it only becomes a link once the sitemap check finds its URL. Otherwise write `Not provided: no live page found for <name>` and flag it in the report.

## Step 3: Research (parallelise)

**Choose `<run>` now:** the system temp folder + `/mos-copy-brief/<keyword-slug>`, written out in full (e.g. `/tmp/mos-copy-brief/how-to-get-more-gym-members`). Use that exact string everywhere below and in both subagent briefs.

Create it first: `mkdir -p <run>/pages`.

In **one turn**, start both subagents AND the first data commands, so they overlap. Each subagent saves its result to a file in `<run>` AND returns it in full as its final reply. **Subagent reports can fail to arrive.** If a subagent finishes and no result reaches you, read its file (`<run>/sitemap-urls.md`, `<run>/information-gain.md`). If the file is missing too, message the subagent and ask it to send its result.

**Subagent A: sitemap verifier.** Brief it with the domain, the keyword, the brand's offer/page names from Step 2, and the resolved `<run>` path. Tell it to:
1. Fetch `https://<domain>/sitemap.xml` (also try `/sitemap_index.xml` and the `Sitemap:` line in `/robots.txt`), follow child sitemaps, and collect every URL.
2. No sitemap: collect the links in the homepage navigation and footer instead, and say so.
3. Save the full URL list, plus everything in item 4, to `<run>/sitemap-urls.md`.
4. Return 5-10 recommended internal links for the keyword (service/product pages first, then 2-4 related posts), each as `full URL (anchor: natural anchor text)`; the live URL for each named offer/page, or "not found"; and any slugs that look like they already target the keyword (cannibalisation risk).

**Subagent B: Information Gain researcher.** Read `~/.claude/skills/mos-copy-brief/references/information-gain.md` yourself and paste its full text into the subagent's prompt (a subagent can't resolve this skill's relative paths), followed by the keyword, a one-line brand/industry description, the country and its output path `<run>/information-gain.md`.

**You, meanwhile:** run the data commands for the locked plan.

### 3a. Keywords
```bash
cd <brain> && python3 <script> autocomplete --keyword "<kw>" --country <cc> --out <run>/autocomplete.json
cd <brain> && python3 <script> keywords --keyword "<kw>" --country <cc> --out <run>/keywords.json    # only when plan.keywords includes dataforseo
```

### 3b. SERP
```bash
cd <brain> && python3 <script> serp --provider <plan.serp> --keyword "<kw>" --country <cc> --out <run>/serp.json
```
**Tier 3 (`plan.serp` = websearch):** WebSearch the keyword and write `<run>/serp.json` yourself in the same shape: `{"keyword": "...", "organic": [{"rank": 1, "url": "...", "title": "...", "domain": "..."}], "paa": [], "related": [], "featured_snippet": null, "ai_overview": null}`. Say in the brief that the order is approximate.

### 3c. Competitor pages
```bash
cd <brain> && python3 <script> scrape --provider <plan.scrape> --serp <run>/serp.json --dir <run>/pages --max 8 --out <run>/scrape.json
```
It skips user-generated results (Reddit, Quora, YouTube, Pinterest...) and pages that block the scraper, then carries on down the list. It exits with an error if no page at all could be scraped. Keep the `skipped` list: a forum thread in the top 10 means the article-style results aren't answering the question well, which is a gap signal.

**Tier 3 (`plan.scrape` = webfetch):** WebFetch each non-UGC organic URL (up to 8) with the prompt *"List every H1-H4 heading of the main article verbatim, as markdown headings (#, ##, ###, ####) in page order. Then one final line: WORDS: <word count of the main article body, digits only, e.g. 1850>."* Save each result to `<run>/pages/<NN>-<domain>.md`, where the first line is `<!-- mos-copy-brief rank=<N> url=<URL> words=<digits> -->`.

### 3d. Themes, gaps, word count
```bash
cd <brain> && python3 <script> themes --dir <run>/pages --out <run>/themes.json
```
The theme list is deliberately generic, so niche topics land in `unmatched_headings`. **Read those and cluster them yourself.** In listicle SERPs they are usually the actual substance (the individual ideas, tactics or tools competitors list).

### 3e. Cannibalisation
Run this after Subagent A reports.
- **Always (every tier):** check Subagent A's sitemap slugs for pages that already target the keyword. This is the baseline check.
- `plan.site_check` = dataforseo and the sitemap has roughly 100+ URLs: also run `cd <brain> && python3 <script> site --domain <domain> --keyword "<kw>" --country <cc> --out <run>/site.json`. Skip it for smaller sites: it costs about $0.04 and returns nothing for sites below DataForSEO's index.
- `plan.site_check` = apify: optionally run `cd <brain> && python3 <script> serp --provider apify --keyword "site:<domain> <kw>" --country <cc> --out <run>/site-serp.json` (Google honours `site:` there).
- Tier 3: rely on the sitemap slugs alone. Claude's WebSearch ignores the `site:` operator and returns unrelated sites.

### 3f. AI search
- The AI Overview (when Google shows one) is already in `<run>/serp.json` on tiers 1 and 2.
- `cd <brain> && python3 <script> chatgpt --provider <plan.chatgpt> --keyword "<kw>" --country <cc> --out <run>/chatgpt.json`
- **Tier 3 (`paste-or-skip`):** ask the member once: "Paste Google's AI Overview and/or ChatGPT's answer for this keyword, or say skip." Skipped is fine; the citability rules still go in the brief.

If a command exits with an error, report it in one line, move that job to the next tier down (DataForSEO/Firecrawl → Apify → free), and keep going. One failed provider never blocks the brief.

## Step 4: Analyse

- **Table stakes:** themes with `pages_covering` of 3 or more go in the outline.
- **Gaps:** themes covered by 0-1 pages that matter to this avatar, angles in the Research Bank or brand files no competitor touches, and questions from PAA/autocomplete no page answers. Every gap names its evidence ("0 of 8 pages cover pricing").
- **Stat check:** for each Information Gain stat, Grep `<run>/pages` for its key number and its source's domain. A stat found on a competitor page is dropped from the top 5, or kept and labelled `also used by #N`. Only unmatched stats may be described as not used by the ranking pages.
- **Stat spot-check:** WebFetch the source of each top-5 stat and confirm the number appears as quoted. Drop any stat you can't confirm, and promote the next one.
- **FAQ questions:** use PAA, autocomplete and related searches only when they match the avatar's intent (e.g. a gym owner's question, not a gym member's). Drop junk suggestions. If fewer than 4 qualify, reframe competitor FAQ headings for the avatar and say so.
- **AI-only sources:** domains cited by the AI Overview or ChatGPT that aren't in the organic top 10.
- **Buying journey:** set the Schwartz awareness stage from intent (informational: Unaware / Problem-Aware; "best / vs / review": Solution-Aware; branded or "pricing": Product / Most-Aware), cross-checked against the avatar. Judge market sophistication (Stage 1-5) from how similar the competitors' claims are.
- **Word count:** `themes.json` → `word_count.target`. If confidence is low, say so in the cell.
- **Secondary keywords:** tier 1 uses the highest-volume relevant terms from `keywords.json`. If that gives fewer than 3 relevant terms (common for low-volume keywords; the JSON `note` says so), top up with terms repeated across autocomplete, PAA, related searches and competitor headings, marked `Not measured (no volume returned)`. Other tiers use those sources only.

## Step 5: Write the brief

Follow `references/brief-template.md` (in this skill's folder) exactly: header, the three Brief Tables, AI Search Visibility, Information Gain Stats, then the Article Outline.

- Internal links only from Subagent A's verified list, always as full URLs.
- The URL slug follows the folder structure of related content in the sitemap (e.g. `/guides/<slug>/` if the site's articles live there).
- Research Pages lists the 3-5 strongest scraped pages, not every result.
- Top 5 Information Gain stats go into the outline as `Cite stat:` bullets in the sections they fit best (intro hook, cost/benefit sections and the conclusion are the strongest placements).
- Title tag options under 60 characters, meta description options under 160, character counts shown.
- Escape `|` inside table cells as `\|`.
- Spelling follows the brand's voice file (Australian, British or American English).

Save to `<brain>/content/briefs/<YYYY-MM-DD>-<keyword-slug>-brief.md` (create the folder if needed).

## Step 6: Verify, then report

Check the saved file against this list and fix anything that fails before reporting:

- [ ] Header states tier, data sources, what wasn't measured, and spend
- [ ] No invented numbers: every volume/KD/CPC traces to `keywords.json`, otherwise `Not measured`
- [ ] All three tables render (no unescaped `|` inside a cell)
- [ ] Every internal link is a full URL from the verified sitemap list
- [ ] Title tags < 60 chars, meta descriptions < 160 chars
- [ ] 8-14 H2s, Key Takeaways near the top, Why Choose + CTA conclusion present, 4-6 FAQs
- [ ] Every outline section except Key Takeaways opens with a `**Writer guidelines:**` line giving its word target; bullets are one idea each
- [ ] At least one `**SERP gap:**` flag, with evidence
- [ ] Information Gain stats have full source URLs and passed the stat check (or a thin-data note is stated)
- [ ] Cannibalisation check completed and stated

Report in chat, briefly:
- File path
- Keyword + volume (or `not measured`) + tier used
- H2 count and word-count target
- Top 2-3 SERP gaps
- Research spend (from the `spend` fields in the JSON outputs)
- Anything that fell back, failed, or needs the member's input (e.g. an offer page with no live URL)

## Step 7: Hand-off

End with: *"Review the brief and edit anything that's off. When it's approved, run `/mos-copywriting` and point it at this file to write the article, then `/mos-proofread` before it ships."*

**Do not start writing the article.**
