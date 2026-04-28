#!/usr/bin/env python3
"""
Download Illinois floor plans using the built-in Print Floor Plan feature.
This produces high-quality PDFs instead of screenshots.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import os
import base64

def download_floor_plans_as_pdf(output_dir="../data/illinois_floor_plans_pdf", max_buildings=None):
    """Download floor plans using the print feature"""

    os.makedirs(output_dir, exist_ok=True)

    options = webdriver.ChromeOptions()
    # Enable printing to PDF
    options.add_argument('--kiosk-printing')

    # Set download preferences
    prefs = {
        'printing.print_preview_sticky_settings.appState': json.dumps({
            'recentDestinations': [{
                'id': 'Save as PDF',
                'origin': 'local',
                'account': ''
            }],
            'selectedDestinationId': 'Save as PDF',
            'version': 2
        }),
        'savefile.default_directory': os.path.abspath(output_dir)
    }
    options.add_experimental_option('prefs', prefs)

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
            print("[!] No buildings found. Saving page source for debugging...")
            with open("debug_page_source.html", "w") as f:
                f.write(driver.page_source)
            return

        # Determine how many buildings to process
        num_to_process = min(max_buildings, total_buildings) if max_buildings else total_buildings
        if max_buildings:
            print(f"[*] Limiting to first {max_buildings} buildings")

        # Process each building by index (re-fetch elements each time to avoid stale references)
        for idx in range(num_to_process):
            try:
                # Re-fetch the building list to avoid stale element references
                building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)
                if idx >= len(building_items):
                    print(f"[!] Building index {idx} out of range, skipping")
                    continue

                building_item = building_items[idx]

                # Get building name from the title div
                try:
                    name_div = building_item.find_element(By.CSS_SELECTOR, "div.StyledSearchResult__StyledItem-sc-1qyatxh-2")
                    building_name = name_div.text.strip()
                except:
                    building_name = f"Building_{idx+1}"

                print(f"\n[{idx+1}/{num_to_process}] Processing: {building_name}")

                # Get the clickable div and click it
                clickable = building_item.find_element(By.CSS_SELECTOR, "div[role='button']")
                driver.execute_script("arguments[0].click();", clickable)
                time.sleep(3)

                # Wait for floor plan to load
                try:
                    wait.until(EC.presence_of_element_located((By.ID, "FloorPlan")))
                    print("  [+] Floor plan loaded")
                except TimeoutException:
                    print("  [!] Floor plan did not load, skipping")
                    # Try to go back
                    try:
                        home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                        driver.execute_script("arguments[0].click();", home_button)
                        time.sleep(2)
                    except:
                        pass
                    continue

                # Click "Show Unmarked Floor Plan" button to remove legend
                try:
                    basic_button = driver.find_element(By.ID, "basicFloorPlan")
                    driver.execute_script("arguments[0].click();", basic_button)
                    print("  [+] Switched to unmarked floor plan")
                    time.sleep(2)
                except NoSuchElementException:
                    print("  [!] Could not find unmarked floor plan button")

                # Use Chrome DevTools Protocol to print to PDF directly (no print button click)
                try:
                    print("  [+] Generating PDF...")
                    result = driver.execute_cdp_cmd("Page.printToPDF", {
                        "landscape": True,
                        "printBackground": True,
                        "preferCSSPageSize": True,
                        "scale": 1.0
                    })

                    # Save PDF
                    pdf_data = base64.b64decode(result['data'])
                    safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in building_name)
                    pdf_path = os.path.join(output_dir, f"{safe_name}.pdf")

                    with open(pdf_path, 'wb') as f:
                        f.write(pdf_data)

                    print(f"  [+] Saved: {pdf_path} ({len(pdf_data)} bytes)")

                except Exception as e:
                    print(f"  [!] Error generating PDF: {e}")

                # Go back to building list
                try:
                    home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                    driver.execute_script("arguments[0].click();", home_button)
                    print("  [+] Returned to building list")

                    # Wait for building list to reload
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, building_selector)))
                    time.sleep(2)
                except Exception as e:
                    print(f"  [!] Error returning to building list: {e}")
                    time.sleep(3)

            except Exception as e:
                print(f"  [!] Error processing building: {e}")
                # Try to go back to building list
                try:
                    home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                    driver.execute_script("arguments[0].click();", home_button)
                    time.sleep(2)
                except:
                    pass
                continue

        print(f"\n[*] Download complete! PDFs saved to: {output_dir}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Download all 208 buildings
    download_floor_plans_as_pdf(max_buildings=None)
