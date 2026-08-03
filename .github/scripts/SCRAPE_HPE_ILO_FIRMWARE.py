import json
import requests
import os
from datetime import datetime

os.makedirs('APC/UPS', exist_ok=True)

def scrape_hpe_ilo_firmware():
    """Scrape HPE iLO firmware versions using the REST API"""
    
    # Collection IDs for each iLO version
    collections = {
        "iLO4": "MTX-b5848d0ffeab4506",
        "iLO5": "MTX-2dc80c4ae4b943fa",
        "iLO6": "MTX-994a0b6ce04a44b9"
    }
    
    lookups = {}
    
    for ilo_version, collection_id in collections.items():
        try:
            # API endpoint discovered from HAR trace
            url = f"https://support.hpe.com/hpesc/public/api/software/detail?swColId={collection_id}&loadProdEnvList=true"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract version from the response
            if isinstance(data, dict) and 'swItemList' in data and len(data['swItemList']) > 0:
                # Get the first (latest) item
                latest_item = data['swItemList'][0]
                if 'swItem' in latest_item:
                    item = latest_item['swItem']
                    version = item.get('versionId', 'Unknown')
                    title = item.get('localizedTitle', 'Unknown')
                    status = item.get('status', 'Unknown')
                    
                    lookups[ilo_version] = {
                        "version": version,
                        "title": title,
                        "status": status
                    }
                    print(f"{ilo_version}: v{version} - {title}")
            else:
                print(f"{ilo_version}: No data found in response")
        
        except Exception as e:
            print(f"Error scraping {ilo_version}: {e}")
    
    output = {
        "description": "HPE iLO Firmware Lookup Table",
        "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
        "lookups": lookups
    }
    
    with open('APC/UPS/HPE_iLO_Firmware_Lookup.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nScraped and saved {len(lookups)} iLO versions")
    return len(lookups)

if __name__ == "__main__":
    scrape_hpe_ilo_firmware()
