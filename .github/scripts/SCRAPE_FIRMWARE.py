import json
import re
import os
from datetime import datetime

os.makedirs('TEMP/OUTPUT', exist_ok=True)

def parse_scraped_html():
    """Parse HTML file and extract firmware table"""
    try:
        with open('firmware_raw.html', 'r', encoding='utf-8') as f:
            html = f.read()
        
        lookups = {}
        
        # Match table rows: <tr>...<td>...</td><td>...</td><td>...</td><td>...</td>...</tr>
        pattern = r'<tr[^>]*>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>\s*<td[^>]*>(.*?)</td>'
        matches = re.finditer(pattern, html, re.DOTALL)
        
        for match in matches:
            # Extract text from HTML (remove tags)
            ups_id_raw = re.sub(r'<[^>]+>', '', match.group(2)).replace('\n', '').strip()
            ups_id = re.sub(r'[^\d]', '', ups_id_raw)  # Remove asterisks and extra chars
            
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
        
        with open('TEMP/OUTPUT/TEST.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Scraped and parsed: {len(lookups)} UPS entries")
        return len(lookups)
    
    except Exception as e:
        print(f"Parsing failed: {e}")
        return 0

if __name__ == "__main__":
    parse_scraped_html()
