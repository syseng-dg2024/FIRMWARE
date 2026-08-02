import json
import os
from datetime import datetime

os.makedirs('TEMP/OUTPUT/APC/UPS', exist_ok=True)

def parse_ups_firmware(input_file, output_file):
    """Parse UPS firmware data into lookup format"""
    try:
        with open(input_file, 'r') as f:
            lines = f.read().strip().split('\n')
        
        lookups = {}
        for line in lines[1:]:
            if line.strip():
                values = [v.strip() for v in line.split('\t')]
                if len(values) >= 4:
                    ups_id = values[1]
                    firmware_version = values[3]
                    if ups_id and firmware_version:
                        lookups[ups_id] = firmware_version
        
        output = {
            "description": "APC UPS Firmware Lookup Table - ID to Latest Version mapping",
            "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
            "lookups": lookups
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"UPS: {len(lookups)} entries → {output_file}")
        return len(lookups)
    except Exception as e:
        print(f"UPS parsing failed: {e}")
        return 0

def parse_nmc_firmware(input_file, output_file):
    """Parse NMC firmware data into nested lookup format"""
    try:
        with open(input_file, 'r') as f:
            lines = f.read().strip().split('\n')
        
        lookups = {}
        for line in lines[1:]:
            if line.strip():
                values = [v.strip() for v in line.split('\t')]
                if len(values) >= 3:
                    ups_type = values[0]
                    nmc_model = values[1]
                    firmware_version = values[2]
                    
                    if ups_type and nmc_model and firmware_version:
                        if ups_type not in lookups:
                            lookups[ups_type] = {}
                        lookups[ups_type][nmc_model] = firmware_version
        
        output = {
            "description": "APC NMC Firmware Lookup Table - NMC Type/Model to Latest Version",
            "lastUpdated": datetime.now().strftime("%-m-%-d-%Y"),
            "lookups": lookups
        }
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"NMC: {len(lookups)} UPS types → {output_file}")
        return len(lookups)
    except Exception as e:
        print(f"NMC parsing failed: {e}")
        return 0

# Main execution
if __name__ == "__main__":
    print("Starting firmware data parsing...")
    parse_ups_firmware('TEMP/INPUT/UPS_Firmware.txt', 'TEMP/OUTPUT/UPS_Firmware_Lookup.json')
    parse_nmc_firmware('TEMP/INPUT/NMC_Firmware.txt', 'TEMP/OUTPUT/NMC_Firmware_Lookup.json')
    print("All firmware data processed successfully!")
