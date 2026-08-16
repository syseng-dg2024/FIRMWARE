import json
import xml.etree.ElementTree as ET
import urllib.request
import re
import os
from datetime import datetime

os.makedirs('HPE/SPP', exist_ok=True)

# Critical firmware components to match
CRITICAL_COMPONENTS = {
    "BIOS": ["System ROM", "Firmware Flash", "BIOS"],
    "iLO": ["iLO 5", "iLO 4", "iLO 6", "Lights-Out"],
    "Power Management": ["Power Management Controller", "PMC"],
    "Power Supply": ["Power Supply Firmware", "PSU"],
    "Innovation Engine": ["Innovation Engine", "IE Firmware"],
    "SPS": ["Server Platform Services", "SPS Firmware"],
    "Network Adapters": ["Ethernet", "Network", "NIC", "Adapter"],
    "Storage": ["Storage Controller", "RAID", "SAS", "HBA", "Fibre Channel"],
    "Video": ["Video Controller", "iLO Virtual"],
}

def get_latest_spp_version():
    """Get the latest SPP Gen10 version from the repository listing"""
    
    base_url = "https://downloads.linux.hpe.com/SDR/repo/spp-gen10"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(base_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        # Extract version directories using href pattern
        version_pattern = r'href="(\d{4}\.\d{2}\.\d{2}\.\d{2})/"'
        versions = re.findall(version_pattern, html)
        
        if not versions:
            return None
        
        # Remove duplicates and sort
        versions = list(set(versions))
        versions_sorted = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
        latest_version = versions_sorted[-1]
        
        return latest_version
    
    except Exception as e:
        print(f"Error fetching directory listing: {e}")
        return None

def get_component_category(name):
    """Determine category for a firmware component"""
    if not name:
        return "Other"
    
    name_lower = name.lower()
    
    for category, keywords in CRITICAL_COMPONENTS.items():
        for keyword in keywords:
            if keyword.lower() in name_lower:
                return category
    
    return None

def is_critical_component(name):
    """Check if a firmware component is critical"""
    return get_component_category(name) is not None

def scrape_hpe_spp_firmware(version):
    """Scrape HPE SPP Gen10 firmware manifest and filter for critical components only"""
    
    url = f"https://downloads.linux.hpe.com/SDR/repo/spp-gen10/{version}/manifest/meta.xml"
    
    try:
        print(f"Fetching SPP manifest from: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()
        
        root = ET.fromstring(xml_content)
        meta = root.find('meta')
        products = meta.findall('product')
        
        print(f"Found {len(products)} total firmware components")
        
        components_dict = {}
        
        for product in products:
            try:
                # Get the firmware name
                name_elem = product.find('.//name_xlate')
                name = name_elem.text if name_elem is not None else None
                
                # Get the version
                version_elem = product.find('.//version')
                fw_version = version_elem.attrib.get('value', 'N/A') if version_elem is not None else None
                
                if name and fw_version:
                    if is_critical_component(name):
                        product_id = product.attrib.get('id', '')
                        category = get_component_category(name)
                        
                        components_dict[product_id] = {
                            "category": category,
                            "name": name,
                            "version": fw_version
                        }
            
            except Exception as e:
                continue
        
        output = {
            "description": "HPE Service Pack for ProLiant (SPP) Gen10 Critical Firmware Components",
            "sppVersion": version,
            "url": url,
            "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
            "totalComponents": len(components_dict),
            "components": components_dict
        }
        
        with open('HPE/SPP/SPP_Gen10_Firmware_Manifest.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Extracted {len(components_dict)} critical firmware components")
        return len(components_dict)
    
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    latest_version = get_latest_spp_version()
    if latest_version:
        scrape_hpe_spp_firmware(latest_version)
    else:
        print("Could not determine latest SPP version")
