# Information Gain researcher (subagent brief)

Hand this whole file to a subagent, together with: the primary keyword, a one-line description of the brand and its industry, the country, and any SERP gap themes already known (optional).

## Why this exists

Google rewards pages that add something the ranking pages don't have, and AI answers prefer named, dated, sourced numbers. The most defensible version of that is a stat pulled from a primary document (a government report, a university paper, an industry body's survey) that no competitor has bothered to dig out. The SERP analysis shows what everyone is saying. This research finds what nobody is citing yet.

## Inputs

- **Primary keyword:** <keyword>
- **Brand + industry:** <one line>
- **Country:** <country>, prefer local data, then international
- **Gap themes:** <optional list>

## Method

### 1. Plan at least 12 searches

Combine file-type operators with the keyword and two or three close synonyms:

```
filetype:pdf "<topic>"
filetype:pdf "<topic>" survey OR report <current year or last year>
site:gov filetype:pdf "<topic>"        (use the country's gov domain, e.g. gov.au, gov.uk)
site:edu filetype:pdf "<topic>"        (ac.uk, edu.au outside the US)
site:org filetype:pdf "<topic>" research
filetype:pptx "<topic>"
filetype:xlsx "<topic>"
filetype:docx "<topic>"
"<topic>" statistics site:<national statistics agency domain>
"<topic>" "industry report" filetype:pdf
"<topic>" benchmark filetype:pdf
"<gap theme>" filetype:pdf              (one per gap theme)
```

Add the relevant standards bodies, trade associations and national statistics agencies for the industry.

### 2. Search, then open the documents

Use WebSearch for every query. For each promising result, WebFetch the document (or its abstract page) and copy the number from the source itself. Never record a stat you only saw in a search snippet.

**Filter hard:**
- Skip blog posts, news articles, listicles and vendor SEO pages. A vendor's own original survey is fine if it states its sample and method.
- Skip paywalled documents unless the free preview contains the stat.
- Prefer the last 3 years. Flag anything older than 5 years as `Dated`.
- Prefer .gov, .edu, .org, statistics agencies, universities, standards bodies and named industry associations.

### 3. Collect at least 10 stats (aim for 20)

Mix the document types when you can. For each stat, record:
- the exact number or claim, copied verbatim
- organisation + document title + year
- the full URL of the document itself (not a search result or redirect)
- file type (PDF / PPTX / XLSX / DOCX / web report)
- where it fits in the article (intro hook, cost section, FAQ, conclusion ...)
- credibility: `High`, `Medium` or `Flag` with the reason (dated, small sample, vendor-funded)

## Output (return this as markdown, write no files)

```markdown
## INFORMATION GAIN: <keyword>

- Stats found: <N>
- Document mix: <e.g. 7 PDF, 2 XLSX, 1 PPTX>
- Strongest sources: <3-5 organisations>
- Notes: <e.g. "no local data, all US/UK", "niche has thin primary data">

| # | Stat | Source (year) | URL | File | Use in | Credibility |
|---|---|---|---|---|---|---|
| 1 | <verbatim stat> | <org, document> (<year>) | <full URL> | PDF | Intro hook | High |

## TOP 5 FOR THE OUTLINE
1. <stat>: best fit <section>
2. ...
```

Fewer than 10 usable stats is an acceptable result. Say so plainly in Notes rather than padding the table with weak sources.

## Never

- Invent, round or paraphrase a number. Verbatim or leave it out.
- Cite a stat you can't open the source for.
- Use numbered footnote markers like `[1]`. The URL goes in the table.
