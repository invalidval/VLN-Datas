#!/usr/bin/env python3
"""
Capture the API requests that load floor plan data.
This will help us download the original high-quality floor plans directly.
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json

def capture_api_requests():
    """Capture network requests to find floor plan API"""

    options = webdriver.ChromeOptions()
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=options)

    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)

        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        print("[*] Waiting for building list to load...")
        time.sleep(10)

        try:
            wait.until(lambda d: "0 Results" not in d.page_source)
            print("[*] Building list loaded!")
        except TimeoutException:
            print("[!] Timeout waiting for building list")

        time.sleep(2)

        # Click on the first building
        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"
        building_items = driver.find_elements(By.CSS_SELECTOR, building_selector)

        if building_items:
            print(f"[*] Found {len(building_items)} buildings")
            print("[*] Clicking first building...")

            clickable = building_items[0].find_element(By.CSS_SELECTOR, "div[role='button']")
            driver.execute_script("arguments[0].click();", clickable)

            print("[*] Waiting for floor plan to load...")
            time.sleep(5)

            # Get network logs
            logs = driver.get_log('performance')

            print("\n[*] Analyzing network requests...")
            api_requests = []

            for entry in logs:
                try:
                    log = json.loads(entry['message'])['message']
                    if log['method'] == 'Network.responseReceived':
                        response = log['params']['response']
                        url = response['url']

                        # Look for interesting requests
                        if any(keyword in url.lower() for keyword in ['floor', 'plan', 'svg', 'drawing', 'dwg', 'image', 'graphic']):
                            api_requests.append({
                                'url': url,
                                'status': response['status'],
                                'mimeType': response.get('mimeType', 'unknown')
                            })
                            print(f"\n[+] Found: {url}")
                            print(f"    Status: {response['status']}")
                            print(f"    Type: {response.get('mimeType', 'unknown')}")

                except Exception as e:
                    continue

            # Save all requests to file
            with open('api_requests.json', 'w') as f:
                json.dump(api_requests, f, indent=2)

            print(f"\n[*] Saved {len(api_requests)} API requests to api_requests.json")

            # Also check for SVG elements in the page
            print("\n[*] Checking for SVG elements...")
            svgs = driver.find_elements(By.TAG_NAME, "svg")
            print(f"[*] Found {len(svgs)} SVG elements")

            if svgs:
                # Save the first SVG
                svg_content = driver.execute_script("return arguments[0].outerHTML;", svgs[0])
                with open('floor_plan.svg', 'w') as f:
                    f.write(svg_content)
                print("[+] Saved first SVG to floor_plan.svg")

        else:
            print("[!] No buildings found")

    finally:
        driver.quit()

if __name__ == "__main__":
    capture_api_requests()
