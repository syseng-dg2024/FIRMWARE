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
    """Scrape HPE SPP firmware with DeviceClass as key"""
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
        
        # Dictionary to track (name, device_class, version) for deduplication
        device_dedup = {}
        
        for payload in payloads:
            try:
                # Get DeviceClass from payload level
                device_class_elem = payload.find('DeviceClass')
                device_class = device_class_elem.text if device_class_elem is not None else "Unknown"
                
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
                                fw_version = version_elem.text
                                
                                # Create dedup key: (name, device_class, version)
                                dedup_key = (device_name, device_class, fw_version)
                                
                                # Only keep first target_id per dedup key
                                if dedup_key not in device_dedup:
                                    device_dedup[dedup_key] = {
                                        "Target": target_id,
                                        "Name": device_name,
                                        "Version": fw_version
                                    }
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        # Convert to output format keyed by DeviceClass
        components = {}
        for dedup_key, info in device_dedup.items():
            device_class = dedup_key[1]  # device_class is the second element in dedup_key
            components[device_class] = {
                "Target": info["Target"],
                "Name": info["Name"],
                "Version": info["Version"]
            }
        
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
                    "version": latest_version,
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
    
    with open('HPE/SPP/SPP_All_Generations_Firmware_Manifest.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Scraped {len(all_results)} SPP generations")

if __name__ == "__main__":
    main()
