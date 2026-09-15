# Brief template

The brief is ONE markdown file. Match this shape exactly: the section names and field labels are the contract `mos-copywriting` reads.

## Table rules

- Brief tables are real markdown tables with two columns: `Field | Guidance`.
- A cell can't hold a markdown list. Put multiple items on separate lines joined with `<br>`, each starting with `• `.
- **Escape every pipe inside a cell as `\|`.** Title tags usually contain one (`Title | Brand`) and an unescaped pipe breaks the whole table.
- Keep cells short. Anything longer than about five lines (AI answers, stat details) goes in its own section below the tables, never in a cell.
- Write `Not measured (<reason>)` for any metric the run couldn't get, e.g. `Not measured (tier 2)`, including a keyword the provider returned with no volume (`Not measured (no volume returned)`). Use that one label everywhere; don't mix in "0/mo" or "volume not returned". Never estimate a number.

---

## Template

````markdown
# Content Brief: <Primary Keyword>

> **Brand:** <Brand> · **Date:** <YYYY-MM-DD> · **Country:** <Country> · **Tier:** <1 / 2 / 3 / mixed>
> **Data:** <e.g. DataForSEO (keywords, SERP, ChatGPT) · Firecrawl (8 pages) · WebSearch (stats)>
> **Not measured:** <e.g. search volume, keyword difficulty, CPC> (or "Nothing")
> **Research spend:** <e.g. DataForSEO $0.11 · Firecrawl 8 credits>

## 1. Client Guidelines

| Field | Guidance |
|---|---|
| **Customer Avatar** | <who they are, one line><br>• <pain point><br>• <goal><br>• <objection> |
| **Tone of Voice** | <voice in one line><br>• <attribute><br>• <attribute><br>• <words to avoid> |
| **Restrictions and Guidelines** | **CANNOT:**<br>• <hard constraint><br>**MUST:**<br>• <required behaviour> |
| **USPs** | • <USP + one-line proof><br>• <USP + one-line proof> |
| **Proof** | • <testimonial, result or credential><br>(or "Not provided: run /mos-onboard") |

## 2. Content Guidelines

| Field | Guidance |
|---|---|
| **Focus Keyword** | <primary keyword> (<volume>/mo · KD <n> · CPC <n>) |
| **Secondary Keywords** | • <keyword> (<volume>/mo)<br>• <keyword> (<volume>/mo)<br>• <keyword> (<volume>/mo) |
| **New or Optimisation** | <New / Optimisation of URL> |
| **Search Intent** | <one line: who is searching and what they need><br>• <they want to understand ...><br>• <they want to understand ...> |
| **Content Type** | <Blog post / Landing page / Pillar page> |
| **Buying Journey** | **Awareness:** <Unaware / Problem-Aware / Solution-Aware / Product-Aware / Most-Aware>: <one-line why><br>**Market sophistication:** Stage <1-5>: <one-line why> |
| **Target Audience** | **Primary:** <segment><br>**Secondary:** <segment> |
| **Word Count** | <target range> words (<N> competitors analysed, average <n>, <confidence>) |
| **Internal Links** | • <full URL> (anchor: <anchor text>)<br>• <full URL> (anchor: <anchor text>) |
| **External Links** | Link only to reputable primary sources (.gov, .edu, .org, research bodies). Never link to competitors. |
| **What's Missing in the SERP** | • <gap angle + evidence, e.g. "no competitor covers X (0/8)"><br>• <gap> |
| **Featured Snippet** | <Exists: URL + format / None> · <how to win it> |
| **Cannibalisation Check** | <Clear / Risk: URL already ranks #n for "keyword"> |
| **Previous Content** | • <related brief or published post><br>(or "None found") |
| **Content Goals** | • **SEO:** <goal><br>• **Lead generation:** <goal><br>• **Education:** <goal> |
| **Research Pages** | • #<rank> <URL> (<what it does well>)<br>• #<rank> <URL> (<what it does well>) |

## 3. Publishing Guidelines

| Field | Guidance |
|---|---|
| **URL Slug** | /<slug>/ |
| **Title Tag** | <option 1 \| Brand> (<n> chars)<br><option 2> (<n> chars)<br><option 3> (<n> chars) |
| **Meta Description** | <option 1> (<n> chars)<br><option 2> (<n> chars)<br><option 3> (<n> chars) |
| **Publishing Notes** | • <spelling convention, e.g. Australian English><br>• <CTA target><br>• <differentiation angle><br>• <brand constraint> |

## 4. AI Search Visibility

**Google AI Overview:** <Present / None for this query / Not captured (tier 3, member skipped)>

<2-4 line summary of what the AI Overview says. Quote short phrases, don't paste the whole thing.>

Cited by the AI Overview:
- <domain>: <URL>

**ChatGPT:** <Present / Not captured>

<2-4 line summary of the answer.>

Cited by ChatGPT:
- <domain>: <URL>

**Cited by AI but not in the top 10:** <domains, or "None">

**How to get cited:**
- Answer the question in the first 40-60 words under each H2.
- Use named, dated stats with sources (see section 5).
- Phrase H2s as the questions this reader actually asks (see the FAQ section).
- <one line specific to what the AI answers above are missing>

## 5. Information Gain Stats

Primary-source stats, each checked against the scraped competitor pages. Mark any stat a competitor also uses as `also used by #N`. The writer drops these into the sections named in the last column.

| # | Stat | Source (year) | URL | Use in |
|---|---|---|---|---|
| 1 | <verbatim stat> | <organisation, document> (<year>) | <full URL> | <outline section> |

<If fewer than 10 usable stats were found, say so here in one line. Thin data is a finding, not a failure.>

## 6. Article Outline

# <H1 targeting the primary keyword>

**Writer guidelines:** target ~<n> words
- <hook: the specific problem or stat to open on>
- <what the article promises>
- Include link: <full URL> (anchor: "<anchor text>")

## Key Takeaways

- <takeaway>
- <takeaway>
- <takeaway>
- <takeaway>

## <H2 from a table-stakes theme>

**Writer guidelines:** target ~<n> words
- Cover: <topic>
- Competitors: #<rank> <domain> covers this: match their depth on <point>
- Go further: <angle>
- Cite stat: "<verbatim stat>" (<Source>, <year>), see section 5
- Include link: <full URL> (anchor: "<anchor text>")

### <H3 subsection>

**Writer guidelines:** target ~<n> words
- **SERP gap:** <angle no competitor covers>. Own it.
- <specific detail to cover>

## Why Choose <Brand>?

**Writer guidelines:** ~30-word intro, then bullets
- <USP from brand files>
- <USP from brand files>

## Frequently Asked Questions

### <Question the avatar actually asks (PAA, autocomplete or a reframed competitor FAQ)>?

**Writer guidelines:** ~60-80 words
- Answer directly in the first sentence
- <detail to add>

## <CTA conclusion H2>

**Writer guidelines:** target ~<n> words
- <summarise the core message>
- <CTA: exact action>
- Include link: <full URL> (anchor: "<anchor text>")
````

---

## Outline rules

- Real markdown heading levels only (`#`, `##`, `###`). Never write `H2:` labels.
- 8-14 H2s. Key Takeaways near the top. 4-6 FAQs. Why Choose and the CTA conclusion always present.
- Every section except Key Takeaways opens with a `**Writer guidelines:**` line giving its word target, then bullets of about 20 words or fewer, one idea each.
- Every internal link is a full URL from the verified sitemap list. Never a relative path, never a guessed URL.
- Section word targets add up to the Word Count range in section 2 (within about 10%).
