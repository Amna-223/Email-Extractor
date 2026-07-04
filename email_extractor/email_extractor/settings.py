# =============================================================================
#  Scrapy Settings — Email Extractor
# =============================================================================
#
#  These are the knobs you'll touch most often.
#  Everything else Scrapy handles automatically.
# =============================================================================
 
BOT_NAME    = 'email_extractor'
SPIDER_MODULES        = ['email_extractor.spiders']
NEWSPIDER_MODULE      = 'email_extractor.spiders'
 
 
# -----------------------------------------------------------------------------
# Crawl limits  — adjust these per site
# -----------------------------------------------------------------------------
 
# How many clicks deep from the start URL to follow links.
# 2 is usually enough for contact pages (homepage -> /contact -> done).
# Raise to 3-4 for large sites where emails are buried deeper.
DEPTH_LIMIT = 2
 
# Stop crawling after this many pages, regardless of depth.
# Prevents runaway crawls on huge sites like sitepoint.com.
CLOSESPIDER_PAGECOUNT = 10
 
# Max concurrent requests — how many pages to fetch in parallel.
# 8 is a reasonable default; lower to 4 if you're getting blocked.
CONCURRENT_REQUESTS = 8
 
# Seconds of delay between requests to the same domain.
# 0 = no delay (fast but rude). 1.0 = polite. 2.0 = very polite.
DOWNLOAD_DELAY = 1.0
 
# Randomise delay between 0.5x and 1.5x DOWNLOAD_DELAY
# so you don't look like a bot with a precise interval.
RANDOMIZE_DOWNLOAD_DELAY = True
 
 
# -----------------------------------------------------------------------------
# Politeness
# -----------------------------------------------------------------------------
 
# Respect the site's robots.txt. Set False only if you own the site
# or have explicit permission to ignore it.
ROBOTSTXT_OBEY = True
 
# Auto-throttle adjusts download delay based on server response time.
# Keeps your crawl from hammering a slow server.
AUTOTHROTTLE_ENABLED      = True
AUTOTHROTTLE_START_DELAY  = 1.0    # initial delay (seconds)
AUTOTHROTTLE_MAX_DELAY    = 10.0   # maximum delay if server is slow
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0  # avg concurrent requests per server
 
 
# -----------------------------------------------------------------------------
# Identity
# -----------------------------------------------------------------------------
 
# Looks like a real browser. Some sites block Python's default user-agent.
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)
 
# Don't send a Referer header (avoids some bot-detection triggers).
REFERER_ENABLED = False
 
 
# -----------------------------------------------------------------------------
# Pipeline — validation + confidence scoring
# -----------------------------------------------------------------------------
 
# The number (300) is the pipeline's priority.
# Lower number = runs earlier. Use 300 for a single pipeline.
# If you add a second pipeline later (e.g. save to CSV), give it 400.
ITEM_PIPELINES = {
    'email_extractor.pipelines.EmailValidationPipeline': 300,
}
 
 
# -----------------------------------------------------------------------------
# Output
# -----------------------------------------------------------------------------
 
# Feed export — writes results to a JSON file automatically.
# Remove or comment out if you'd rather handle output manually.
FEEDS = {
    'results.json': {
        'format':    'json',
        'encoding':  'utf8',
        'overwrite': True,          # start fresh each run
        'fields': [                 # column order in the output
            'email',
            'confidence',
            'found_via',
            'source_url',
            'domain',
            'site_domain',
            'mx_valid',
            'smtp_result',
        ],
    },
}
 
 
# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
 
# 'INFO'    — see each page visited and each email kept/dropped
# 'WARNING' — quieter, only problems
# 'DEBUG'   — very verbose, shows every request + pipeline decision
LOG_LEVEL = 'INFO'
 
 
# -----------------------------------------------------------------------------
# Misc
# -----------------------------------------------------------------------------
 
# Disable cookies — email crawling doesn't need sessions, and cookies
# can trigger bot-detection or GDPR consent walls.
COOKIES_ENABLED = False
 
# Suppress the Scrapy telemetry warning.
TELNETCONSOLE_ENABLED = False
 
# Default request headers.
DEFAULT_REQUEST_HEADERS = {
    'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
}

# Playwright integration
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"