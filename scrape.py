from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)

url = "https://www.se.com/us/en/faqs/FA279197/"

try:
    # Configure Chrome for headless browsing
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    
    # Wait for page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
    )
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    
    # Extract page title
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
