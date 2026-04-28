#!/usr/bin/env python3
"""
Download floor plans from University of Illinois Facility Access Maps
Version 2: Click on buildings and capture floor plans
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json
import re

def sanitize_filename(name):
    """Convert building name to safe filename"""
    # Remove special characters
    name = re.sub(r'[^\w\s\-\[\]]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    return name[:100]

def download_illinois_floorplans():
    """Download floor plans from Illinois Facility Access Maps"""

    # Setup output directory
    output_dir = "data/illinois_floor_plans"
    os.makedirs(output_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    # Run in normal mode to see what's happening
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        # Wait for page to load
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        print("[*] Waiting for building list to load...")
        time.sleep(10)

        # Wait for result count to change from "0 Results"
        try:
            wait.until(lambda d: "0 Results" not in d.page_source)
            print("[*] Building list loaded!")
        except TimeoutException:
            print("[!] Timeout waiting for building list to load")

        time.sleep(2)

        # Find all building list items
        building_items = driver.find_elements(By.CSS_SELECTOR, "ul.Department__ListContainer-sc-16fju6t-1 li")
        print(f"[*] Found {len(building_items)} buildings")

        # Process first 5 buildings as a test
        num_to_process = min(5, len(building_items))
        print(f"[*] Processing first {num_to_process} buildings...")

        for i in range(num_to_process):
            try:
                # Re-find the building list items (to avoid stale element reference)
                building_items = driver.find_elements(By.CSS_SELECTOR, "ul.Department__ListContainer-sc-16fju6t-1 li")
                building = building_items[i]

                building_text = building.text.strip()
                building_name = building_text.split('\n')[0]  # First line is the name
                print(f"\n[{i+1}/{num_to_process}] Processing: {building_name}")

                # Click on the building
                building.click()
                print(f"  [*] Clicked on building")

                # Wait for floor plan to load
                time.sleep(5)

                # Take a screenshot
                filename = sanitize_filename(building_name) + ".png"
                filepath = os.path.join(output_dir, filename)
                driver.save_screenshot(filepath)
                print(f"  [*] Screenshot saved: {filename}")

                # Try to find and click a "back" or "close" button to return to list
                # Look for common back button patterns
                back_selectors = [
                    "button[aria-label*='back']",
                    "button[aria-label*='Back']",
                    "button[title*='back']",
                    "button[title*='Back']",
                    "a[aria-label*='back']",
                    "svg[aria-label*='back']",
                    "[class*='back']",
                    "[class*='Back']"
                ]

                back_clicked = False
                for selector in back_selectors:
                    try:
                        back_button = driver.find_element(By.CSS_SELECTOR, selector)
                        back_button.click()
                        print(f"  [*] Clicked back button")
                        back_clicked = True
                        time.sleep(2)
                        break
                    except:
                        continue

                if not back_clicked:
                    print(f"  [!] Could not find back button, navigating back...")
                    driver.back()
                    time.sleep(3)

                # Wait for building list to reload
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.Department__ListContainer-sc-16fju6t-1")))
                time.sleep(2)

            except Exception as e:
                print(f"  [!] Error processing building: {e}")
                import traceback
                traceback.print_exc()
                # Try to go back to the list
                driver.get(url)
                time.sleep(5)

        print(f"\n[*] Completed! Processed {num_to_process} buildings")
        print(f"[*] Screenshots saved to: {output_dir}")

    finally:
        print("\n[*] Closing browser...")
        driver.quit()

if __name__ == "__main__":
    download_illinois_floorplans()
