#!/usr/bin/env python3
"""
RSS News Fetcher — Iran-Gulf War 2026
Fetches BBC World News and Economic Times Markets via RSS.

Usage:
  uv run src/news_agent.py

Schedule: 8 AM daily (via cron)
Output: Console print with classified headlines + market context
"""

from datetime import datetime
import json
import os

import feedparser
from config import VAULT_DAILY_DIR
from market_pulse import get_data_from_cache

# Consolidated to vault Daily subfolder
NEWS_DIR = str(VAULT_DAILY_DIR)


def _news_path(date_str: str = None, ext: str = "json") -> str:
    """Return path to today's (or given date's) news file in the configured vault."""
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    os.makedirs(NEWS_DIR, exist_ok=True)
    return os.path.join(NEWS_DIR, f"news_{date_str}.{ext}")


def save_news_cache(articles: list, date_str: str = None) -> str:
    """Save articles list to vault as news_YYYY-MM-DD.json. Returns file path."""
    date_key = date_str or datetime.now().strftime("%Y-%m-%d")
    path = _news_path(date_key, "json")
    payload = {
        "date": date_key,
        "fetched_at": datetime.now().isoformat(),
        "article_count": len(articles),
        "articles": articles,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    # Mirror to TinyDB (deduped)
    try:
        from db import insert_articles
        insert_articles(articles, date_key)
    except Exception as e:
        print(f"  ⚠️  TinyDB write skipped: {e}")

    return path


def load_news_cache(date_str: str = None) -> list | None:
    """Load articles from cache for the given date. Returns None if not found."""
    path = _news_path(date_str, "json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f).get("articles")

SOURCES = [
    {
        "name": "BBC World News (RSS)",
        "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml",
    },
    {
        "name": "Economic Times Markets",
        "rss_url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    },
]

KEYWORDS = [
    # Geopolitical / war
    "iran", "hormuz", "gulf", "israel", "strike", "ceasefire",
    "missile", "drone", "nuclear", "khamenei", "netanyahu", "trump",
    "war", "beirut", "hezbollah", "sanctions", "attack", "uae", "kuwait",
    # Energy / commodities
    "oil", "energy", "production", "brent", "opec", "saudi",
    "tanker", "refinery", "crude", "wti", "barrel", "lng",
    # India macro / market
    "nifty", "sensex", "rbi", "repo rate", "rupee", "usdinr",
    "hdfc", "reliance", "infosys", "tcs", "icici",
    "nifty bank", "banknifty", "fii", "dii", "earnings", "quarterly results",
    "rate cut", "inflation", "cpi", "gdp", "fiscal",
]

# Articles matching ANY of these patterns are excluded at intake.
# Rule: only factual macro-impact events. No opinion, no analysis, no human interest.
EXCLUDE_PATTERNS = [
    # Opinion / analysis / explainers — not factual events
    " | ",          # Guardian byline format: "Title | Author Name"
    "| opinion", "| letters", "guardian view", "guardian weekly",
    " – podcast", " – cartoon", "in pictures", "in maps:",
    "bbc visits", "briefing:", "explainer", "explained:",
    "what is ", "what are ", "why did ", "how did ", "how iran", "how the ",
    "who is ", "who are ", "analysis:", "comment:", "column:",
    # Human interest / sentiment — no macro impact
    "asylum", "diaspora", "norooz", "celebrates persian", "escape to claim",
    "effigies", "rally", "protest", "funeral", "procession",
    "burn trump", "burn netanyahu", "vigil", "demonstration",
    # Sports / entertainment
    "football", "soccer", "afcon", "world cup", "f1 cancel", "gp cancel",
    "cricket", "olympic",
    # Domestic crime / legal unrelated to infrastructure
    "charged with murder", "charged in death", "drops charges against soldiers",
    # Western domestic politics tangential to war
    "britain's poorest", "poorest lands", "illinois primaries", "senegal",
    "mamdani",
    # Background/feature pieces — not events
    "evading internet blocks", "anti-establishment protests",
    "defense contractors. we can't",
    "daily life under", "how young iranians", "iranians describe",
    "what iranians are being told", "we've been speaking to iranians",
    "a corner of north london",
    # ── ET Markets: analyst attribution / opinion ─────────────────────────────
    # Pattern: "... : Analyst Name" or "says Expert Name" — not factual events
    ": analysts", ": analyst",          # "Rupee may test 94-95: Analysts"
    "smart money",                       # "where smart money is hiding"
    "says unmesh", "says nischal", "says pashupati", "says arvind sanger",
    "says siddhartha", "says jignanshu", "says unmesh",
    # ── ET Markets: stock tips / trading recommendations ─────────────────────
    "market trading guide",              # "Market Trading Guide: Buy X for 9% gains"
    "trading setup",                     # "here's the trading setup for today"
    "market prediction",                 # "Market Prediction for Nifty & Bank Nifty"
    "market outlook",                    # "Market Outlook & NIFTY Outlook"
    "upside potential",                  # "10 stocks with 60% upside potential"
    "short term gains",                  # trading tips
    "in your portfolio",                 # "Are these in your portfolio?"
    "buy the dip",                       # trading advice
    "sector to watch",                   # "Sector To Watch: X seen key beneficiary"
    "don't buy ", "don't sell ",         # "Don't buy HDFC Bank yet..."
    "what should investor",              # "What should investors do?"
    "stocks to buy", "stocks to watch",  # stock tips
    "target price",                      # broker target articles
    "pick winning stock",                # educational
    # ── ET Markets: speculative / forward-looking analysis ───────────────────
    "what to expect",                    # "What to expect for Sensex, Nifty"
    "more pain or",                      # "More pain or time to buy the dip?"
    "can sensex", "can nifty",           # "Can Sensex extend gains for second session?"
    "factors that will", "factors that decide",  # "5 factors that will decide market mood"
    "triggers behind",                   # "7 triggers behind today's market crash" — listicle
    "timeless guide",                    # "Pat Dorsey's timeless guide to picking stocks"
    "playbook",                          # "Options market eyes 2022 playbook"
    "steer stock market",                # "crude oil prices to steer stock markets"
    "holiday-shortened week",            # analyst preview pieces
    # ── Off-topic geographies ─────────────────────────────────────────────────
    "ukraine", "russian attack",         # Russia-Ukraine conflict
    "west bank", "gaza",                 # Palestine conflict (different from Iran war)
    "robert mueller",                    # US domestic
    "ice agents", "dhs shutdown",        # US domestic immigration
    "abc staff", "abc workers",          # Australia
    "sudan",                             # Sudan conflict
    "un warns earth", "climate being",   # Climate (not macro for this portfolio)
    # ── Irrelevant company / real estate / financial industry ─────────────────
    "land parcel", "godrej properties",  # Indian real estate
    "uae real estate",                   # Real estate
    "berkshire hathaway",                # Irrelevant US equity
    "credit suisse",                     # Old news / background
    "hedge fund nets",                   # Hedge fund interest stories
    "timeless guide", "pat dorsey",      # Educational / fund manager content
    "zomato", "swiggy",                  # Food delivery — not macro
    "uti amc", "kotak explains",         # Fund house commentary
    # ── Remaining leakers ────────────────────────────────────────────────────
    "not acting as safe haven",          # "Why gold is not acting as safe haven" — analysis
    "no let up",                         # "No let up in war; Nifty can fall to..." — technical prediction
    ": arvind sanger",                   # Analyst attribution without "says"
    "why is israel", "why is hamas",     # Explainer ("Why is Israel targeting...")
]

# ── Intake relevance scoring ──────────────────────────────────────────────────
# Same logic used in the Mar-19 DB cleanup. Applied after keyword match to rank
# and cap at MAX_GEO_PER_DAY geopolitical articles before storing.

import re as _re

_EVENT   = _re.compile(r'\b(attack|struck|strike|kill(?:ed)?|bomb|missile|explosion|fire|shut|block|expel|surge|ceasefire|deal|launch|hit|destroy|wound|crash|drone|forces|troops|intercept|offensive|escalat|sanction|deploy|withdraw)\b', _re.IGNORECASE)
_RELEVANT= _re.compile(r'\b(iran|hormuz|brent|gulf|qatar|uae|saudi|tehran|south.pars|gasfield|strait|nifty|rupee|rbi|sensex|oil.price|crude|lng|refinery|supply.disruption|india.vix|usdinr)\b', _re.IGNORECASE)
_NOISE   = _re.compile(r'\b(opinion|explains|analysis|briefing|weekly|column|visits|rally|protest|funeral|background|lessons|gamblers?|haircut)\b', _re.IGNORECASE)
_OFFTOPIC= _re.compile(r'\b(west.bank|gaza|hezbollah|lebanon|palestine|palestinian|settler|kurdish|kurds)\b', _re.IGNORECASE)

MAX_GEO_PER_DAY = 5

def _score(title: str) -> int:
    """Relevance score for portfolio-context macro news. Higher = more important."""
    t = title or ""
    if t.startswith("[BREAKING]"):
        return -100          # always a duplicate of a non-BREAKING article
    s  =  len(_EVENT.findall(t))    * 10
    s  += len(_RELEVANT.findall(t)) * 15
    s  -= len(_NOISE.findall(t))    * 8
    s  -= len(_OFFTOPIC.findall(t)) * 12
    if "|" in t: s -= 10    # byline in title → likely opinion
    return s


def _fetch_rss_fallback(source: dict, keywords: list) -> list:
    """
    Fetch articles from a source's RSS feed using feedparser.
    Used as fallback when Playwright scraping returns 0 articles.
    Returns list of article dicts in the same shape as Playwright results.
    """
    rss_url = source.get("rss_url")
    if not rss_url:
        return []
    try:
        feed = feedparser.parse(rss_url)
        articles = []
        for entry in feed.entries:
            title = str(entry.get("title") or "").strip()
            summary = str(entry.get("summary") or "").strip()[:200]
            url = str(entry.get("link") or "")
            published = str(entry.get("published") or "")
            title_lower = title.lower()
            text = (title + " " + summary).lower()
            if len(title) < 10:
                continue
            if any(p in title_lower for p in EXCLUDE_PATTERNS):
                continue
            if any(k in text for k in keywords):
                articles.append({
                    "title": title,
                    "source": source["name"] + " (RSS)",
                    "url": url,
                    "summary": summary,
                    "time": published,
                    "published": published,
                })
        return articles
    except Exception as e:
        print(f"  ⚠️  RSS fallback failed for {source['name']}: {e}")
        return []


def fetch_news(sources=None):
    """
    Fetch articles from all sources via RSS (feedparser).
    Sources: Reuters Business, Economic Times Markets.
    Returns list of article dicts with title, source, url, summary, time.
    """
    if sources is None:
        sources = SOURCES

    print("[1] Fetching news via RSS...")
    articles = []

    for source in sources:
        rss_articles = _fetch_rss_fallback(source, KEYWORDS)
        articles.extend(rss_articles)
        print(f"  ✅ {source['name']} (RSS): {len(rss_articles)} articles")

    # Deduplicate by title
    seen = set()
    unique = []
    for a in articles:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    print(f"  ✅ {len(unique)} relevant articles total")

    path = save_news_cache(unique)
    print(f"  💾 Saved to {path}")
    return unique


def save_digest_md(digest: str, date_str: str = None) -> str:
    """Write the markdown digest to vault as news_YYYY-MM-DD.md. Returns file path."""
    path = _news_path(date_str, "md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(digest)
    return path


# Backward-compat alias — mcp_server.py imports this name
def fetch_rss_feeds():
    return fetch_news()


def classify_articles(articles):
    """Classify articles into Escalation / Supply Impact / Diplomatic / Other."""
    print("[2] Classifying articles...")

    escalation_kw = [
        "strike", "attack", "missile", "drone", "bomb", "killed", "nuclear",
        "war", "shoot", "destroyed", "explosion", "airstrike", "target",
    ]
    supply_kw = [
        "production", "cut", "bpd", "export", "supply", "hormuz", "shutdown",
        "lng", "refinery", "tanker", "oil", "brent", "crude", "price", "barrel",
    ]
    peace_kw = [
        "ceasefire", "peace", "talk", "negotiat", "mediat", "off-ramp",
        "deal", "terms", "truce", "diplomatic",
    ]

    for article in articles:
        text = (article["title"] + " " + article.get("summary", "")).lower()
        # BREAKING ticker items are almost always escalation
        if article.get("time") == "Breaking":
            article["type"] = "🔴 Escalation"
        elif any(k in text for k in escalation_kw):
            article["type"] = "🔴 Escalation"
        elif any(k in text for k in supply_kw):
            article["type"] = "🟡 Supply Impact"
        elif any(k in text for k in peace_kw):
            article["type"] = "🟢 Diplomatic"
        else:
            article["type"] = "⚪ Other"

    # ── Trim to top MAX_GEO_PER_DAY geopolitical + top 5 other ──────────────
    geo_types = {"🔴 Escalation", "🟡 Supply Impact", "🟢 Diplomatic"}
    geo   = sorted([a for a in articles if a.get("type") in geo_types],   key=lambda x: -_score(x["title"]))
    other = sorted([a for a in articles if a.get("type") not in geo_types], key=lambda x: -_score(x["title"]))
    articles = geo[:MAX_GEO_PER_DAY] + other[:5]
    dropped = len(geo) - min(len(geo), MAX_GEO_PER_DAY)
    if dropped:
        print(f"  ✂️  Trimmed {dropped} lower-relevance geo articles (kept top {MAX_GEO_PER_DAY})")

    # Overwrite cache with typed + trimmed articles
    save_news_cache(articles)
    print(f"  ✅ Classified {len(articles)} articles")
    return articles


def get_market_context():
    """Get latest market data from SQLite."""
    try:
        df = get_data_from_cache()
        if df is None or len(df) == 0:
            return None
        latest = df.tail(1).to_dicts()[0]
        return {
            "brent": latest.get("Brent") or 0,
            "vix": latest.get("IndiaVIX") or 0,
            "nifty": latest.get("Nifty50") or 0,
            "gold": latest.get("Gold") or 0,
        }
    except Exception as e:
        print(f"  ⚠️  Could not load market data: {e}")
        return None


def format_digest(articles):
    """Format classified articles as a markdown digest."""
    print("[3] Formatting digest...")

    date_str = datetime.now().strftime("%B %d, %Y")
    digest = f"## {date_str} — Daily News Brief\n\n"

    market = get_market_context()
    if market:
        digest += (
            f"**Market:** Brent ${market['brent']:.2f} | "
            f"VIX {market['vix']:.1f} | "
            f"Nifty {market['nifty']:.0f} | "
            f"Gold ${market['gold']:.0f}\n\n"
        )

    if not articles:
        digest += "No significant news today.\n\n"
        digest += "**Action:** Hold position. Monitor Nifty 23,500 trigger.\n"
        return digest

    for article_type in ["🔴 Escalation", "🟡 Supply Impact", "🟢 Diplomatic", "⚪ Other"]:
        matching = [a for a in articles if a.get("type") == article_type]
        if not matching:
            continue
        digest += f"### {article_type}\n"
        for a in matching:
            clean_title = a["title"].replace("[BREAKING] ", "")
            prefix = "**[BREAKING]** " if "BREAKING" in a["title"] else ""
            time_str = f" ({a['time']})" if a.get("time") and a["time"] not in ("", "Breaking") else ""
            digest += f"- {prefix}**{clean_title}**{time_str} — {a['source']}\n"
        digest += "\n"

    digest += "**Action:** Review. No auto-trades. Capital preservation first.\n"
    print("  ✅ Digest formatted")
    return digest


def main():
    """Run the news digest generator."""
    print("=" * 70)
    print("📡 Daily News Digest — Iran-Gulf War 2026 (RSS)")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    articles = fetch_news()
    articles = classify_articles(articles)
    digest = format_digest(articles)

    md_path = save_digest_md(digest)
    print(digest)
    print("=" * 70)
    print(f"✅ Complete. Articles: {len(articles)}")
    print(f"📄 Digest saved: {md_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
