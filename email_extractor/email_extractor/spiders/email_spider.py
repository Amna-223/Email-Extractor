import re
import json
import html
from urllib import response
import scrapy
from urllib.parse import urlparse
from email_extractor.items import EmailItem
 
 
# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------
 
# Broad pattern — catches standard emails AND obfuscated ones
# (e.g.  name [at] domain [dot] com,  name(at)domain.com,  name at domain dot com)
BROAD_EMAIL_PATTERN = re.compile(
    r'[a-zA-Z0-9._%+\-]+'
    r'\s*(?:@|\[at\]|\(at\)|\{at\}|-at-|\s+at\s+)\s*'
    r'[a-zA-Z0-9.\-]+'
    r'\s*(?:\.|\[dot\]|\(dot\)|\{dot\}|-dot-|\s+dot\s+)\s*'
    r'[a-zA-Z]{2,}',
    re.IGNORECASE
)
 
# Strict sanity-check pattern applied AFTER normalisation
CLEAN_EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
)
 
 
# ---------------------------------------------------------------------------
# Normalisation helpers  (your existing logic, kept exactly as-is)
# ---------------------------------------------------------------------------
 
def clean_and_format_email(raw: str) -> str:
    """
    Converts obfuscated email strings into standard form.
    Order matters — bracketed forms first, then space-boundary form.
    """
    email = raw.strip()
 
    # Step 1: Replace obfuscated '@' — bracketed before bare-word
    email = re.sub(r'\[at\]|\(at\)|\{at\}|-at-', '@', email, flags=re.IGNORECASE)
    email = re.sub(r'\s+at\s+', '@', email, flags=re.IGNORECASE)
 
    # Step 2: Replace obfuscated '.' — same order
    email = re.sub(r'\[dot\]|\(dot\)|\{dot\}|-dot-', '.', email, flags=re.IGNORECASE)
    email = re.sub(r'\s+dot\s+', '.', email, flags=re.IGNORECASE)
 
    # Step 3: Strip all remaining whitespace now that symbols are in place
    email = re.sub(r'\s+', '', email)
 
    return email.lower()
 
 
def clean_extension_junk(email: str) -> str:
    """
    Removes trailing garbage extensions that get picked up by the regex.
    e.g.  support@sitepoint.com.Screenshots  ->  support@sitepoint.com
    Rule: if the last dot-segment starts with a capital letter OR is > 4 chars, drop it.
    """
    parts = email.split('.')
    if len(parts) > 1:
        last = parts[-1]
        if last and (last[0].isupper() or len(last) > 4):
            email = '.'.join(parts[:-1])
    return email
 
 
def normalise_email(raw: str) -> str | None:
    """
    Full normalisation pipeline for a single raw match.
    Returns a clean email string, or None if it's structurally invalid.
    """
    step0 = html.unescape(raw)
    if re.search(r'[<>"\']', step0):
        return None
    step1 = clean_and_format_email(step0)
    step2 = clean_extension_junk(step1)
 
    if '@' not in step2:
        return None

    username, domain = step2.split('@', 1)
    if '/' in username or '\\' in username:
        return None
    
    if len(username) < 2:
        return None
 
    if not CLEAN_EMAIL_PATTERN.match(step2):
        return None
 
    return step2
 
 
def get_site_domain(url: str) -> str:
    """Returns the bare domain (no www.) for a given URL."""
    netloc = urlparse(url).netloc.lower()
    return netloc.replace('www.', '')
 
 
# ---------------------------------------------------------------------------
# Per-method extractors  (priority order: mailto > json_ld > footer > regex)
# ---------------------------------------------------------------------------
 
def extract_mailto(response) -> list[tuple[str, str]]:
    """
    Pulls emails from  <a href="mailto:someone@example.com">  attributes.
    Highest-confidence source — someone explicitly linked this address.
    Returns list of (email, 'mailto') tuples.
    """
    results = []
    for href in response.css('a[href^="mailto:"]::attr(href)').getall():
        raw = href.replace('mailto:', '').split('?')[0].strip()
        clean = normalise_email(raw)
        if clean:
            results.append((clean, 'mailto'))
    return results
 
 
def extract_json_ld(response) -> list[tuple[str, str]]:
    """
    Searches JSON-LD <script type="application/ld+json"> blocks for email fields.
    Common on modern sites — structured data often includes contactPoint.email.
    Returns list of (email, 'json_ld') tuples.
    """
    results = []
    for script_text in response.css('script[type="application/ld+json"]::text').getall():
        try:
            data = json.loads(script_text)
        except (json.JSONDecodeError, ValueError):
            continue
 
        # Walk the JSON tree (could be a dict or a list of dicts)
        emails_in_json = _walk_json_for_emails(data)
        for raw in emails_in_json:
            clean = normalise_email(raw)
            if clean:
                results.append((clean, 'json_ld'))
    return results
 
 
def _walk_json_for_emails(node) -> list[str]:
    """Recursively walks any JSON structure and collects strings that look like emails."""
    found = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in ('email', 'contactemail', 'e-mail'):
                if isinstance(value, str) and '@' in value:
                    found.append(value)
            else:
                found.extend(_walk_json_for_emails(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_walk_json_for_emails(item))
    return found
 
 
def extract_footer(response) -> list[tuple[str, str]]:
    """
    Searches the raw HTML of <footer> elements for emails.
    Higher confidence than free-text regex because it's a known contact zone.
    Returns list of (email, 'footer') tuples.
    """
    results = []
    for footer_html in response.css('footer').getall():
        raw_matches = BROAD_EMAIL_PATTERN.findall(footer_html)
        for raw in raw_matches:
            clean = normalise_email(raw)
            if clean:
                results.append((clean, 'footer'))
    return results
 
 
def extract_regex(response) -> list[tuple[str, str]]:
    """
    Fallback: runs the broad regex over all visible text on the page.
    Lowest-confidence source — catches the most but also the most noise.
    Returns list of (email, 'regex') tuples.
    """
    results = []
    page_text = ' '.join(response.css('body *::text').getall())
    raw_matches = BROAD_EMAIL_PATTERN.findall(page_text)
    for raw in raw_matches:
        clean = normalise_email(raw)
        if clean:
            results.append((clean, 'regex'))
    return results
 
 
# ---------------------------------------------------------------------------
# The Spider
# ---------------------------------------------------------------------------
 
class EmailSpider(scrapy.Spider):
    name = 'email_spider'
 
    def __init__(self, url=None, *args, **kwargs):
        """
        Usage:
            scrapy crawl email_spider -a url=https://sitepoint.com
        """

        self.priority_keywords = [
            'contact', 'contact us', 'conatct-us' 'about', 'team', 'advertise', 'advertising',
            'info', 'support', 'help', 'career', 'jobs', 'hire',
            'press', 'media', 'partnership', 'sponsor', 'work-with-us',
            'get-in-touch', 'reach-us', 'connect', 'staff', 'people'
        ]
        super().__init__(*args, **kwargs)
 
        if not url:
            raise ValueError("Provide a start URL:  -a url=https://example.com")
 
        # Normalise missing scheme — mirrors your existing :// check
        if '://' not in url:
            url = 'https://' + url.strip()
 
        self.start_urls = [url]
        self.site_domain = get_site_domain(url)
 
        # Tracks emails already yielded this run — avoids duplicate items
        self._seen_emails: set[str] = set()
    

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url,
                meta={
                    "playwright": True,
                    "playwright_include_page": False,
                },
                callback=self.parse
            )
 
    # ------------------------------------------------------------------
    # Scrapy entry point — called automatically for every fetched page
    # ------------------------------------------------------------------

 
    def parse(self, response):
        """
        Called by Scrapy for every successfully fetched page.
 
        Responsibilities:
          1. Run all four extractors in priority order
          2. Yield EmailItem for each new candidate  (pipeline validates them)
          3. Yield new Requests for same-domain links  (Scrapy queues them)
        """
        self.logger.info(f"Parsing: {response.url}")
 
        # --- 1. Extract candidates, priority order ---
        # We merge all found emails, keeping the highest-priority source
        # if the same address was found via multiple methods on this page.
        email_map: dict[str, str] = {}  # email -> found_via
 
        for email, method in (
            extract_mailto(response)    # highest signal
            + extract_json_ld(response)
            + extract_footer(response)
            + extract_regex(response)   # lowest signal
        ):
            # Priority: only update if this method is better than what we already have
            if email not in email_map:
                email_map[email] = method
            else:
                priority = ['mailto', 'json_ld', 'footer', 'regex']
                if priority.index(method) < priority.index(email_map[email]):
                    email_map[email] = method
 
        # --- 2. Yield items ---
        for email, found_via in email_map.items():
            if email in self._seen_emails:
                continue
            self._seen_emails.add(email)
 
            yield EmailItem(
                email       = email,
                source_url  = response.url,
                found_via   = found_via,
                domain      = email.split('@')[-1],
                site_domain = self.site_domain,
                confidence  = '',            # pipeline fills this
                mx_valid    = None,          # pipeline fills this
                smtp_result = '',            # pipeline fills this
            )
 
        # --- 3. Follow links — priority pages pehle ---
        priority_links = []
        normal_links = []

        for href in response.css('a::attr(href)').getall():
            full_url = response.urljoin(href)
            parsed = urlparse(full_url)

            if self.site_domain not in parsed.netloc:
                continue  # bahar ki sites skip
            
            # Check karo kya yeh priority page hai
            url_lower = full_url.lower()
            link_text = ' '.join(response.css(f'a[href="{href}"]::text').getall()).lower()

            is_priority = any(
                kw in url_lower or kw in link_text
                for kw in self.priority_keywords
            )

            if is_priority:
                priority_links.append(full_url)
            else:
                normal_links.append(full_url)

        # Priority links pehle yield karo
        for url in priority_links:
            yield scrapy.Request(
                url,
                meta={"playwright": True},
                callback=self.parse,
                priority=10  # ← Scrapy pehle inhe process karta hai
            )

        # Normal links baad mein
        for url in normal_links:
            yield scrapy.Request(
                url,
                meta={"playwright": True},
                callback=self.parse,
                priority=0
            )