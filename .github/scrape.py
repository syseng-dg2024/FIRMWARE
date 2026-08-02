import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

url = "https://www.se.com/us/en/faqs/FA279197"  # Replace with target URL
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Extract data (customize based on your needs)
data = {
    'timestamp': datetime.now().isoformat(),
    'content': soup.find('h1').text if soup.find('h1') else None
}

# Save to file
with open('data/scraped_data.json', 'w') as f:
    json.dump(data, f, indent=2)
