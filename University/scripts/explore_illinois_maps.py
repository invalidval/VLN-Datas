#!/usr/bin/env python3
"""
Explore Illinois Facility Access Maps system
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json

def explore_facility_maps():
    """Explore the Facility Access Maps interface"""

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        # Wait for the app to load (look for any interactive elements)
        print("[*] Waiting for page to load...")
        time.sleep(10)  # Give it time to fully load

        # Take a screenshot to see what's on the page
        driver.save_screenshot("illinois_maps_loaded.png")
        print("[*] Screenshot saved: illinois_maps_loaded.png")

        # Try to find any clickable elements
        print("\n[*] Looking for interactive elements...")

        # Look for buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        print(f"[*] Found {len(buttons)} buttons")
        for i, btn in enumerate(buttons[:10]):  # Show first 10
            try:
                text = btn.text or btn.get_attribute("aria-label") or btn.get_attribute("title")
                if text:
                    print(f"  Button {i+1}: {text}")
            except:
                pass

        # Look for input fields
        inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"\n[*] Found {len(inputs)} input fields")
        for i, inp in enumerate(inputs[:10]):
            try:
                placeholder = inp.get_attribute("placeholder")
                input_type = inp.get_attribute("type")
                if placeholder or input_type:
                    print(f"  Input {i+1}: type={input_type}, placeholder={placeholder}")
            except:
                pass

        # Look for any divs with text that might be clickable
        print("\n[*] Looking for text content...")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        print(f"[*] Page text content (first 500 chars):\n{body_text[:500]}")

        # Check for any iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"\n[*] Found {len(iframes)} iframes")

        # Try to find building search or navigation
        print("\n[*] Trying to find building search...")
        try:
            # Look for search input
            search_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='search'], input[placeholder*='search'], input[placeholder*='Search']")
            if search_inputs:
                print(f"[*] Found {len(search_inputs)} search inputs")
                search_input = search_inputs[0]
                print("[*] Trying to search for 'Davenport Hall'...")
                search_input.send_keys("Davenport Hall")
                time.sleep(2)
                driver.save_screenshot("illinois_maps_search.png")
                print("[*] Screenshot saved: illinois_maps_search.png")
        except Exception as e:
            print(f"[!] Error during search: {e}")

        # Keep browser open for manual inspection
        print("\n[*] Browser will stay open for 30 seconds for manual inspection...")
        time.sleep(30)

    except Exception as e:
        print(f"[!] Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()

if __name__ == "__main__":
    explore_facility_maps()
