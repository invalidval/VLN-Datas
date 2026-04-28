#!/usr/bin/env python3
"""
Explore export/download options on Illinois Facility Access Maps
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def explore_export_options():
    """Explore the page for export/download options"""

    options = webdriver.ChromeOptions()
    # Don't use headless so we can see what's happening
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        print("[*] Waiting for building list to load...")
        time.sleep(10)
        wait.until(lambda d: "0 Results" not in d.page_source)
        time.sleep(2)

        # Click on first building
        building_items = driver.find_elements(By.CSS_SELECTOR, "ul.Department__ListContainer-sc-16fju6t-1 li")
        if building_items:
            first_building = building_items[0]
            building_name = first_building.text.strip().split('\n')[0]
            print(f"[*] Clicking on: {building_name}")
            first_building.click()
            time.sleep(5)

            print("\n[*] Looking for export/download buttons...")

            # Look for buttons with export/download/print/save keywords
            keywords = ['export', 'download', 'print', 'save', 'pdf', 'image', 'share']

            for keyword in keywords:
                # Check buttons
                buttons = driver.find_elements(By.TAG_NAME, "button")
                for btn in buttons:
                    text = (btn.text or btn.get_attribute("aria-label") or
                           btn.get_attribute("title") or "").lower()
                    if keyword in text:
                        print(f"  [+] Found button: {text}")

                # Check links
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    text = (link.text or link.get_attribute("aria-label") or
                           link.get_attribute("title") or "").lower()
                    href = link.get_attribute("href") or ""
                    if keyword in text or keyword in href.lower():
                        print(f"  [+] Found link: {text} -> {href}")

            print("\n[*] Looking for SVG/Canvas elements (floor plan rendering)...")
            svgs = driver.find_elements(By.TAG_NAME, "svg")
            print(f"  Found {len(svgs)} SVG elements")

            canvases = driver.find_elements(By.TAG_NAME, "canvas")
            print(f"  Found {len(canvases)} Canvas elements")

            print("\n[*] Looking for image elements...")
            images = driver.find_elements(By.TAG_NAME, "img")
            print(f"  Found {len(images)} image elements")
            for i, img in enumerate(images[:5]):
                src = img.get_attribute("src")
                if src and not src.startswith("data:"):
                    print(f"    Image {i+1}: {src}")

            print("\n[*] Checking for iframes...")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            print(f"  Found {len(iframes)} iframes")
            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute("src")
                print(f"    Iframe {i+1}: {src}")

            # Save page source for analysis
            with open("illinois_building_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("\n[*] Page source saved to: illinois_building_page.html")

            # Take a screenshot
            driver.save_screenshot("illinois_building_view.png")
            print("[*] Screenshot saved to: illinois_building_view.png")

            print("\n[*] Browser will stay open for 60 seconds for manual inspection...")
            print("[*] Please check if there are any export/download options visible")
            time.sleep(60)

    finally:
        driver.quit()

if __name__ == "__main__":
    explore_export_options()
