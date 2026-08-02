import requests
from requests_html import HTMLSession
import json
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)

url = "https://www.se.com/us/en/faqs/FA279197/"

try:
    session = HTMLSession()
    response = session.get(url, timeout=15)
    
    # Extract page title
    title = response.html.find('h1', first=True)
    title_text = title.text if title else "No title found"
    
    # Find all tables
    tables = response.html.find('table')
    table_data = []
    
    for idx, table in enumerate(tables):
        rows = table.find('tr')
        table_rows = []
        
        for row in rows:
            cells = row.find(['td', 'th'])
            row_data = []
            
            for cell in cells:
                text = cell.text
                link = cell.find('a', first=True)
                link_text = link.attrs.get('href') if link else None
                link_label = link.text if link else None
                
                row_data.append({
                    'text': text,
                    'link': link_text,
                    'link_label': link_label
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
