#!/usr/bin/env python3
"""
Download all Illinois building floor plans as high-quality SVG files.
This extracts the large SVG element that contains the actual floor plan.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
import json

def download_floor_plans(output_dir="../data/illinois_floor_plans_svg_final", max_buildings=None):
    """Download floor plans as SVG files"""

    os.makedirs(output_dir, exist_ok=True)

    # Progress tracking
    progress_file = os.path.join(output_dir, "download_progress.json")
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            progress = json.load(f)
        print(f"[*] Resuming from building {progress['last_index'] + 1}")
        start_index = progress['last_index'] + 1
    else:
        progress = {'last_index': -1, 'completed': []}
        start_index = 0

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

        # Find all buildings
        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"
        building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)

        total_buildings = len(building_items)
        print(f"[*] Found {total_buildings} buildings")

        # Determine range
        num_to_process = min(max_buildings, total_buildings) if max_buildings else total_buildings
        if max_buildings:
            print(f"[*] Limiting to first {max_buildings} buildings")

        # Process each building
        for idx in range(start_index, num_to_process):
            try:
                # Re-fetch building list
                building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)
                if idx >= len(building_items):
                    print(f"[!] Building index {idx} out of range")
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
                time.sleep(4)

                # Wait for floor plan to load
                try:
                    wait.until(EC.presence_of_element_located((By.ID, "FloorPlan")))
                    print("  [+] Floor plan loaded")
                except TimeoutException:
                    print("  [!] Floor plan did not load, skipping")
                    # Go back
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
                except:
                    pass

                # Find all SVG elements and get the largest one (the floor plan)
                svgs = driver.find_elements(By.TAG_NAME, "svg")

                # Find the SVG with the most content (the floor plan)
                largest_svg = None
                max_size = 0

                for svg in svgs:
                    try:
                        html = svg.get_attribute('outerHTML')
                        if len(html) > max_size:
                            max_size = len(html)
                            largest_svg = svg
                    except:
                        continue

                if largest_svg and max_size > 10000:  # Floor plan should be large
                    svg_content = largest_svg.get_attribute('outerHTML')

                    # Save SVG
                    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in building_name)
                    svg_path = os.path.join(output_dir, f"{safe_name}.svg")

                    with open(svg_path, 'w', encoding='utf-8') as f:
                        f.write(svg_content)

                    print(f"  [+] Saved: {svg_path} ({max_size} bytes)")

                    # Update progress
                    progress['last_index'] = idx
                    progress['completed'].append(building_name)
                    with open(progress_file, 'w') as f:
                        json.dump(progress, f, indent=2)
                else:
                    print(f"  [!] Could not find floor plan SVG")

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
                # Try to go back
                try:
                    home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                    driver.execute_script("arguments[0].click();", home_button)
                    time.sleep(2)
                except:
                    pass
                continue

        print(f"\n[*] Download complete! SVG floor plans saved to: {output_dir}")
        print(f"[*] Total downloaded: {len(progress['completed'])}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Download all 208 buildings
    download_floor_plans(max_buildings=None)
