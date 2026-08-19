import json
import xml.etree.ElementTree as ET
import urllib.request
import re
import os
from datetime import datetime

os.makedirs('HPE/SPP', exist_ok=True)

# Only include critical hardware components
CRITICAL_DEVICES = [
    "iLO",
    "System ROM",
    "System BIOS",
    "BIOS",
    "Smart Array",
    "Power Management",
    "Power Supply",
    "Innovation Engine",
    "Server Platform Services",
    "Intelligent Provisioning",
]

# SPP generations to scrape
SPP_GENERATIONS = [
    "spp-gen9",
    "spp-gen10",
    "spp-gen11",
    "spp-gen12",
    "spp-gen13",
]

def normalize_version(version_string):
    """Normalize version by removing leading zeros from each segment"""
    if not version_string:
        return version_string
    
    # Extract only the version number part (before any space or parenthesis)
    # e.g., "v3.66 (04/01/2026)" -> "3.66"
    version_string = version_string.strip()
    
    # Remove 'v' prefix if present
    if version_string.startswith('v') or version_string.startswith('V'):
        version_string = version_string[1:]
    
    # Extract only the numeric part before any space or special character
    match = re.match(r'^([\d.]+)', version_string)
    if match:
        version_string = match.group(1)
    
    try:
        parts = version_string.split('.')
        normalized_parts = [str(int(part)) for part in parts if part]
        return '.'.join(normalized_parts)
    except ValueError:
        # If normalization fails, return original string
        return version_string

def get_latest_spp_version(generation):
    """Get the latest SPP version for a specific generation"""
    base_url = f"https://downloads.linux.hpe.com/SDR/repo/{generation}"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(base_url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            html = response.read().decode('utf-8')
        
        version_pattern = r'href="(\d{4}\.\d{2}\.\d{2}\.\d{2})/"'
        versions = re.findall(version_pattern, html)
        
        if not versions:
            return None
        
        versions = list(set(versions))
        versions_sorted = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
        return versions_sorted[-1]
    
    except Exception as e:
        return None

def is_critical_device(device_name):
    """Check if device is critical"""
    if not device_name:
        return False
    
    name_lower = device_name.lower()
    for critical in CRITICAL_DEVICES:
        if critical.lower() in name_lower:
            return True
    return False

def scrape_hpe_spp_firmware(generation, version):
    """Scrape HPE SPP firmware with Target as key and normalized versions"""
    url = f"https://downloads.linux.hpe.com/SDR/repo/{generation}/{version}/manifest/meta.xml"
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()
        
        root = ET.fromstring(xml_content)
        payloads = root.findall('.//payload')
        
        # Dictionary keyed by Target
        components = {}
        
        for payload in payloads:
            try:
                # Get DeviceClass from payload level (can be None)
                device_class_elem = payload.find('DeviceClass')
                device_class = device_class_elem.text if device_class_elem is not None else None
                
                # Get all devices in this payload
                devices = payload.findall('.//Device')
                
                for device in devices:
                    try:
                        device_name_elem = device.find('DeviceName')
                        target_elem = device.find('Target')
                        version_elem = device.find('Version')
                        
                        device_name = device_name_elem.text if device_name_elem is not None else None
                        
                        # Only include critical devices
                        if device_name and is_critical_device(device_name):
                            if target_elem is not None and version_elem is not None:
                                target_id = target_elem.text
                                fw_version = normalize_version(version_elem.text)
                                
                                # Key by Target ID
                                components[target_id] = {
                                    "Name": device_name,
                                    "Version": fw_version,
                                    "DeviceClass": device_class
                                }
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        return components, len(components)
    
    except Exception as e:
        return {}, 0

def main():
    all_results = {}
    
    for generation in SPP_GENERATIONS:
        # Get latest version for this generation
        latest_version = get_latest_spp_version(generation)
        
        if latest_version:
            components, count = scrape_hpe_spp_firmware(generation, latest_version)
            
            if count > 0:
                all_results[generation] = {
                    "version": normalize_version(latest_version),
                    "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
                    "totalComponents": count,
                    "components": components
                }
    
    # Output combined results
    output = {
        "description": "HPE Service Pack for ProLiant (SPP) Critical Firmware Components - All Generations",
        "generationCount": len(all_results),
        "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
        "generations": all_results
    }
    
    with open('HPE/SPP/SPP_Firmware_Lookup.json', 'w') as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    main()
