import json
import urllib.request
import urllib.error
import re
import os
from datetime import datetime

os.makedirs('NetApp/SANtricity', exist_ok=True)

def get_latest_santricity_version():
    """Scrape NetApp SANtricity latest release version"""
    
    version = None
    
    # Try MySupportURL first
    try:
        my_support_url = "https://mysupport.netapp.com/site/products/all/details/eseries-santricityos/downloads-tab"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        
        req = urllib.request.Request(my_support_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # Try to find "Download Latest Release [XX.XXR#]"
        match = re.search(r'Download Latest Release\s*\[\s*(?P<rel>\d{2}\.\d{2}R\d+)\s*\]', html, re.IGNORECASE)
        if not match:
            # Fallback: just find the version pattern
            match = re.search(r'(?P<rel>\d{2}\.\d{2}R\d+)', html, re.IGNORECASE)
        
        if match:
            version = match.group('rel')
            print(f"Found SANtricity version from MySupportURL: {version}")
            return version
    
    except Exception as e:
        print(f"MySupportURL scrape failed: {e}")
    
    # Fallback to NetApp docs
    try:
        docs_url = "https://docs.netapp.com/us-en/e-series/whats-new.html"
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        
        req = urllib.request.Request(docs_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # Try R-style version first
        match = re.search(r'(?P<rel>\d{2}\.\d{2}R\d+)', html, re.IGNORECASE)
        if match:
            version = match.group('rel')
            print(f"Found SANtricity version from docs (R-style): {version}")
            return version
        
        # Try Version XX.XX format (treat as R0)
        match = re.search(r'(?i)\bVersion\s+(?P<majmin>\d{2}\.\d{2})\b', html)
        if match:
            version = f"{match.group('majmin')}R0"
            print(f"Found SANtricity version from docs (Version style): {version}")
            return version
    
    except Exception as e:
        print(f"NetApp docs scrape failed: {e}")
    
    return None

def parse_release_tag(release_tag):
    """Parse release tag like '11.90R4' into components"""
    if not release_tag:
        return None
    
    match = re.match(r'^(?P<maj>\d{2})\.(?P<min>\d{2})R(?P<r>\d+)$', release_tag)
    if match:
        return {
            "major": int(match.group('maj')),
            "minor": int(match.group('min')),
            "r": int(match.group('r')),
            "full": release_tag
        }
    
    return None

def scrape_santricity():
    """Main scraper function"""
    version = get_latest_santricity_version()
    
    if not version:
        print("Could not retrieve SANtricity version")
        return None
    
    parsed = parse_release_tag(version)
    
    output = {
        "description": "NetApp E-Series SANtricity OS Latest Release",
        "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
        "latestVersion": version,
        "parsed": parsed
    }
    
    with open('NetApp/SANtricity/SANtricity_Latest.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Scraped SANtricity version: {version}")
    return version

if __name__ == "__main__":
    scrape_santricity()
