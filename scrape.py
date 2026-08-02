import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)

url = "https://www.se.com/us/en/faqs/FA279197"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'title': soup.title.string if soup.title else None,
    }
    
    with open('data/scraped_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print("Scrape successful!")
except Exception as e:
    print(f"Error: {e}")
    exit(1)
