#!/usr/bin/env python3
"""
Download Illinois floor plans by capturing the SVG floor plan directly.
This avoids the print dialog and captures high-quality vector graphics.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

def download_floor_plans(output_dir="../data/illinois_floor_plans_svg", max_buildings=None):
    """Download floor plans by capturing SVG content"""

    os.makedirs(output_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=options)

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        print("[*] Waiting for building list to load...")
        time.sleep(10)

        # Wait for buildings to load
        try:
            wait.until(lambda d: "0 Results" not in d.page_source)
            print("[*] Building list loaded!")
        except TimeoutException:
            print("[!] Timeout waiting for building list")

        time.sleep(2)

        # Find all building list items to get the count
        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"
        building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)

        total_buildings = len(building_items)
        print(f"[*] Found {total_buildings} buildings")

        if not building_items:
            print("[!] No buildings found")
            return

        # Determine how many buildings to process
        num_to_process = min(max_buildings, total_buildings) if max_buildings else total_buildings
        if max_buildings:
            print(f"[*] Limiting to first {max_buildings} buildings")

        # Process each building by index
        for idx in range(num_to_process):
            try:
                # Re-fetch the building list
                building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)
                if idx >= len(building_items):
                    print(f"[!] Building index {idx} out of range, skipping")
                    continue

                building_item = building_items[idx]

                # Get building name
                try:
                    name_div = building_item.find_element(By.CSS_SELECTOR, "div.StyledSearchResult__StyledItem-sc-1qyatxh-2")
                    building_name = name_div.text.strip()
                except:
                    building_name = f"Building_{idx+1}"

                print(f"\n[{idx+1}/{num_to_process}] Processing: {building_name}")

                # Click the building
                clickable = building_item.find_element(By.CSS_SELECTOR, "div[role='button']")
                driver.execute_script("arguments[0].click();", clickable)
                time.sleep(3)

                # Wait for floor plan to load
                try:
                    wait.until(EC.presence_of_element_located((By.ID, "FloorPlan")))
                    print("  [+] Floor plan loaded")
                except TimeoutException:
                    print("  [!] Floor plan did not load, skipping")
                    # Go back and continue
                    try:
                        home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                        driver.execute_script("arguments[0].click();", home_button)
                        time.sleep(2)
                    except:
                        pass
                    continue

                # Click "Show Unmarked Floor Plan" to remove legend
                try:
                    basic_button = driver.find_element(By.ID, "basicFloorPlan")
                    driver.execute_script("arguments[0].click();", basic_button)
                    print("  [+] Switched to unmarked floor plan")
                    time.sleep(1)
                except NoSuchElementException:
                    print("  [!] Could not find unmarked floor plan button")

                # Take screenshot of the floor plan area
                try:
                    floor_plan_element = driver.find_element(By.ID, "FloorPlan")

                    # Save screenshot
                    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in building_name)
                    screenshot_path = os.path.join(output_dir, f"{safe_name}.png")

                    floor_plan_element.screenshot(screenshot_path)
                    print(f"  [+] Saved: {screenshot_path}")

                except Exception as e:
                    print(f"  [!] Error capturing screenshot: {e}")

                # Go back to building list
                try:
                    home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                    driver.execute_script("arguments[0].click();", home_button)

                    # Wait for building list to reload
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, building_selector)))
                    time.sleep(1)
                except Exception as e:
                    print(f"  [!] Error going back: {e}")
                    time.sleep(2)

            except Exception as e:
                print(f"  [!] Error processing building: {e}")
                # Try to go back to home
                try:
                    home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                    driver.execute_script("arguments[0].click();", home_button)
                    time.sleep(2)
                except:
                    pass
                continue

        print(f"\n[*] Download complete! Floor plans saved to: {output_dir}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Test with first 10 buildings
    download_floor_plans(max_buildings=10)
