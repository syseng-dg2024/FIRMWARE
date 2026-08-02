import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)

url = "https://www.se.com/us/en/faqs/FA279197/"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    response = requests.get(url, timeout=10, headers=headers)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract page title
    title = soup.find('h1')
    title_text = title.get_text(strip=True) if title else "No title found"
    
    # Find all tables on the page
    tables = soup.find_all('table')
    table_data = []
    
    for idx, table in enumerate(tables):
        rows = table.find_all('tr')
        table_rows = []
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = []
            
            for cell in cells:
                # Get text and any links
                text = cell.get_text(strip=True)
                link = cell.find('a')
                link_text = link.get('href') if link else None
                
                row_data.append({
                    'text': text,
                    'link': link_text
                })
            
            if row_data:
                table_rows.append(row_data)
        
        table_data.append({
            'table_number': idx + 1,
            'rows': table_rows
        })
    
    data = {
        'timestamp': datetime.now().isoformat(),
        'url': url,
        'title': title_text,
        'tables': table_data,
        'total_tables': len(tables)
    }
    
    with open('data/scraped_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Scrape successful! Found {len(tables)} table(s)")
    
except Exception as e:
    print(f"Error: {e}")
    exit(1)
