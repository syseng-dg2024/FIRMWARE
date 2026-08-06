import json
import re
import os
import gzip
from datetime import datetime

os.makedirs('APC/UPS', exist_ok=True)

def scrape_se_com():
    """Try to scrape SE.com with various techniques"""
    import urllib.request
    import urllib.error
    
    url = "https://www.se.com/us/en/faqs/FA279197/"
    
    # Try multiple User-Agent strings
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    ]
    
    for user_agent in user_agents:
        try:
            headers = {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://www.se.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')
            
            if html and 'Access Denied' not in html and '403' not in html:
                print(f"Successfully scraped with UA: {user_agent[:50]}...")
                return html
        
        except Exception as e:
            print(f"Failed with UA {user_agent[:40]}...: {e}")
            continue
    
    return None

def parse_scraped_html(html):
    """Parse HTML file and extract firmware table"""
    if not html:
        print("No HTML content to parse")
        return 0
    
    try:
        lookups = {}
        
        # Match table rows
        pattern = r'<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>'
        matches = re.finditer(pattern, html, re.DOTALL)
        
        for match in matches:
            ups_id_raw = re.sub(r'<[^>]+>', '', match.group(2)).replace('\n', '').strip()
            ups_id = re.sub(r'[^\d]', '', ups_id_raw)
            
            fw_raw = re.sub(r'<[^>]+>', '', match.group(4)).replace('\n', ' ').strip()
            fw_match = re.search(r'UPS\s+[\d\.]+', fw_raw)
            
            if ups_id and ups_id.isdigit() and fw_match:
                firmware = fw_match.group(0).replace('  ', ' ')
                lookups[ups_id] = firmware
        
        output = {
            "description": "APC UPS Firmware Lookup Table - ID to Latest Version mapping",
            "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
            "lookups": lookups
        }
        
        with open('APC/UPS/UPS_Firmware_Lookup.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Scraped and parsed: {len(lookups)} UPS entries")
        return len(lookups)
    
    except Exception as e:
        print(f"Parsing failed: {e}")
        return 0

if __name__ == "__main__":
    html = scrape_se_com()
    parse_scraped_html(html)
