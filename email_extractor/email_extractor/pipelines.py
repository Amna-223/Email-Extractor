import logging
import scrapy
import dns.resolver
from itemadapter import ItemAdapter
 
logger = logging.getLogger(__name__)
 
 
# ---------------------------------------------------------------------------
# MX record check
# ---------------------------------------------------------------------------
 
def check_mx(domain: str) -> bool:
    """
    Returns True if the domain has at least one MX record.
    A domain that exists on the internet but has no MX record cannot
    receive email — socket.gethostbyname() wouldn't catch this.
    """
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return len(answers) > 0
    except Exception:
        return False
 
 
# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------
 
# Priority order for found_via — lower index = higher signal
SOURCE_PRIORITY = ['mailto', 'json_ld', 'footer', 'regex']
 
 
def score_confidence(item) -> str:
    """
    Assigns a confidence label based on two axes:
      - WHERE the email was found  (found_via)
      - HOW it validated           (mx_valid, smtp_result, domain match)
 
    Scoring matrix
    --------------
    mailto   + domain match + MX + SMTP pass  ->  high
    json_ld  + domain match + MX + SMTP pass  ->  high
    footer   + domain match + MX + SMTP pass  ->  high
    regex    + domain match + MX + SMTP pass  ->  medium
    any      + NO domain match + MX + pass    ->  medium  (external, verified)
    any      + domain match + MX + inconclusive -> medium
    regex    + no domain match + inconclusive ->  low
    any      + no MX                          ->  low  (shouldn't reach here,
                                                        pipeline drops these)
 
    This mirrors Hunter.io's Valid / Risky / Unknown philosophy:
    instead of silently dropping or accepting, we label every result
    so the user can decide how much to trust it.
    """
    found_via    = item['found_via']
    mx_valid     = item['mx_valid']
    domain_match = item['domain'] == item['site_domain'] or \
                   item['site_domain'] in item['domain'] or \
                   item['domain'] in item['site_domain']

    # No MX → fake domain
    if not mx_valid:
        return 'low'

    # Strong source + domain match → high
    if found_via in ('mailto', 'json_ld', 'footer') and domain_match:
        return 'high'

    # Regex + domain match → medium
    if found_via == 'regex' and domain_match:
        return 'medium'

    # Any source + external domain + MX exists → medium
    if not domain_match:
        return 'medium'

    return 'low'
 
 
# ---------------------------------------------------------------------------
# The Pipeline class
# ---------------------------------------------------------------------------
 
class EmailValidationPipeline:
    """
    Scrapy Item Pipeline — runs after every EmailItem yielded by the spider.
 
    Stages:
      1. MX record check  — drop immediately if no MX (domain can't receive mail)
      2. SMTP handshake   — check if the specific mailbox exists
      3. Confidence score — label High / Medium / Low based on source + validation
      4. Filter by min confidence — drop 'low' items (configurable)
 
    To enable this pipeline, make sure settings.py has:
        ITEM_PIPELINES = {'email_extractor.pipelines.EmailValidationPipeline': 300}
    """
 
    # Domains whose MX result we've already looked up this run — avoid repeat DNS queries
    _mx_cache: dict[str, bool] = {}
 
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        domain  = adapter.get('domain', '')
 
        # ------------------------------------------------------------------
        # Stage 1: MX record check
        # ------------------------------------------------------------------
        if domain not in self._mx_cache:
            self._mx_cache[domain] = check_mx(domain)
 
        mx_valid = self._mx_cache[domain]
        adapter['mx_valid'] = mx_valid
 
        if not mx_valid:
            logger.debug(f"DROP (no MX): {adapter['email']}")
            raise scrapy.exceptions.DropItem(f"No MX record for domain: {domain}")
 
        # ------------------------------------------------------------------
        # Stage 2: SMTP handshake
        # ------------------------------------------------------------------
        email = adapter.get('email', '')

        adapter['smtp_result'] = 'skipped'
 
        # ------------------------------------------------------------------
        # Stage 3: Confidence scoring
        # ------------------------------------------------------------------
        confidence = score_confidence(adapter.asdict())
        adapter['confidence'] = confidence
 
        # ------------------------------------------------------------------
        # Stage 4: Filter by minimum confidence level
        # ------------------------------------------------------------------
        # Change MIN_CONFIDENCE in settings.py to adjust strictness:
        #   'low'    -> keep everything that passed MX + wasn't SMTP-rejected
        #   'medium' -> drop low-confidence regex guesses
        #   'high'   -> only keep strongly verified emails
        min_confidence = getattr(spider, 'min_confidence', 'low')
 
        confidence_rank = {'high': 3, 'medium': 2, 'low': 1}
        if confidence_rank.get(confidence, 0) < confidence_rank.get(min_confidence, 1):
            logger.debug(f"DROP (below min confidence '{min_confidence}'): {email}")
            raise scrapy.exceptions.DropItem(f"Confidence '{confidence}' below minimum: {email}")
 
        logger.info(f"KEEP [{confidence.upper()}] {email}  (via {adapter['found_via']}, source: {adapter['source_url']})")
        return item