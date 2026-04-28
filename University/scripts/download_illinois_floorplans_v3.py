#!/usr/bin/env python3
"""
Download floor plans from University of Illinois Facility Access Maps
Version 3: Improved navigation and error handling
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

def load_progress():
    """Load progress from file"""
    progress_file = "illinois_download_progress.json"
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {"completed": [], "failed": []}

def save_progress(progress):
    """Save progress to file"""
    progress_file = "illinois_download_progress.json"
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)

def download_illinois_floorplans():
    """Download floor plans from Illinois Facility Access Maps"""

    # Setup output directory
    output_dir = "data/illinois_floor_plans"
    os.makedirs(output_dir, exist_ok=True)

    # Load progress
    progress = load_progress()
    completed = set(progress.get("completed", []))
    failed = set(progress.get("failed", []))

    print(f"[*] Progress: {len(completed)} completed, {len(failed)} failed")

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode for faster processing
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)

    base_url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"

    try:
        print(f"[*] Loading: {base_url}")
        driver.get(base_url)

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
            return

        time.sleep(2)

        # Get all building names first
        building_items = driver.find_elements(By.CSS_SELECTOR, "ul.Department__ListContainer-sc-16fju6t-1 li")
        total_buildings = len(building_items)
        print(f"[*] Found {total_buildings} buildings")

        # Extract building names
        building_names = []
        for item in building_items:
            text = item.text.strip()
            name = text.split('\n')[0]  # First line is the name
            building_names.append(name)

        print(f"[*] Starting download process...")

        # Process each building
        for i, building_name in enumerate(building_names):
            # Skip if already completed
            if building_name in completed:
                print(f"[{i+1}/{total_buildings}] Skipping (already completed): {building_name}")
                continue

            # Skip if previously failed (but we'll retry after 3 attempts)
            if building_name in failed:
                print(f"[{i+1}/{total_buildings}] Skipping (previously failed): {building_name}")
                continue

            try:
                print(f"\n[{i+1}/{total_buildings}] Processing: {building_name}")

                # Reload the main page to ensure clean state
                driver.get(base_url)
                time.sleep(3)

                # Wait for building list to load
                wait.until(lambda d: "0 Results" not in d.page_source)
                time.sleep(2)

                # Find the building item again
                building_items = driver.find_elements(By.CSS_SELECTOR, "ul.Department__ListContainer-sc-16fju6t-1 li")

                # Find the correct building by matching name
                target_building = None
                for item in building_items:
                    item_text = item.text.strip()
                    item_name = item_text.split('\n')[0]
                    if item_name == building_name:
                        target_building = item
                        break

                if not target_building:
                    print(f"  [!] Could not find building in list")
                    failed.add(building_name)
                    save_progress({"completed": list(completed), "failed": list(failed)})
                    continue

                # Click on the building
                target_building.click()
                print(f"  [*] Clicked on building")

                # Wait for floor plan to load
                time.sleep(5)

                # Take a screenshot
                filename = sanitize_filename(building_name) + ".png"
                filepath = os.path.join(output_dir, filename)
                driver.save_screenshot(filepath)
                print(f"  [*] Screenshot saved: {filename}")

                # Mark as completed
                completed.add(building_name)
                save_progress({"completed": list(completed), "failed": list(failed)})

                # Small delay between buildings
                time.sleep(1)

            except Exception as e:
                print(f"  [!] Error processing building: {e}")
                failed.add(building_name)
                save_progress({"completed": list(completed), "failed": list(failed)})
                continue

        print(f"\n[*] Download complete!")
        print(f"[*] Successfully downloaded: {len(completed)} buildings")
        print(f"[*] Failed: {len(failed)} buildings")
        print(f"[*] Screenshots saved to: {output_dir}")

    finally:
        print("\n[*] Closing browser...")
        driver.quit()

if __name__ == "__main__":
    download_illinois_floorplans()
