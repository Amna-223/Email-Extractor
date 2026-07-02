import re
import socket
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def does_domain_exist(domain):
    """
    Internet par check karta hai k kya domain waqai exist karti hai.
    Agar domain fake hogi ya sirf sentence ka hissa hogi, tou yeh False return karega.
    """
    try:
        # socket.gethostbyname() internet par domain ka IP address dhoondta hai
        socket.gethostbyname(domain)
        return True
    except socket.gaierror:
        # Agar domain internet par nahi milti (Fake/Junk Domain like runtime.function)
        return False

def clean_and_format_email(messy_email):
    """Cleans up the obfuscated email matches."""
    email = messy_email.strip()
    email = re.sub(r'\s+', '', email)
    
    # Standardize the '@' symbol (including your space-at-space addition)
    at_patterns = [r'\[at\]', r'\(at\)', r'-at-', r'\{at\}', r'at']
    for pattern in at_patterns:
        email = re.sub(pattern, '@', email, flags=re.IGNORECASE)
        
    # Standardize the '.' symbol
    dot_patterns = [r'\[dot\]', r'\(dot\)', r'-dot-', r'\{dot\}', r'dot']
    for pattern in dot_patterns:
        email = re.sub(pattern, '.', email, flags=re.IGNORECASE)
        
    return email

def validate_and_refine_email(messy_email, target_url):
    """
    Aap k btaey huay mutabiq validation stage:
    1. Splits and cleans extra words like .Screenshots
    2. Live DNS Verification via socket (Strategy B)
    3. Allows generic domains (Gmail, Yahoo, etc.)
    4. Cross-references other domains with the target_url domain
    """
    # Base URL se main domain nikalna (e.g., https://www.sitepoint.com -> sitepoint.com)
    parsed_target = urlparse(target_url).netloc.lower()
    target_domain = parsed_target.replace('www.', '')

    # --- STEP 1: Split the Extension (.Screenshots Issue Fix) ---
    parts = messy_email.split('.')
    if len(parts) > 1:
        last_part = parts[-1]
        # Agar aakhri part Capital letter se shuru ho rha ho ya 4 chars se bara ho (e.g., Screenshots)
        if last_part and (last_part[0].isupper() or len(last_part) > 4):
            # Tou us extra part ko nikal do aur baqi email jor lo
            cleaned_email = ".".join(parts[:-1])
        else:
            cleaned_email = messy_email
    else:
        cleaned_email = messy_email

    if '@' not in cleaned_email:
        return None
        
    # Email se us ka domain alag karein (e.g., support@sitepoint.com -> sitepoint.com)
    email_domain = cleaned_email.split('@')[-1].lower()

    # --- STEP 2: Real Domain Existence Check ---
    # Agar internet par yeh domain mapped hi nahi hai, tou drop it
    if not does_domain_exist(email_domain):
        return None

    # --- STEP 3: Allow Generic Domains ---
    generic_domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com', 'icloud.com']
    if email_domain in generic_domains:
        return cleaned_email

    # --- STEP 4: Domain Cross-Reference Check ---
    # Agar email ka domain target_url k domain se match karta hai tou return karein
    if target_domain in email_domain or email_domain in target_domain:
        return cleaned_email

    # Agar match nahi karta (jaise github.com on sitepoint.com), tou drop it
    return None

def extract_emails_from_text(text, target_url):
    """Finds, processes, and strictly validates emails from plain text."""
    # Broad pattern tracking including your optimization for literal spaces around 'at'
    broad_pattern = r'[a-zA-Z0-9._%+-]+\s*(?:@|\[at\]|\(at\)|-at-|\s+at\s+)\s*[a-zA-Z0-9.-]+\s*(?:\.|\[dot\]|\(dot\)|-dot-|\s+dot\s+)\s*[a-zA-Z]{2,}'
    
    raw_matches = re.findall(broad_pattern, text, re.IGNORECASE)
    
    cleaned_emails = set()
    for match in raw_matches:
        # Step A: Format standard symbols
        formatted_email = clean_and_format_email(match)
        # Step B: Pass through strict structural and live filter gates
        valid_email = validate_and_refine_email(formatted_email, target_url)
        
        if valid_email:
            cleaned_emails.add(valid_email)
        
    return cleaned_emails

def get_internal_contact_links(soup, base_url):
    """Scans the homepage for high-probability internal contact links."""
    contact_links = set()
    keywords = ['contact', 'about', 'team', 'info', 'support', 'help', 'career', 'contact us', 'about-us', 'customer-service', 'get-in-touch']
    
    main_domain = urlparse(base_url).netloc 
    
    for anchor in soup.find_all('a', href=True):
        href = anchor['href'].strip()
        link_text = anchor.get_text().lower()
        
        if any(keyword in href.lower() or keyword in link_text for keyword in keywords):
            full_url = urljoin(base_url, href) 
            
            if urlparse(full_url).netloc == main_domain: 
                contact_links.add(full_url)
                
    return contact_links

def email_extractor_engine(target_url):
    """The main manager that coordinates fetching, crawling, and extracting."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    final_emails = set()
    
    print(f"\n[1/3] Hitting homepage: {target_url}")
    try:
        response = requests.get(target_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"--> Homepage failed with status code: {response.status_code}")
            return final_emails 
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. Check Homepage for emails right away
        homepage_text = soup.get_text()
        homepage_emails = extract_emails_from_text(homepage_text, target_url)
        final_emails.update(homepage_emails)
        
        # 2. Find high-probability internal links
        links_to_crawl = get_internal_contact_links(soup, target_url) 
        print(f"[2/3] Found {len(links_to_crawl)} relevant internal pages to check.")
        
        # 3. Crawl those specific internal pages
        print("[3/3] Scanning internal pages...")
        for link in links_to_crawl:
            try:
                if link == target_url:
                    continue
                    
                sub_response = requests.get(link, headers=headers, timeout=7)
                if sub_response.status_code == 200:
                    sub_soup = BeautifulSoup(sub_response.text, "html.parser")
                    sub_emails = extract_emails_from_text(sub_soup.get_text(), target_url)
                    final_emails.update(sub_emails) 
            except Exception:
                continue
                
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        
    return final_emails

# --- Run a Test ---
test_site = "https://www.sitepoint.com/"
results = email_extractor_engine(test_site)
print("\n--- FINAL RESULTS ---")
print(results if results else "No emails found.")