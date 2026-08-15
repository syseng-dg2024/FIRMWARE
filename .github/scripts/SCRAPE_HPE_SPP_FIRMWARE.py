import json
import xml.etree.ElementTree as ET
import urllib.request
import os
from datetime import datetime

os.makedirs('HPE/SPP', exist_ok=True)

def scrape_hpe_spp_manifest():
    """Scrape HPE Service Pack for ProLiant (SPP) Gen10 firmware manifest XML"""
    
    url = "https://downloads.linux.hpe.com/SDR/repo/spp-gen10/2026.07.00.00/manifest/meta.xml"
    
    try:
        print(f"Fetching SPP manifest from: {url}")
        
        # Download the XML
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
                version = version_elem.attrib.get('value', 'N/A') if version_elem is not None else None
                
                if name and version:
                    # Use product ID as key
                    product_id = product.attrib.get('id', '')
                    lookups[product_id] = {
                        "name": name,
                        "version": version
                    }
            except Exception as e:
                continue
        
        output = {
            "description": "HPE Service Pack for ProLiant (SPP) Gen10 Firmware Manifest",
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
    scrape_hpe_spp_manifest()
