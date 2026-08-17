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
        print(f"Error fetching {generation} directory: {e}")
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
    """Scrape HPE SPP firmware with all targets listed per DeviceClass"""
    url = f"https://downloads.linux.hpe.com/SDR/repo/{generation}/{version}/manifest/meta.xml"
    
    try:
        print(f"  Fetching {generation} {version}...")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            xml_content = response.read()
        
        root = ET.fromstring(xml_content)
        payloads = root.findall('.//payload')
        
        # Dictionary to group all targets per (device_class, name, version)
        device_groups = {}
        
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
                                
                                # Create grouping key: (device_class, name, version)
                                group_key = (device_class, device_name, fw_version)
                                
                                # Add target to this group
                                if group_key not in device_groups:
                                    device_groups[group_key] = {
                                        "Name": device_name,
                                        "Version": fw_version,
                                        "Targets": []
                                    }
                                
                                device_groups[group_key]["Targets"].append(target_id)
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        # Convert to output format keyed by DeviceClass
        components = {}
        for group_key, info in device_groups.items():
            device_class = group_key[0]  # device_class is first element
            
            # Remove duplicates from Targets list while preserving order
            unique_targets = []
            seen = set()
            for target in info["Targets"]:
                if target not in seen:
                    unique_targets.append(target)
                    seen.add(target)
            
            components[device_class] = {
                "Name": info["Name"],
                "Version": info["Version"],
                "Targets": unique_targets
            }
        
        return components, len(components)
    
    except Exception as e:
        print(f"    Error scraping: {e}")
        return {}, 0

def main():
    print("Scraping HPE SPP firmware across all generations...\n")
    
    all_results = {}
    
    for generation in SPP_GENERATIONS:
        print(f"Processing {generation}:")
        
        # Get latest version for this generation
        latest_version = get_latest_spp_version(generation)
        
        if latest_version:
            print(f"  Latest version: {latest_version}")
            components, count = scrape_hpe_spp_firmware(generation, latest_version)
            
            if count > 0:
                all_results[generation] = {
                    "version": latest_version,
                    "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
                    "totalComponents": count,
                    "components": components
                }
                print(f"  Extracted {count} critical firmware components")
            else:
                print(f"  No critical components found")
        else:
            print(f"  Could not determine latest version")
        
        print()
    
    # Output combined results
    output = {
        "description": "HPE Service Pack for ProLiant (SPP) Critical Firmware Components - All Generations",
        "generationCount": len(all_results),
        "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
        "generations": all_results
    }
    
    with open('HPE/SPP/SPP_Firmware_Lookup.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"Completed scraping {len(all_results)} SPP generations")

if __name__ == "__main__":
    main()
