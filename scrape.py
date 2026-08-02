import asyncio
import json
import os
from datetime import datetime
from crawlee.http_crawler import HttpCrawler
from bs4 import BeautifulSoup

os.makedirs('data', exist_ok=True)

async def main():
    crawler = HttpCrawler(
        max_requests_per_crawl=1,
    )

    @crawler.on_response_received
    async def handle_response(context):
        soup = BeautifulSoup(context.http_response.text, 'html.parser')
        
        # Extract title
        title = soup.find('h1')
        title_text = title.get_text(strip=True) if title else "No title found"
        
        # Find all tables
        tables = soup.find_all('table')
        table_data = []
        
        for idx, table in enumerate(tables):
            rows = table.find_all('tr')
            table_rows = []
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                row_data = []
                
                for cell in cells:
                    text = cell.get_text(strip=True)
                    link = cell.find('a')
                    link_text = link.get('href') if link else None
                    link_label = link.get_text(strip=True) if link else None
                    
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
            'url': context.request.url,
            'title': title_text,
            'tables': table_data,
            'total_tables': len(tables)
        }
        
        with open('data/scraped_data.json', 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Scrape successful! Found {len(tables)} table(s)")

    await crawler.run(['https://www.se.com/us/en/faqs/FA279197/'])

if __name__ == '__main__':
    asyncio.run(main())
