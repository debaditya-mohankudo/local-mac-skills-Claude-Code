# Safari URL allowlist
# Only these domains are allowed to be opened by the safari skill.
# Subdomains are matched automatically (github.com also allows gist.github.com).
#
# To disable the allowlist and allow ALL URLs, set DISABLE_ALLOWLIST=true.
# WARNING: Disabling removes all URL restrictions — Claude can open any URL.

DISABLE_ALLOWLIST=false

ALLOWED_URLS=(
    "google.com"
    "news.ycombinator.com"
    "github.com"
    "wikipedia.org"
    "reuters.com"
    "bbc.com"
    "apnews.com"
    "aljazeera.com"
    "cnbc.com"
    "theguardian.com"
    "whitehouse.gov"
    "federalregister.gov"
    "finance.yahoo.com"
    "screener.in"
    "youtube.com"
    "nseindia.com"
    "bseindia.com"
    "moneycontrol.com"
    "tickertape.in"
    "trendlyne.com"
    "tijorifinance.com"
    "economictimes.indiatimes.com"
    "livemint.com"
    "ndtvprofit.com"
    "tradingview.com"
    "investing.com"
    "upstox.com"
    "marketwatch.com"
    "bloomberg.com"
    "linkedin.com"
    "mcx.in"
    "mcxlive.org"
    "claude.ai"
    "openclaw.ai"
)
