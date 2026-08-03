import json
import requests
import os
from datetime import datetime

os.makedirs('HPE/iLO', exist_ok=True)

def scrape_hpe_ilo_versions():
    """Scrape HPE iLO firmware versions from HPE support API"""
    
    # Collection IDs for each iLO version
    collections = {
        "iLO4": "MTX-b5848d0ffeab4506",
        "iLO5": "MTX-2dc80c4ae4b943fa",
        "iLO6": "MTX-994a0b6ce04a44b9"
    }
    
    lookups = {}
    
    for ilo_version, collection_id in collections.items():
        try:
            # API endpoint discovered from DevTools
            url = f"https://support.hpe.com/hpesc/public/api/software/detail?swColId={collection_id}&loadProdEnvList=true"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/json",
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract version from the response
            if isinstance(data, list) and len(data) > 0:
                latest = data[0]  # First item is latest version
                if 'swItem' in latest and 'versionId' in latest['swItem']:
                    version = latest['swItem']['versionId']
                    title = latest['swItem'].get('localizedTitle', 'Unknown')
                    status = latest['swItem'].get('status', 'Unknown')
                    release_date = latest['swItem'].get('customerAvailableDate', 'Unknown')
                    
                    lookups[ilo_version] = {
                        "version": version,
                        "title": title,
                        "status": status,
                        "releaseDate": release_date
                    }
                    print(f"{ilo_version}: v{version}")
        
        except Exception as e:
            print(f"Error scraping {ilo_version}: {e}")
    
    output = {
        "description": "HPE iLO Firmware Lookup Table - Latest versions for iLO4, iLO5, iLO6",
        "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
        "lookups": lookups
    }
    
    with open('HPE/iLO/iLO_Firmware_Lookup.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nScraped {len(lookups)} iLO firmware versions")
    return len(lookups)

if __name__ == "__main__":
    scrape_hpe_ilo_versions()
