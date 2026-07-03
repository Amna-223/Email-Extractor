import re
from urllib import response

# def clean_and_format_email(messy_email):
#     """Cleans up the obfuscated email matches."""
#     email = messy_email.strip()
#     email = re.sub(r'\s+', '', email)
    
#     # Standardize the '@' symbol (including your space-at-space addition)
#     at_patterns = [r'\[at\]', r'\(at\)', r'-at-', r'\{at\}', r'at'] #why did I add the last one? because some people write "at" without any brackets or dashes, so we need to catch that too
#     for pattern in at_patterns:
#         email = re.sub(pattern, '@', email, flags=re.IGNORECASE)
        
#     # Standardize the '.' symbol
#     dot_patterns = [r'\[dot\]', r'\(dot\)', r'-dot-', r'\{dot\}', r'dot']
#     for pattern in dot_patterns:
#         email = re.sub(pattern, '.', email, flags=re.IGNORECASE)
        
#     return email


def clean_and_format_email(messy_email):
    """Cleans up obfuscated email matches — order-safe version."""
    email = messy_email.strip()

    # Step 1: Replace obfuscated '@' patterns FIRST, while spacing still exists
    # Order matters: bracketed forms first, then space-boundary form
    email = re.sub(r'\[at\]|\(at\)|\{at\}|-at-', '@', email, flags=re.IGNORECASE)
    email = re.sub(r'\s+at\s+', '@', email, flags=re.IGNORECASE)

    # Step 2: Replace obfuscated '.' patterns, same order logic
    email = re.sub(r'\[dot\]|\(dot\)|\{dot\}|-dot-', '.', email, flags=re.IGNORECASE)
    email = re.sub(r'\s+dot\s+', '.', email, flags=re.IGNORECASE)

    # Step 3: NOW it's safe to strip remaining whitespace
    email = re.sub(r'\s+', '', email)

    return email

test_cases = [
    "natalie@gmail.com",              # should stay unchanged
    "chat@company.com",               # should stay unchanged
    "info [at] domain [dot] com",     # should become info@domain.com
    "support (at) sitepoint (dot) com",
    "contact -at- business -dot- com",
]

for t in test_cases:
    print(t, "->", clean_and_format_email(t))



# products = response.css("div.product")
# for prod in products:
#     title = prod.css("a h2::text").get()
#     price = prod.css("span.price::text").get()
#     url = prod.css("a::attr(href)").get()

#     yield response.follow(
#         url, 
#         callback=self.parse_product,)
    
# next = response.css("li.next a::attr(href)").get()
# if next:
#     yield response.follow(next, callback=self.parse)