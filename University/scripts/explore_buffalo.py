#!/usr/bin/env python3
"""
Explore University at Buffalo website for floor plans
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def explore_buffalo():
    """Explore buffalo.edu for floor plan resources"""

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Try common URLs for campus maps and floor plans
        urls_to_try = [
            'https://www.buffalo.edu/campusliving/life-on-campus/maps.html',
            'https://www.buffalo.edu/facilities.html',
            'https://www.buffalo.edu/administrative-services/facilities.html',
            'https://facilities.buffalo.edu/',
            'https://www.buffalo.edu/administrative-services/facilities/building-services.html',
        ]

        for url in urls_to_try:
            print(f"\n[*] Trying: {url}")
            try:
                driver.get(url)
                time.sleep(2)

                print(f"    Title: {driver.title}")

                # Look for PDF links
                pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
                if pdf_links:
                    print(f"    Found {len(pdf_links)} PDF links:")
                    for link in pdf_links[:5]:  # Show first 5
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        if 'floor' in text.lower() or 'floor' in href.lower():
                            print(f"      ✓ {text}: {href}")

                # Look for floor plan related links
                floor_links = driver.find_elements(By.XPATH, "//a[contains(translate(text(), 'FLOOR', 'floor'), 'floor')]")
                if floor_links:
                    print(f"    Found {len(floor_links)} floor-related links:")
                    for link in floor_links[:5]:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        print(f"      → {text}: {href}")

            except Exception as e:
                print(f"    Error: {e}")
                continue

        # Try searching for building directory
        print("\n[*] Searching for building directory...")
        search_url = 'https://www.buffalo.edu/search.html?q=floor+plans+buildings'
        driver.get(search_url)
        time.sleep(2)
        print(f"    Search results page: {driver.title}")

    finally:
        driver.quit()

if __name__ == '__main__':
    print("Exploring University at Buffalo for floor plans...")
    explore_buffalo()
