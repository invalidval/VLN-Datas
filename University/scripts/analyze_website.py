#!/usr/bin/env python3
"""
Analyze university website structure to find floor plans
"""
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def analyze_website(url):
    """Analyze website structure"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    browser = webdriver.Chrome(options=options)

    try:
        print(f"[*] Accessing: {url}")
        browser.get(url)
        time.sleep(3)

        # Get page title
        print(f"\n[*] Page Title: {browser.title}")

        # Find all links
        links = browser.find_elements(By.TAG_NAME, "a")
        print(f"\n[*] Total links found: {len(links)}")

        # Filter floor plan related links
        floor_plan_keywords = ['floor', 'plan', 'building', 'map', 'layout', 'pdf']
        floor_plan_links = []

        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()

                if href and any(keyword in href.lower() or keyword in text.lower()
                               for keyword in floor_plan_keywords):
                    floor_plan_links.append({
                        'text': text,
                        'href': href
                    })
            except:
                continue

        print(f"\n[*] Floor plan related links: {len(floor_plan_links)}")
        for i, link in enumerate(floor_plan_links[:20], 1):
            print(f"  {i}. {link['text'][:50]}")
            print(f"     {link['href']}")

        # Find all images
        images = browser.find_elements(By.TAG_NAME, "img")
        print(f"\n[*] Total images found: {len(images)}")

        # Find PDFs
        pdf_links = [link for link in links if link.get_attribute('href') and '.pdf' in link.get_attribute('href').lower()]
        print(f"\n[*] PDF links found: {len(pdf_links)}")
        for i, link in enumerate(pdf_links[:10], 1):
            try:
                print(f"  {i}. {link.text.strip()[:50]}")
                print(f"     {link.get_attribute('href')}")
            except:
                continue

        # Save page source for further analysis
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(browser.page_source)
        print(f"\n[*] Page source saved to page_source.html")

    finally:
        browser.quit()

if __name__ == '__main__':
    url = sys.argv[1] if len(sys.argv) > 1 else "https://afd.calpoly.edu/facilities/campus-maps/"
    analyze_website(url)
