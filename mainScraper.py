import sys
import time
import json
import csv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from selenium.webdriver.common.action_chains import ActionChains

class ZillowScraper():
    results = []
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-encoding': 'gzip, deflate, br,zstd',
        'accept-language': 'en-US,en;q=0.9,fr;q=0.8',
        'cache-control': 'max-age=0',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.binary_location = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def fetch(self, url):
        self.driver.get(url)
        # Let Webpage Load
        time.sleep(3)

        # Locate the scrollable container
        search_results_container = self.driver.find_element(By.ID, 'search-page-list-container')

        # While loop to scroll until bottom
        while True:
            last_scroll_top = self.driver.execute_script("return arguments[0].scrollTop", search_results_container)
            self.driver.execute_script("arguments[0].scrollTop += 600;", search_results_container)
            # Timer to let data load
            time.sleep(.5)
            new_scroll_top = self.driver.execute_script("return arguments[0].scrollTop", search_results_container)
            # When last scroll height and current scroll height is same, break
            if new_scroll_top == last_scroll_top:
                break

    def parse(self):
        content = BeautifulSoup(self.driver.page_source, 'lxml')
        # class name of cards
        deck = content.find('ul', {'class': 'List-c11n-8-105-2__sc-1smrmqp-0 StyledSearchListWrapper-srp-8-105-2__sc-1ieen0c-0 hEDtmo gHtOqg photo-cards photo-cards_extra-attribution'})
        if deck is None:
            print("No photo cards found.")
            return

        for card in deck.contents:
            script = card.find('script', {'type': 'application/ld+json'})
            if script:
                script_json = json.loads(script.contents[0])

                # Can add more data as needed
                self.results.append({
                    'latitude': script_json['geo'].get('latitude'),
                    'longitude': script_json['geo'].get('longitude'),
                    'address': script_json.get('address', {}).get('streetAddress'),
                    'floorSize': script_json.get('floorSize', {}).get('value'),
                    'url': script_json.get('url'),
                    'price': card.find('span', {'data-test': 'property-card-price'}).text.strip()
                })

    def to_csv(self, location):
        if not self.results:
            print("No data to write to the CSV.")
            return

        filename = f'{location}.csv'

        with open(filename, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['latitude', 'longitude', 'address', 'floorSize', 'url', 'price'])
            for row in self.results:
                # Clean data to remove commas and $ signs
                price_cleaned = row['price'].replace('$', '').replace(',', '').strip() if row['price'] else '0'
                floorSize_cleaned = row['floorSize'].replace(',', '').strip() if row['price'] else '0'
                
                writer.writerow([
                    row['latitude'],
                    row['longitude'],
                    row["address"],
                    floorSize_cleaned,
                    row["url"],
                    price_cleaned
                ])
        print("Data successfully written to zillow.csv.")

    def run(self, location):
        base_url = f'https://www.zillow.com/{location}/rentals/'

        # Can scrape more pages for additional properties
        for page in range(1, 2):
            url = f'{base_url}?searchQueryState={json.dumps({"pagination": {"currentPage": page}})}'
            print(f"Fetching page {page}: URL {url}")
            self.fetch(url)
            self.parse()
            time.sleep(2)

        self.to_csv(location)

    def close(self):
        self.results = []
        self.driver.quit()