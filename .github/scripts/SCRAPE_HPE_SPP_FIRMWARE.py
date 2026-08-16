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
        
        version_pattern = r'href="(\d{4}\.\d{2}\.\d{2}\.\d{2})/"'
        versions = re.findall(version_pattern, html)
        
        if not versions:
            return None
        
        versions = list(set(versions))
        versions_sorted = sorted(versions, key=lambda v: tuple(map(int, v.split('.'))))
        return versions_sorted[-1]
    
    except Exception as e:
        print(f"Error fetching directory listing: {e}")
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

def compare_versions(v1, v2):
    """Compare two version strings - returns True if v1 > v2"""
    try:
        v1_parts = tuple(map(int, v1.replace('.', '').split()))
        v2_parts = tuple(map(int, v2.replace('.', '').split()))
        return v1_parts > v2_parts
    except:
        return v1 > v2

def scrape_hpe_spp_firmware(version):
    """Scrape HPE SPP Gen10 firmware with DeviceClass - keep latest per device"""
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
        payloads = root.findall('.//payload')
        
        print(f"Found {len(payloads)} payload blocks")
        
        # Dictionary to track device name -> latest version info
        device_latest = {}
        
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
                                
                                # Check if this device name already exists and if this is a newer version
                                if device_name not in device_latest:
                                    device_latest[device_name] = {
                                        "target_id": target_id,
                                        "version": fw_version,
                                        "device_class": device_class
                                    }
                                else:
                                    # Compare versions - keep the newer one
                                    existing_version = device_latest[device_name]["version"]
                                    if compare_versions(fw_version, existing_version):
                                        device_latest[device_name] = {
                                            "target_id": target_id,
                                            "version": fw_version,
                                            "device_class": device_class
                                        }
                    except Exception as e:
                        continue
            except Exception as e:
                continue
        
        # Convert to output format keyed by target_id
        components = {}
        for device_name, info in device_latest.items():
            components[info["target_id"]] = {
                "name": device_name,
                "version": info["version"],
                "device_class": info["device_class"]
            }
        
        output = {
            "description": "HPE Service Pack for ProLiant (SPP) Gen10 Critical Firmware Components",
            "sppVersion": version,
            "url": url,
            "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
            "totalComponents": len(components),
            "components": components
        }
        
        with open('HPE/SPP/SPP_Gen10_Firmware_Manifest.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Extracted {len(components)} critical firmware components with DeviceClass")
        return len(components)
    
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    latest_version = get_latest_spp_version()
    if latest_version:
        scrape_hpe_spp_firmware(latest_version)
    else:
        print("Could not determine latest SPP version")
