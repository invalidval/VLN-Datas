#!/usr/bin/env python3
"""
Download Cal Poly building floor plans
"""
import os
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

def setup_browser(headless=True):
    """Setup Chrome browser"""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    browser = webdriver.Chrome(options=options)
    return browser

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def download_calpoly_floor_plans(output_dir='calpoly_floor_plans'):
    """Download all Cal Poly building floor plans"""
    os.makedirs(output_dir, exist_ok=True)

    url = "https://afd.calpoly.edu/facilities/campus-maps/building-floor-plans"

    print(f"[*] Accessing: {url}")
    browser = setup_browser(headless=True)

    try:
        browser.get(url)
        time.sleep(3)

        # Find all PDF links
        links = browser.find_elements(By.TAG_NAME, "a")
        pdf_links = []

        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.text.strip()

                if href and '.pdf' in href.lower() and 'Building' in href:
                    pdf_links.append({
                        'text': text,
                        'url': href
                    })
            except:
                continue

        print(f"[*] Found {len(pdf_links)} building floor plans")

        # Download each PDF
        success_count = 0
        for i, link in enumerate(pdf_links, 1):
            try:
                pdf_url = link['url']
                building_name = link['text'] if link['text'] else f"Building_{i}"

                # Extract building number from URL
                match = re.search(r'Building%20(\d+)', pdf_url)
                if match:
                    building_num = match.group(1)
                    filename = f"{building_num.zfill(3)}_{sanitize_filename(building_name)}.pdf"
                else:
                    filename = f"{sanitize_filename(building_name)}.pdf"

                output_path = os.path.join(output_dir, filename)

                # Skip if already downloaded
                if os.path.exists(output_path):
                    print(f"[{i}/{len(pdf_links)}] Already exists: {filename}")
                    success_count += 1
                    continue

                # Download PDF
                print(f"[{i}/{len(pdf_links)}] Downloading: {building_name}")
                response = requests.get(pdf_url, timeout=30)

                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"    ✓ Saved: {filename} ({len(response.content)/1024:.1f} KB)")
                    success_count += 1
                else:
                    print(f"    ✗ Failed: HTTP {response.status_code}")

                time.sleep(0.5)  # Be polite

            except Exception as e:
                print(f"    ✗ Error: {e}")

        print(f"\n[*] Complete! Downloaded {success_count}/{len(pdf_links)} floor plans")
        print(f"[*] Saved to: {output_dir}/")

    finally:
        browser.quit()

if __name__ == '__main__':
    download_calpoly_floor_plans()
