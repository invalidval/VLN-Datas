#!/usr/bin/env python3
"""
Extract all SVG elements from the Illinois floor plan page
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import os

def setup_driver():
    options = Options()
    # options.add_argument('--headless=new')  # Run with GUI for debugging
    options.add_argument('--window-size=1920,1080')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=options)
    return driver

def main():
    driver = setup_driver()

    try:
        print("Loading page...")
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        driver.get(url)

        # Wait for page to load
        print("Waiting for page to load...")
        time.sleep(15)

        # Click on first building
        print("Looking for buildings...")
        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"
        buildings = WebDriverWait(driver, 30).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, building_selector))
        )

        print(f"Found {len(buildings)} buildings")

        if buildings:
            print("Clicking on first building...")
            clickable = buildings[0].find_element(By.CSS_SELECTOR, "div[role='button']")
            driver.execute_script("arguments[0].click();", clickable)
            print("Waiting for floor plan to load...")
            time.sleep(5)

            # Click basicFloorPlan button to remove legends
            try:
                basic_button = driver.find_element(By.CSS_SELECTOR, "button[data-testid='basicFloorPlan']")
                basic_button.click()
                print("Clicked basic floor plan button")
                time.sleep(2)
            except:
                print("Could not find basic floor plan button")

            # Find all SVG elements
            svgs = driver.find_elements(By.TAG_NAME, "svg")
            print(f"\nFound {len(svgs)} SVG elements")

            output_dir = "/Users/zcy/Documents/3-2/VLN/InsideMaps/university_maps/svg_elements"
            os.makedirs(output_dir, exist_ok=True)

            for i, svg in enumerate(svgs):
                try:
                    # Get SVG attributes
                    outer_html = svg.get_attribute('outerHTML')
                    width = svg.get_attribute('width')
                    height = svg.get_attribute('height')
                    viewBox = svg.get_attribute('viewBox')

                    # Get size info
                    size = svg.size
                    location = svg.location

                    print(f"\nSVG {i+1}:")
                    print(f"  Width: {width}, Height: {height}")
                    print(f"  ViewBox: {viewBox}")
                    print(f"  Rendered size: {size['width']}x{size['height']}")
                    print(f"  Location: ({location['x']}, {location['y']})")
                    print(f"  HTML length: {len(outer_html)} characters")

                    # Save SVG to file
                    svg_file = os.path.join(output_dir, f"svg_{i+1}.svg")
                    with open(svg_file, 'w', encoding='utf-8') as f:
                        f.write(outer_html)
                    print(f"  Saved to: {svg_file}")

                except Exception as e:
                    print(f"  Error processing SVG {i+1}: {e}")

            print(f"\nAll SVG elements saved to: {output_dir}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
