#!/usr/bin/env python3
"""
Download Illinois floor plans as clean PDFs by:
1. Hiding layers (clicking basicFloorPlan button)
2. Clicking the print button (printFloorPlan)
This produces clean floor plan PDFs without extra UI elements.

Version 2: Always clicks the first unprocessed building to avoid index issues.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import os
import json

def download_floor_plans(output_dir="../data/illinois_floor_plans_clean", max_buildings=None):
    """Download clean floor plans as PDFs"""

    os.makedirs(output_dir, exist_ok=True)

    # Progress tracking
    progress_file = os.path.join(output_dir, "download_progress.json")
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            progress = json.load(f)
        print(f"[*] Resuming - already completed {len(progress['completed'])} buildings")
    else:
        progress = {'completed': [], 'skipped': []}

    # Configure Chrome for automatic PDF saving
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--kiosk-printing')  # Enable automatic printing

    prefs = {
        "printing.print_preview_sticky_settings.appState": json.dumps({
            "recentDestinations": [{
                "id": "Save as PDF",
                "origin": "local",
                "account": ""
            }],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }),
        "savefile.default_directory": os.path.abspath(output_dir),
        "download.default_directory": os.path.abspath(output_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=options)

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)
        print("[*] Waiting for building list to load...")
        time.sleep(15)

        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"

        processed_count = 0

        # Keep processing until we reach max_buildings or no more buildings
        while True:
            if max_buildings and processed_count >= max_buildings:
                print(f"[*] Reached max_buildings limit: {max_buildings}")
                break

            # Get current building list
            building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)

            if not building_items:
                print("[*] No more buildings found")
                break

            # Find first unprocessed building
            found_building = False
            for building_item in building_items:
                try:
                    name_div = building_item.find_element(By.CSS_SELECTOR, "div.StyledSearchResult__StyledItem-sc-1qyatxh-2")
                    building_name = name_div.text.strip()
                except:
                    continue

                # Skip if already processed
                if building_name in progress['completed'] or building_name in progress['skipped']:
                    continue

                # Found an unprocessed building
                found_building = True
                print(f"\n[{len(progress['completed']) + 1}] Processing: {building_name}")

                try:
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
                        progress['skipped'].append(building_name)
                        with open(progress_file, 'w') as f:
                            json.dump(progress, f, indent=2)

                        # Go back
                        try:
                            home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                            driver.execute_script("arguments[0].click();", home_button)
                            time.sleep(2)
                        except:
                            pass
                        break

                    # Step 1: Click "Show Unmarked Floor Plan" to hide layers
                    try:
                        basic_button = driver.find_element(By.ID, "basicFloorPlan")
                        driver.execute_script("arguments[0].click();", basic_button)
                        print("  [+] Hid layers (unmarked floor plan)")
                        time.sleep(1)
                    except:
                        print("  [!] Could not hide layers")

                    # Step 2: Click "Print Floor Plan" button
                    try:
                        print_button = driver.find_element(By.ID, "printFloorPlan")

                        # Get expected filename
                        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in building_name)
                        expected_pdf = os.path.join(output_dir, f"{safe_name}.pdf")

                        # Click print button
                        driver.execute_script("arguments[0].click();", print_button)
                        print("  [+] Clicked print button")

                        # Wait longer for floor plan to render and PDF to be created
                        print("  [*] Waiting for floor plan to render...")
                        time.sleep(15)

                        # Check if PDF was created (Chrome may save with different name)
                        # Look for recently created PDFs
                        pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
                        if pdf_files:
                            # Get most recent PDF
                            latest_pdf = max([os.path.join(output_dir, f) for f in pdf_files],
                                           key=os.path.getctime)

                            # Check file size to ensure it's not just a loading circle
                            pdf_size = os.path.getsize(latest_pdf)
                            if pdf_size < 30000:  # Less than 30KB is likely just loading circle
                                print(f"  [!] PDF too small ({pdf_size} bytes), likely incomplete")
                                if os.path.exists(latest_pdf):
                                    os.remove(latest_pdf)
                                progress['skipped'].append(building_name)
                            else:
                                # Rename to building name if needed
                                if latest_pdf != expected_pdf:
                                    if os.path.exists(expected_pdf):
                                        os.remove(expected_pdf)
                                    os.rename(latest_pdf, expected_pdf)

                                print(f"  [+] Saved: {expected_pdf} ({pdf_size} bytes)")

                                # Update progress
                                progress['completed'].append(building_name)
                                processed_count += 1
                        else:
                            print("  [!] PDF not found after print")
                            progress['skipped'].append(building_name)

                        # Save progress
                        with open(progress_file, 'w') as f:
                            json.dump(progress, f, indent=2)

                    except Exception as e:
                        print(f"  [!] Error printing: {e}")
                        progress['skipped'].append(building_name)
                        with open(progress_file, 'w') as f:
                            json.dump(progress, f, indent=2)

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
                    progress['skipped'].append(building_name)
                    with open(progress_file, 'w') as f:
                        json.dump(progress, f, indent=2)

                    # Try to go back
                    try:
                        home_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='tab-home-button']")
                        driver.execute_script("arguments[0].click();", home_button)
                        time.sleep(2)
                    except:
                        pass

                # Break to re-fetch building list
                break

            if not found_building:
                print("[*] No more unprocessed buildings found")
                break

        print(f"\n[*] Download complete! Clean floor plan PDFs saved to: {output_dir}")
        print(f"[*] Total downloaded: {len(progress['completed'])}")
        print(f"[*] Total skipped: {len(progress['skipped'])}")

    finally:
        driver.quit()

if __name__ == "__main__":
    # Download all buildings
    download_floor_plans(max_buildings=None)
