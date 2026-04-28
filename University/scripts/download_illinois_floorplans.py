#!/usr/bin/env python3
"""
Download floor plans from University of Illinois Facility Access Maps
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json

def download_illinois_floorplans():
    """Download floor plans from Illinois Facility Access Maps"""

    # Setup output directory
    output_dir = "data/illinois_floor_plans"
    os.makedirs(output_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    # Don't use headless mode so we can see what's happening
    driver = webdriver.Chrome(options=options)

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        print("[*] Waiting for building list to load...")
        # Wait for the building list container to have items
        time.sleep(10)  # Give it time to load the list

        # Wait for result count to change from "0 Results"
        try:
            wait.until(lambda d: "0 Results" not in d.page_source)
            print("[*] Building list loaded!")
        except TimeoutException:
            print("[!] Timeout waiting for building list to load")

        time.sleep(2)  # Extra wait

        # Try to find the building list container
        # Let's inspect the page structure
        page_source = driver.page_source

        # Save page source for analysis
        with open("illinois_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("[*] Page source saved to illinois_page_source.html")

        # Try to find building elements using various selectors
        selectors = [
            "ul.Department__ListContainer-sc-16fju6t-1 li",  # The actual building list
            "div.building-item",
            "div.building",
            "li.building",
            "a[href*='building']",
            "div[class*='building']",
            "div[class*='list'] a",
            "div[class*='result'] a"
        ]

        buildings = []
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"[+] Found {len(elements)} elements with selector: {selector}")
                    buildings = elements
                    break
            except:
                continue

        if not buildings:
            print("[!] Could not find building list elements")
            print("[*] Trying to find all clickable links...")
            links = driver.find_elements(By.TAG_NAME, "a")
            print(f"[*] Found {len(links)} total links")
            for i, link in enumerate(links[:10]):  # Show first 10
                try:
                    text = link.text.strip()
                    href = link.get_attribute("href")
                    if text:
                        print(f"  Link {i+1}: {text[:50]} -> {href}")
                except:
                    pass
        else:
            print(f"[*] Found {len(buildings)} building elements")

            # Extract building information
            building_info = []
            for i, building in enumerate(buildings[:5]):  # Test with first 5
                try:
                    text = building.text.strip()
                    href = building.get_attribute("href")
                    print(f"  Building {i+1}: {text[:50]}")
                    building_info.append({"text": text, "href": href})
                except Exception as e:
                    print(f"  Error extracting building {i+1}: {e}")

            # Save building info
            with open("illinois_buildings.json", "w") as f:
                json.dump(building_info, f, indent=2)
            print(f"[*] Saved building info to illinois_buildings.json")

        print("\n[*] Browser will stay open for 60 seconds for manual inspection...")
        time.sleep(60)

    finally:
        driver.quit()

if __name__ == "__main__":
    download_illinois_floorplans()
