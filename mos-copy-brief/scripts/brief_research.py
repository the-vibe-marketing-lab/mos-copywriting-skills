#!/usr/bin/env python3
"""Research helper for the mos-copy-brief skill.

Standard library only, so members need nothing beyond Python 3.9+.
Every command writes JSON (to --out, or stdout). Errors go to stderr as JSON with exit code 2.
Credentials come from the environment, or the nearest .env found walking up from the current
directory (stopping at the project's git root, and never reading the home folder's .env from
a subfolder). Credential values are never printed.

Commands:
  preflight [--use all|apify|free]  which providers are configured and valid, and the plan
  serp --keyword K                  Google top 10, People Also Ask, related searches, AI Overview
  keywords --keyword K              volume, difficulty, CPC, related + suggested terms (DataForSEO)
  autocomplete --keyword K          Google autocomplete expansion (free, no key)
  site --domain D --keyword K       existing rankings + top pages, for cannibalisation (DataForSEO)
  scrape --serp FILE --dir D        competitor pages to markdown (Firecrawl or Apify)
  themes --dir D                    heading themes, SERP gaps and word-count target
  chatgpt --keyword K               ChatGPT answer + cited sources
"""

import argparse
import base64
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from statistics import median

DATAFORSEO = "https://api.dataforseo.com/v3/"
FIRECRAWL = "https://api.firecrawl.dev/v2/"
APIFY = "https://api.apify.com/v2/"
US_LOCATION = 2840

COUNTRIES = {
    "us": (2840, "the United States"),
    "au": (2036, "Australia"),
    "gb": (2826, "the United Kingdom"),
    "uk": (2826, "the United Kingdom"),
    "ca": (2124, "Canada"),
    "nz": (2554, "New Zealand"),
    "ie": (2372, "Ireland"),
    "in": (2356, "India"),
    "sg": (2702, "Singapore"),
    "za": (2710, "South Africa"),
    "ph": (2608, "the Philippines"),
    "ae": (2784, "the United Arab Emirates"),
}

# User-generated content ranks often but has no article structure worth clustering.
UGC_DOMAINS = ("reddit.com", "quora.com", "youtube.com", "facebook.com", "instagram.com",
               "tiktok.com", "x.com", "twitter.com", "linkedin.com")

# Site-furniture headings. Matched against the WHOLE heading (or a short heading that starts with
# the phrase), never as a substring, so "How to collect more testimonials" survives.
NOISE = ("contact us", "contact", "enquire now", "latest articles", "testimonials", "related posts",
         "related post", "related articles", "about us", "our products", "quick links", "footer",
         "newsletter", "subscribe", "subscribe to our newsletter", "sign up for our newsletter",
         "follow us", "share this", "share this post", "recent posts", "you may also like",
         "you might also like", "request a quote", "get a quote", "book online", "call us",
         "email us", "copyright", "categories", "table of contents", "leave a reply", "comments",
         "about the author", "written by", "ready to get started", "get your free quote",
         "awards and recognition", "related reading", "further reading", "sources", "sources and data",
         "references")

# Checked in order; the first match wins. Specific themes come before broad ones.
THEMES = {
    "faq": r"\bfaqs?\b|frequently asked|common questions",
    "why_choose_us": r"why choose|\bwhy us\b|what makes us|\bour (service|process)\b",
    "comparison": r"\bvs\.?\b|\bversus\b|\bcompared?\b|\bdifferences?\b|\balternatives?\b",
    "conclusion": r"\bconclusion\b|final thoughts?|\bsummary\b|get started|next steps?|wrapping up",
    "definition": r"\bwhat (is|are)\b|\bdefinition\b|\boverview\b|\bintroduction\b|\bmeaning\b",
    "how_it_works": r"\bhow (do|does)\b|how it works|how they work",
    "cost": r"\bcosts?\b|\bprices?\b|\bpricing\b|how much|\bbudget\b|\broi\b|\bfees?\b",
    "types": r"\btypes?\b|\bkinds?\b|\bvarieties\b",
    "steps_how_to": r"\bhow to\b|\bsteps?\b|step-by-step|\bguide\b|\bset ?up\b|\binstall",
    "problems_mistakes": r"\bproblems?\b|\bissues?\b|\bdisadvantages?\b|\bdownsides?\b|\bmistakes?\b"
                         r"|\bavoid\b|\bmyths?\b|\brisks?\b|\bpitfalls?\b",
    "tools": r"\btools?\b|\bsoftware\b|\bapps?\b|\bplatforms?\b|\btemplates?\b|\bresources?\b",
    "examples_case_studies": r"\bexamples?\b|case stud|success stor|\bresults\b|\binspiration\b",
    "tips_strategies": r"\btips?\b|\bstrateg(y|ies)\b|\bideas?\b|ways to|\btactics?\b|\bhacks?\b"
                       r"|best practices?",
    "choosing": r"\bchoos(e|ing)\b|\bselect(ing)?\b|\bbest\b|\bpick\b|right for",
    "metrics_tracking": r"\bmeasur|\btrack(ing)?\b|\bmetrics?\b|\bkpis?\b|\banalytics\b",
    "maintenance": r"\bmaint(ain|enance)\b|\brepairs?\b|\breplac|\bupkeep\b",
    "local": r"near me|in your area|service areas?",
    "benefits": r"\bbenefits?\b|\badvantages?\b|^why\b|\bworth\b|\bimportance\b|\bpurpose\b",
}
THEME_PATTERNS = {theme: re.compile(pattern) for theme, pattern in THEMES.items()}
PRICE_NOISE = re.compile(r"\$\s?\d[\d,.]*\s*(/|per)\s*(mo|month|week|year)|starting at \$", re.I)

AUTOCOMPLETE_PREFIXES = ("how", "what", "why", "when", "which", "can", "is", "best", "cost of")
STOP_WORDS = {"how", "to", "get", "more", "the", "a", "an", "for", "of", "in", "on", "and", "or", "what",
              "is", "are", "best", "top", "your", "my", "with", "why", "do", "does", "can", "ideas", "tips"}

COST = {"dataforseo_usd": 0.0, "apify_usd": 0.0, "firecrawl_credits": 0}


class ToolError(Exception):
    pass


# --- environment + HTTP -----------------------------------------------------------------------

def load_env():
    """Load the nearest .env without overriding the real environment.

    Stops at the project's git root, and never climbs into the home folder from a subfolder,
    so an unrelated ~/.env can't silently spend someone else's keys.
    """
    home, cwd = Path.home().resolve(), Path.cwd().resolve()
    for folder in [cwd, *cwd.parents]:
        if folder == home and folder != cwd:
            return
        if (folder / ".env").is_file():
            read_env_file(folder / ".env")
            return
        if (folder / ".git").exists():
            return


def read_env_file(path):
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        match = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not match or os.environ.get(match.group(1)):
            continue
        value = match.group(2).strip()
        if value[:1] in "\"'" and value[:1] and value.count(value[0]) >= 2:
            value = value[1:value.index(value[0], 1)]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
        os.environ[match.group(1)] = value


def env(name):
    return os.environ.get(name, "").strip()


def apify_token():
    return env("APIFY_TOKEN") or env("APIFY_API_KEY")


CONFIGURED = {
    "dataforseo": lambda: bool(env("DATAFORSEO_LOGIN") and env("DATAFORSEO_PASSWORD")),
    "firecrawl": lambda: bool(env("FIRECRAWL_API_KEY")),
    "apify": lambda: bool(apify_token()),
}


def http(method, url, body=None, headers=None, timeout=120):
    """Return (status, parsed JSON). Status 0 means the request never got a usable response."""
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={
        "Content-Type": "application/json", "User-Agent": "mos-copy-brief/1.0", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8", "ignore") or "null")
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", "ignore")
        try:
            return error.code, json.loads(raw)
        except ValueError:
            return error.code, {"error": raw[:300]}
    except (OSError, http.client.HTTPException, ValueError) as error:
        return 0, {"error": f"{type(error).__name__}: {error}"}


def pick_provider(requested, order):
    if requested:
        require(requested)
        return requested
    for name in order:
        if CONFIGURED[name]():
            return name
    raise ToolError(f"No provider configured (tried {', '.join(order)}). Use the free tier-3 path.")


def require(name):
    if not CONFIGURED[name]():
        raise ToolError(f"{name} is not configured. See the env var names in SKILL.md, Step 0.")


def read_json_file(path, what):
    file = Path(path)
    if not file.is_file():
        raise ToolError(f"{what} not found: {path}")
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except ValueError as error:
        raise ToolError(f"{what} is not valid JSON: {path} ({error})")


# --- providers --------------------------------------------------------------------------------

def dataforseo_headers():
    token = base64.b64encode(f"{env('DATAFORSEO_LOGIN')}:{env('DATAFORSEO_PASSWORD')}".encode())
    return {"Authorization": "Basic " + token.decode()}


def dataforseo(path, body):
    status, data = http("POST", DATAFORSEO + path, [body], dataforseo_headers(), timeout=300)
    data = data if isinstance(data, dict) else {}
    task = (data.get("tasks") or [{}])[0]
    COST["dataforseo_usd"] += task.get("cost") or 0
    if status == 200 and task.get("status_code") == 40102:  # "No Search Results": a valid empty answer
        return {}
    if status != 200 or task.get("status_code") != 20000:
        message = task.get("status_message") or data.get("status_message") or data.get("error")
        raise ToolError(f"DataForSEO {path} failed: {message}")
    return (task.get("result") or [None])[0] or {}


def firecrawl_scrape(url):
    body = {"url": url, "formats": ["markdown"], "onlyMainContent": True}
    headers = {"Authorization": "Bearer " + env("FIRECRAWL_API_KEY")}
    status, data = http("POST", FIRECRAWL + "scrape", body, headers, timeout=120)
    data = data if isinstance(data, dict) else {}
    if status != 200 or not data.get("success"):
        return None, status, f"firecrawl {status}: {str(data.get('error'))[:120]}"
    COST["firecrawl_credits"] += (data["data"].get("metadata") or {}).get("creditsUsed") or 1
    return data["data"].get("markdown") or "", status, None


def apify_headers():
    return {"Authorization": "Bearer " + apify_token()}


def apify_run(actor, run_input, timeout=900):
    """Start an actor run, wait for it, return its dataset items. Aborts the run if it overruns."""
    status, data = http("POST", f"{APIFY}acts/{actor}/runs?waitForFinish=60", run_input, apify_headers())
    run = (data or {}).get("data") if isinstance(data, dict) else None
    if status not in (200, 201) or not run:
        raise ToolError(f"Apify {actor} failed to start: HTTP {status} {str(data)[:200]}")
    started = time.time()
    while run.get("status") in ("READY", "RUNNING") and time.time() - started < timeout:
        _, data = http("GET", f"{APIFY}actor-runs/{run['id']}?waitForFinish=60", None, apify_headers())
        run = (data or {}).get("data") or run
    if run.get("status") in ("READY", "RUNNING"):
        http("POST", f"{APIFY}actor-runs/{run['id']}/abort", {}, apify_headers())
        raise ToolError(f"Apify {actor} still running after {timeout}s; the run was aborted to stop billing.")
    COST["apify_usd"] += run.get("usageTotalUsd") or 0
    if run.get("status") != "SUCCEEDED":
        raise ToolError(f"Apify {actor} ended with status {run.get('status')}")
    status, items = http("GET", f"{APIFY}datasets/{run['defaultDatasetId']}/items?clean=true", None,
                         apify_headers())
    if status != 200 or not isinstance(items, list):
        raise ToolError(f"Apify {actor} finished but its results could not be read (HTTP {status}).")
    return items


# --- helpers ----------------------------------------------------------------------------------

def country_entry(args):
    code = (args.country or "us").lower()
    if code in COUNTRIES:
        return COUNTRIES[code]
    if args.location_code:
        return args.location_code, "your country"
    raise ToolError(f"Unknown country '{code}'. Use one of {sorted(COUNTRIES)} or pass --location-code.")


def location_code(args):
    return args.location_code or country_entry(args)[0]


def domain_of(url):
    url = url or ""
    host = urllib.parse.urlparse(url if "//" in url else "//" + url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def normalise_url(url):
    return domain_of(url) + urllib.parse.urlparse(url or "").path.rstrip("/").lower()


def is_ugc(url):
    host = domain_of(url)
    if host.startswith("pinterest.") or ".pinterest." in host:
        return True
    return any(host == d or host.endswith("." + d) for d in UGC_DOMAINS)


def strip_markdown(text):
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    return text.replace("\xa0", " ")


def word_count(markdown):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’-]*", strip_markdown(markdown)))


def clean_heading(text):
    text = strip_markdown(text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", r"\1", text)  # markdown escapes like "1\. Tip"
    text = re.sub(r"[*_`]+", "", text)
    return re.sub(r"\s+", " ", text).strip(" :#")


def is_noise(heading):
    # A heading starting lowercase is a stat callout or a sentence fragment, not a section title.
    if len(heading) < 4 or len(heading) > 140 or heading[0].islower() or PRICE_NOISE.search(heading):
        return True
    normal = re.sub(r"[^a-z0-9 ]+", "", heading.lower()).strip()
    for phrase in NOISE:
        if normal == phrase or (normal.startswith(phrase + " ") and len(normal.split()) <= len(phrase.split()) + 1):
            return True
    return False


def extract_headings(markdown):
    headings, in_code = [], False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```"):
            in_code = not in_code
            continue
        match = None if in_code else re.match(r"^(#{1,4})\s+(.+?)\s*#*\s*$", line.strip())
        if match:
            text = clean_heading(match.group(2))
            if not is_noise(text):
                headings.append({"level": len(match.group(1)), "text": text})
    return headings


def match_theme(heading):
    lowered = heading.lower()
    return next((theme for theme, pattern in THEME_PATTERNS.items() if pattern.search(lowered)), None)


def source_rows(raw_sources):
    rows, seen = [], set()
    for source in raw_sources or []:
        url = (source.get("url") or source.get("link") or "").strip() if isinstance(source, dict) else ""
        if url and url not in seen:
            seen.add(url)
            rows.append({"url": url, "title": source.get("title"), "domain": domain_of(url)})
    return rows


# --- preflight --------------------------------------------------------------------------------

def check_dataforseo():
    if not CONFIGURED["dataforseo"]():
        return {"status": "missing", "env": ["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"]}
    status, data = http("GET", DATAFORSEO + "appendix/user_data", None, dataforseo_headers())
    data = data if isinstance(data, dict) else {}
    if status != 200 or data.get("status_code") != 20000:
        return {"status": "invalid", "detail": str(data.get("status_message") or data.get("error"))[:160]}
    result = ((data.get("tasks") or [{}])[0].get("result") or [{}])[0] or {}
    return {"status": "ok", "balance_usd": (result.get("money") or {}).get("balance")}


def check_firecrawl():
    if not CONFIGURED["firecrawl"]():
        return {"status": "missing", "env": ["FIRECRAWL_API_KEY"]}
    headers = {"Authorization": "Bearer " + env("FIRECRAWL_API_KEY")}
    status, data = http("GET", FIRECRAWL + "team/credit-usage", None, headers)
    data = data if isinstance(data, dict) else {}
    if status != 200 or not data.get("success"):
        return {"status": "invalid", "detail": str(data.get("error"))[:160]}
    credits = (data.get("data") or {}).get("remainingCredits")
    result = {"status": "ok", "credits_remaining": credits}
    if isinstance(credits, (int, float)) and credits < 20:
        result["warning"] = "Under 20 Firecrawl credits left. One brief uses about 8-10."
    return result


def check_apify():
    if not CONFIGURED["apify"]():
        return {"status": "missing", "env": ["APIFY_TOKEN"]}
    status, data = http("GET", f"{APIFY}users/me", None, apify_headers())
    if status != 200 or not (data or {}).get("data"):
        return {"status": "invalid", "detail": f"HTTP {status}"}
    return {"status": "ok"}


def build_plan(checks):
    ok = {name: check["status"] == "ok" for name, check in checks.items()}
    dfs, fire, apify = ok["dataforseo"], ok["firecrawl"], ok["apify"]
    plan = {
        "serp": "dataforseo" if dfs else "apify" if apify else "websearch",
        "keywords": "dataforseo+autocomplete" if dfs else "autocomplete",
        "site_check": "dataforseo" if dfs else "apify" if apify else "websearch",
        "scrape": "firecrawl" if fire else "apify" if apify else "webfetch",
        "chatgpt": "dataforseo" if dfs else "apify" if apify else "paste-or-skip",
    }
    if dfs and fire:
        plan["tier"] = "1 (DataForSEO + Firecrawl)"
    elif apify and not (dfs or fire):
        plan["tier"] = "2 (Apify)"
    elif not (dfs or fire or apify):
        plan["tier"] = "3 (free, no keys)"
    else:
        plan["tier"] = "mixed"
    plan["not_measured"] = [] if dfs else ["search volume", "keyword difficulty", "CPC"]
    if plan["serp"] == "websearch":
        plan["not_measured"] += ["exact Google ranking order", "AI Overview (unless pasted)",
                                 "ChatGPT answer (unless pasted)"]
    return plan


PROVIDERS = ("dataforseo", "firecrawl", "apify")


def parse_use(value):
    """'all', 'free', or a comma list of providers, e.g. 'dataforseo,apify'."""
    if value == "all":
        return PROVIDERS
    if value == "free":
        return ()
    chosen = tuple(p.strip() for p in value.split(",") if p.strip())
    if not chosen or any(p not in PROVIDERS for p in chosen):
        raise argparse.ArgumentTypeError(f"use all, free, or a comma list of {', '.join(PROVIDERS)}")
    return chosen


def cmd_preflight(args):
    allowed = args.use
    checkers = {"dataforseo": check_dataforseo, "firecrawl": check_firecrawl, "apify": check_apify}
    checks = {name: checker() if name in allowed else {"status": "not_used"} for name, checker in checkers.items()}
    return {"use": args.use, "checks": checks, "plan": build_plan(checks)}


# --- serp -------------------------------------------------------------------------------------

def empty_serp(args, provider):
    return {"provider": provider, "keyword": args.keyword, "country": args.country, "organic": [],
            "paa": [], "related": [], "featured_snippet": None, "ai_overview": None}


def dfs_organic(serp, item):
    serp["organic"].append({"rank": item.get("rank_group"), "url": item.get("url"),
                            "title": item.get("title"), "domain": domain_of(item.get("url"))})
    if item.get("is_featured_snippet"):
        serp["featured_snippet"] = {"url": item.get("url"), "text": item.get("description")}


def dfs_featured(serp, item):
    serp["featured_snippet"] = {"url": item.get("url"), "text": item.get("description")}


def dfs_paa(serp, item):
    serp["paa"] += [q.get("title") for q in item.get("items") or [] if q.get("title")]


def dfs_related(serp, item):
    for entry in item.get("items") or []:
        text = entry if isinstance(entry, str) else (entry or {}).get("title")
        if text:
            serp["related"].append(text)


def dfs_ai_overview(serp, item):
    parts = [e.get("text") for e in item.get("items") or [] if e.get("text")]
    serp["ai_overview"] = {"text": "\n\n".join(parts) or item.get("markdown") or "",
                           "references": source_rows(item.get("references"))}


DFS_SERP_HANDLERS = {"organic": dfs_organic, "featured_snippet": dfs_featured,
                     "people_also_ask": dfs_paa, "related_searches": dfs_related,
                     "ai_overview": dfs_ai_overview}


def serp_dataforseo(args):
    body = {"keyword": args.keyword, "location_code": location_code(args), "language_code": args.lang,
            "device": "desktop", "depth": 20, "load_async_ai_overview": True}  # 20: SERP features eat slots
    serp = empty_serp(args, "dataforseo")
    for item in dataforseo("serp/google/organic/live/advanced", body).get("items") or []:
        handler = DFS_SERP_HANDLERS.get(item.get("type"))
        if handler:
            handler(serp, item)
    return serp


def serp_apify(args):
    country_entry(args)
    country = "gb" if args.country.lower() == "uk" else args.country.lower()
    items = apify_run("apify~google-search-scraper", {
        "queries": args.keyword, "countryCode": country, "languageCode": args.lang,
        "resultsPerPage": 20, "maxPagesPerQuery": 1})
    page = items[0] if items else {}
    serp = empty_serp(args, "apify")
    serp["organic"] = [{"rank": o.get("position"), "url": o.get("url"), "title": o.get("title"),
                        "domain": domain_of(o.get("url"))} for o in page.get("organicResults") or []]
    serp["paa"] = [q.get("question") for q in page.get("peopleAlsoAsk") or [] if q.get("question")]
    serp["related"] = [q.get("title") for q in page.get("relatedQueries") or [] if q.get("title")]
    overview = page.get("aiOverview") or {}
    if isinstance(overview, dict) and overview.get("content"):
        serp["ai_overview"] = {"text": overview["content"], "references": source_rows(overview.get("sources"))}
    return serp


def cmd_serp(args):
    provider = pick_provider(args.provider, ("dataforseo", "apify"))
    return serp_dataforseo(args) if provider == "dataforseo" else serp_apify(args)


# --- keywords ---------------------------------------------------------------------------------

def keyword_row(item):
    item = item or {}
    info = item.get("keyword_info") or {}
    return {"keyword": item.get("keyword"), "volume": info.get("search_volume"), "cpc": info.get("cpc"),
            "difficulty": (item.get("keyword_properties") or {}).get("keyword_difficulty"),
            "intent": (item.get("search_intent_info") or {}).get("main_intent")}


def by_volume(rows):
    return sorted((r for r in rows if r["keyword"]), key=lambda r: r["volume"] or 0, reverse=True)


def cmd_keywords(args):
    require("dataforseo")
    base = {"location_code": location_code(args), "language_code": args.lang}
    overview = dataforseo("dataforseo_labs/google/keyword_overview/live", {**base, "keywords": [args.keyword]})
    related = dataforseo("dataforseo_labs/google/related_keywords/live",
                         {**base, "keyword": args.keyword, "depth": 1, "limit": args.limit})
    suggestions = dataforseo("dataforseo_labs/google/keyword_suggestions/live",
                             {**base, "keyword": args.keyword, "limit": args.limit})
    overview_items = overview.get("items") or []
    related_rows = by_volume(keyword_row(i.get("keyword_data")) for i in related.get("items") or [])
    suggestion_rows = by_volume(keyword_row(i) for i in suggestions.get("items") or [])
    return {
        "provider": "dataforseo", "keyword": args.keyword, "country": args.country,
        "overview": keyword_row(overview_items[0]) if overview_items else None,
        "related": related_rows, "suggestions": suggestion_rows,
        "note": keywords_note(args.keyword, bool(overview_items), related_rows + suggestion_rows),
    }


def keywords_note(keyword, has_overview, rows):
    notes = ["DataForSEO floors very low volumes at 10/mo." if has_overview else
             "No keyword data returned: the term is likely below DataForSEO's volume floor."]
    if len({r["keyword"] for r in rows} - {keyword}) < 3:
        notes.append("Fewer than 3 related terms returned: top up secondary keywords from autocomplete, "
                     "PAA and related searches, marked Not measured.")
    return " ".join(notes)


def google_suggest(query, args):
    params = urllib.parse.urlencode({"client": "firefox", "hl": args.lang, "gl": args.country, "q": query})
    status, data = http("GET", "https://suggestqueries.google.com/complete/search?" + params)
    return data[1] if status == 200 and isinstance(data, list) and len(data) > 1 else []


def cmd_autocomplete(args):
    seeds = [args.keyword]
    seeds += [f"{args.keyword} {letter}" for letter in "abcdefghijklmnopqrstuvwxyz"]
    seeds += [f"{prefix} {args.keyword}" for prefix in AUTOCOMPLETE_PREFIXES]
    found = []
    for seed in seeds:
        for suggestion in google_suggest(seed, args):
            if suggestion.lower() != args.keyword.lower() and suggestion not in found:
                found.append(suggestion)
        time.sleep(0.1)
    return {"provider": "google-autocomplete", "keyword": args.keyword, "suggestions": found,
            "note": "Unfiltered. Drop suggestions that don't match the reader's intent before using them."}


# --- site (cannibalisation) -------------------------------------------------------------------

def match_terms(keyword):
    """Full phrase first, then adjacent content-word pairs. Single words match too much noise."""
    content = [w for w in re.findall(r"[a-z0-9]+", keyword.lower()) if w not in STOP_WORDS]
    pairs = [" ".join(pair) for pair in zip(content, content[1:])]
    return list(dict.fromkeys([keyword.lower()] + pairs[:2]))


def ranked_row(item):
    data = item.get("keyword_data") or {}
    serp_item = (item.get("ranked_serp_element") or {}).get("serp_item") or {}
    return {"keyword": data.get("keyword"), "volume": (data.get("keyword_info") or {}).get("search_volume"),
            "rank": serp_item.get("rank_group"), "url": serp_item.get("url")}


def page_row(item):
    organic = (item.get("metrics") or {}).get("organic") or {}
    top10 = sum(organic.get(k) or 0 for k in ("pos_1", "pos_2_3", "pos_4_10"))
    return {"url": item.get("page_address"), "est_monthly_traffic": organic.get("etv"), "keywords_top10": top10}


def cmd_site(args):
    require("dataforseo")
    base = {"target": domain_of(args.domain), "location_code": location_code(args), "language_code": args.lang}
    ranked, matched_on = [], None
    for term in match_terms(args.keyword):
        result = dataforseo("dataforseo_labs/google/ranked_keywords/live", {
            **base, "limit": 50, "filters": ["keyword_data.keyword", "like", f"%{term}%"],
            "order_by": ["keyword_data.keyword_info.search_volume,desc"]})
        ranked = [ranked_row(i) for i in result.get("items") or []]
        if ranked:
            matched_on = term
            break
    pages = dataforseo("dataforseo_labs/google/relevant_pages/live", {**base, "limit": 30})
    rows = [page_row(i) for i in pages.get("items") or []]
    return {"provider": "dataforseo", "domain": base["target"], "ranked_keywords": ranked,
            "matched_on": matched_on, "top_pages": rows,
            "note": None if ranked or rows else "No ranking data: the site is too small for DataForSEO's index. "
                                                 "Fall back to a site: search and the sitemap slugs."}


# --- scrape -----------------------------------------------------------------------------------

def write_page(folder, rank, url, markdown):
    rank = rank if isinstance(rank, int) else 99
    slug = re.sub(r"[^a-z0-9]+", "-", domain_of(url)).strip("-")
    header = f"<!-- mos-copy-brief rank={rank} url={url} words={word_count(markdown)} -->\n\n"
    (folder / f"{rank:02d}-{slug}.md").write_text(header + markdown, encoding="utf-8")


def scrape_firecrawl(candidates, limit, skipped, folder):
    scraped = []
    for row in candidates:
        if len(scraped) >= limit:
            break
        markdown, status, error = firecrawl_scrape(row["url"])
        if error:
            skipped.append({**row, "reason": error})
            if status in (401, 402):  # bad key or out of credits: every later page fails the same way
                break
            continue
        write_page(folder, row.get("rank"), row["url"], markdown)  # saved immediately: paid pages survive a crash
        scraped.append({"rank": row.get("rank"), "url": row["url"], "words": word_count(markdown)})
    return scraped


def index_by_url(items):
    """Apify may report the redirected URL, so index each item under both its URLs."""
    by_url = {}
    for item in items:
        for url in (item.get("url"), (item.get("crawl") or {}).get("loadedUrl")):
            if url:
                by_url[normalise_url(url)] = item
    return by_url


def scrape_apify(candidates, limit, skipped, folder):
    targets = candidates[:limit + 2]  # one batch run, so send a couple of spares for failures
    items = apify_run("apify~website-content-crawler", {
        "startUrls": [{"url": row["url"]} for row in targets], "maxCrawlDepth": 0,
        "maxCrawlPages": len(targets), "crawlerType": "playwright:adaptive", "saveMarkdown": True})
    by_url = index_by_url(items)
    scraped = []
    for row in targets:
        if len(scraped) >= limit:
            break
        markdown = (by_url.get(normalise_url(row["url"])) or {}).get("markdown")
        if not markdown:
            skipped.append({**row, "reason": "apify: no content returned"})
            continue
        write_page(folder, row.get("rank"), row["url"], markdown)
        scraped.append({"rank": row.get("rank"), "url": row["url"], "words": word_count(markdown)})
    return scraped


def cmd_scrape(args):
    serp = read_json_file(args.serp, "SERP file")
    folder = Path(args.dir)
    folder.mkdir(parents=True, exist_ok=True)
    candidates, skipped = [], []
    for row in serp.get("organic") or []:
        if is_ugc(row.get("url")):
            skipped.append({**row, "reason": "user-generated content (a content-gap signal, not a template)"})
        else:
            candidates.append(row)
    provider = pick_provider(args.provider, ("firecrawl", "apify"))
    scraper = scrape_firecrawl if provider == "firecrawl" else scrape_apify
    scraped = scraper(candidates, args.max, skipped, folder)
    if not scraped:
        reasons = "; ".join(sorted({s["reason"] for s in skipped}))[:300]
        raise ToolError(f"No competitor pages could be scraped with {provider}. Reasons: {reasons or 'no results'}")
    return {"provider": provider, "dir": str(folder), "scraped": scraped, "skipped": skipped}


# --- themes -----------------------------------------------------------------------------------

def header_int(attrs, name):
    digits = re.sub(r"[^\d]", "", attrs.get(name, ""))
    return int(digits) if digits else None


def read_page(path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    header = re.match(r"<!--\s*mos-copy-brief(.*?)-->", text)
    attrs = dict(re.findall(r"(\w+)=(\S+)", header.group(1))) if header else {}
    body = text[header.end():] if header else text
    words = header_int(attrs, "words")
    return {"rank": header_int(attrs, "rank"), "url": attrs.get("url", path.name),
            "words": words if words is not None else word_count(body), "headings": extract_headings(body)}


def word_target(pages):
    counts = sorted(p["words"] for p in pages)
    if not counts:
        return None
    low = max(sum(counts) // len(counts), int(median(counts)))
    high = max(low, min(counts[-1], low + 800))
    return {"pages": len(counts), "min": counts[0], "max": counts[-1], "average": sum(counts) // len(counts),
            "median": int(median(counts)), "target": f"{low:,}-{high:,}",
            "confidence": "high" if len(counts) >= 5 else "low (fewer than 5 pages analysed)"}


def theme_status(covering):
    if covering >= 3:
        return "table_stakes"
    return {2: "common", 1: "gap (only one competitor)", 0: "absent"}[covering]


def classify(pages):
    coverage = {theme: set() for theme in THEMES}
    examples = {theme: [] for theme in THEMES}
    unmatched = []
    for page in pages:
        for heading in (h for h in page["headings"] if h["level"] > 1):
            theme = match_theme(heading["text"])
            if theme is None:
                unmatched.append({"rank": page["rank"], "heading": heading["text"]})
                continue
            coverage[theme].add(page["url"])
            if len(examples[theme]) < 8:
                examples[theme].append({"rank": page["rank"], "heading": heading["text"]})
    return coverage, examples, unmatched


def cmd_themes(args):
    folder = Path(args.dir)
    pages = [read_page(p) for p in sorted(folder.glob("*.md"))] if folder.is_dir() else []
    if not pages:
        raise ToolError(f"No page files (*.md) found in {args.dir}. Run scrape first, or save tier-3 pages there.")
    usable = [p for p in pages if p["words"] >= args.min_words]
    coverage, examples, unmatched = classify(usable)
    themes = sorted(({"theme": t, "pages_covering": len(coverage[t]), "of": len(usable),
                      "status": theme_status(len(coverage[t])), "examples": examples[t]} for t in THEMES),
                    key=lambda row: row["pages_covering"], reverse=True)
    return {
        "pages_analysed": len(usable),
        "pages_too_thin": [{"url": p["url"], "words": p["words"]} for p in pages if p not in usable],
        "competitors": [{"rank": p["rank"], "url": p["url"], "words": p["words"],
                         "h1": next((h["text"] for h in p["headings"] if h["level"] == 1), None),
                         "headings": p["headings"][:40]} for p in usable],
        "themes": themes,
        "unmatched_headings": unmatched[:80],
        "word_count": word_target(usable),
    }


# --- chatgpt ----------------------------------------------------------------------------------

def chatgpt_dataforseo(args):
    body = {"keyword": args.keyword, "location_code": location_code(args), "language_code": args.lang}
    note = None
    try:
        result = dataforseo("ai_optimization/chat_gpt/llm_scraper/live/advanced", body)
    except ToolError as error:
        if body["location_code"] == US_LOCATION:
            raise
        result = dataforseo("ai_optimization/chat_gpt/llm_scraper/live/advanced",
                            {**body, "location_code": US_LOCATION})
        note = f"The request for your country failed ({error}); this answer was captured as United States."
    answer = result.get("markdown") or ""
    sources = (result.get("sources") or []) + (result.get("search_results") or [])
    if not sources:  # DataForSEO often leaves these empty; the answer's own links are the citations
        sources = [{"url": url} for url in re.findall(r"\]\((https?://[^)\s]+)\)", answer)]
    if not sources:
        note = (note + " " if note else "") + "ChatGPT answered without searching the web, so it cited no sources."
    return {"answer": answer, "sources": source_rows(sources),
            "fan_out_queries": result.get("fan_out_queries"), "note": note}


def chatgpt_apify(args):
    prompt = f"{args.keyword} (answer for someone in {country_entry(args)[1]})"
    items = apify_run("apify~chatgpt-search-scraper", {"queries": prompt})
    item = items[0] if items else {}
    answer = item.get("response") or item.get("answer") or item.get("text") or ""
    return {"answer": answer, "sources": source_rows(item.get("citations") or item.get("sources")),
            "prompt": prompt, "note": None}


def cmd_chatgpt(args):
    provider = pick_provider(args.provider, ("dataforseo", "apify"))
    result = chatgpt_dataforseo(args) if provider == "dataforseo" else chatgpt_apify(args)
    result["answer"] = result["answer"][:6000]
    return {"provider": provider, "keyword": args.keyword, **result}


# --- cli --------------------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(description="Research helper for mos-copy-brief.")
    sub = parser.add_subparsers(dest="command", required=True)

    def command(name, handler, keyword=False, provider=None):
        p = sub.add_parser(name)
        p.set_defaults(handler=handler)
        p.add_argument("--out", help="write JSON here instead of stdout")
        p.add_argument("--country", default="us", help="ISO country code, e.g. us, au, gb")
        p.add_argument("--lang", default="en")
        p.add_argument("--location-code", type=int, help="DataForSEO location code override")
        if keyword:
            p.add_argument("--keyword", required=True)
        if provider:
            p.add_argument("--provider", choices=provider)
        return p

    command("preflight", cmd_preflight).add_argument(
        "--use", type=parse_use, default="all",
        help="all (default), free (tier 3), or a comma list of providers, e.g. apify or dataforseo,apify")
    command("serp", cmd_serp, keyword=True, provider=("dataforseo", "apify"))
    command("keywords", cmd_keywords, keyword=True).add_argument("--limit", type=int, default=20)
    command("autocomplete", cmd_autocomplete, keyword=True)
    command("site", cmd_site, keyword=True).add_argument("--domain", required=True)
    scrape = command("scrape", cmd_scrape, provider=("firecrawl", "apify"))
    scrape.add_argument("--serp", required=True, help="serp.json from the serp command")
    scrape.add_argument("--dir", required=True, help="folder to write page markdown into")
    scrape.add_argument("--max", type=int, default=8, help="readable pages to collect")
    themes = command("themes", cmd_themes)
    themes.add_argument("--dir", required=True)
    themes.add_argument("--min-words", type=int, default=300)
    command("chatgpt", cmd_chatgpt, keyword=True, provider=("dataforseo", "apify"))
    return parser


def main():
    load_env()
    args = build_parser().parse_args()
    try:
        result = args.handler(args)
    except ToolError as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(2)
    spend = {name: round(value, 4) for name, value in COST.items() if value}
    if spend:
        result["spend"] = spend
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out}" + (f" | spend {spend}" if spend else ""), file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
