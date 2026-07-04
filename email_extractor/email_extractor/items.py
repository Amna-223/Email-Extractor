import scrapy
 
 
class EmailItem(scrapy.Item):
    """
    Represents one candidate email found during a crawl.
 
    Fields
    ------
    email       : the address itself, fully normalised (lowercase, no whitespace)
    source_url  : the exact page URL where it was found
    found_via   : extraction method — one of:
                    'mailto'    – pulled from a <a href="mailto:..."> attribute
                    'json_ld'   – found inside a JSON-LD <script> block
                    'footer'    – found inside a <footer> tag's HTML
                    'regex'     – plain-text regex match (lowest signal)
    domain      : the email's domain part  (e.g. "sitepoint.com")
    site_domain : the crawled site's root domain (e.g. "sitepoint.com")
                  stored here so the pipeline can compare without re-parsing
    confidence  : set by the pipeline after validation —
                    'high' | 'medium' | 'low'
                  left empty ('') by the spider; the pipeline fills it in
    mx_valid    : bool — does the domain have at least one MX record?
                  set by the pipeline
    smtp_result : one of 'pass' | 'fail' | 'inconclusive'
                  set by the pipeline
    """
 
    email       = scrapy.Field()
    source_url  = scrapy.Field()
    found_via   = scrapy.Field()
    domain      = scrapy.Field()
    site_domain = scrapy.Field()
    confidence  = scrapy.Field()   # filled by pipeline
    mx_valid    = scrapy.Field()   # filled by pipeline
    smtp_result = scrapy.Field()   # filled by pipeline