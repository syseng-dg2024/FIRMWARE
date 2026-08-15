import json
import xml.etree.ElementTree as ET
import urllib.request
import re
import os
from datetime import datetime

os.makedirs('HPE/SPP', exist_ok=True)

def get_latest_spp_version():
    """Get the latest SPP Gen10 version from the repository listing"""
    
    base_url = "https://downloads.linux.hpe.com/SDR/repo/spp-gen10"
    
    try:
        print(f"Fetching directory listing from: {base_url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(base_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # Extract version directories (format: YYYY.MM.DD.DD)
        # Pattern: [DIR] 2026.07.00.00/
        version_pattern = r'\[DIR\]\s+(\d{4}\.\d{2}\.\d{2}\.\d{2})/'
        versions = re.findall(version_pattern, html)
        
        if not versions:
            print("No SPP versions found")
            return None
        
        # Sort versions and get the latest
        versions_sorted = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
        latest_version = versions_sorted[-1]
        
        print(f"Found {len(versions_sorted)} SPP versions")
        print(f"Latest version: {latest_version}")
        
        return latest_version
    
    except Exception as e:
        print(f"Error fetching directory listing: {e}")
        return None

def scrape_hpe_spp_manifest(version):
    """Scrape HPE SPP Gen10 firmware manifest XML for a specific version"""
    
    url = f"https://downloads.linux.hpe.com/SDR/repo/spp-gen10/{version}/manifest/meta.xml"
    
    try:
        print(f"Fetching SPP manifest from: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()
        
        # Parse XML
        root = ET.fromstring(xml_content)
        meta = root.find('meta')
        products = meta.findall('product')
        
        print(f"Found {len(products)} firmware components")
        
        lookups = {}
        
        for product in products:
            try:
                # Get the firmware name
                name_elem = product.find('.//name_xlate')
                name = name_elem.text if name_elem is not None else None
                
                # Get the version
                version_elem = product.find('.//version')
                fw_version = version_elem.attrib.get('value', 'N/A') if version_elem is not None else None
                
                if name and fw_version:
                    # Use product ID as key
                    product_id = product.attrib.get('id', '')
                    lookups[product_id] = {
                        "name": name,
                        "version": fw_version
                    }
            except Exception as e:
                continue
        
        output = {
            "description": "HPE Service Pack for ProLiant (SPP) Gen10 Firmware Manifest",
            "sppVersion": version,
            "url": url,
            "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
            "totalComponents": len(lookups),
            "lookups": lookups
        }
        
        with open('HPE/SPP/SPP_Gen10_Firmware_Manifest.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Extracted {len(lookups)} firmware components to SPP_Gen10_Firmware_Manifest.json")
        return len(lookups)
    
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    latest_version = get_latest_spp_version()
    if latest_version:
        scrape_hpe_spp_manifest(latest_version)
    else:
        print("Could not determine latest SPP version")
