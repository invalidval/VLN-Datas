#!/usr/bin/env python3
"""
First, get the complete list of all buildings by scrolling to load all items.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

def get_all_buildings():
    """Get complete list of all buildings"""

    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)
        print("[*] Waiting for building list to load...")
        time.sleep(15)

        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"

        # Try to find the scrollable container
        print("[*] Looking for scrollable container...")

        # Get initial count
        buildings = driver.find_elements(By.CSS_SELECTOR, building_selector)
        print(f"[*] Initial count: {len(buildings)} buildings")

        # Try scrolling to load more
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 20

        while scroll_attempts < max_scroll_attempts:
            buildings = driver.find_elements(By.CSS_SELECTOR, building_selector)
            current_count = len(buildings)

            if current_count == last_count:
                print(f"[*] No new buildings loaded after scroll attempt {scroll_attempts}")
                break

            print(f"[*] Found {current_count} buildings after scroll {scroll_attempts}")
            last_count = current_count

            # Scroll to last building
            if buildings:
                driver.execute_script("arguments[0].scrollIntoView();", buildings[-1])
                time.sleep(2)

            scroll_attempts += 1

        # Get final list
        buildings = driver.find_elements(By.CSS_SELECTOR, building_selector)
        print(f"\n[*] Total buildings found: {len(buildings)}")

        # Extract building names
        building_names = []
        for i, building in enumerate(buildings):
            try:
                name_div = building.find_element(By.CSS_SELECTOR, "div.StyledSearchResult__StyledItem-sc-1qyatxh-2")
                building_name = name_div.text.strip()
                building_names.append(building_name)
                print(f"  {i+1}. {building_name}")
            except:
                print(f"  {i+1}. [Could not get name]")

        # Save to file
        with open('../data/illinois_buildings_list.json', 'w') as f:
            json.dump(building_names, f, indent=2)

        print(f"\n[*] Saved {len(building_names)} building names to illinois_buildings_list.json")

        return building_names

    finally:
        driver.quit()

if __name__ == "__main__":
    get_all_buildings()
