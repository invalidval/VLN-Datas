#!/usr/bin/env python3
"""
Explore the Illinois floor plan page to find the hide layers and print buttons
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def explore_buttons():
    options = webdriver.ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(options=options)
    
    try:
        url = "https://facilityaccessmaps.fs.illinois.edu/archibus/schema/ab-products/essential/workplace/index.html"
        print(f"[*] Loading: {url}")
        driver.get(url)
        
        wait = WebDriverWait(driver, 30)
        print("[*] Waiting for page to load...")
        time.sleep(15)
        
        # Click first building
        building_selector = "li.Department__StyledBlContainer-sc-16fju6t-14"
        buildings = driver.find_elements(By.CSS_SELECTOR, building_selector)
        
        if buildings:
            print(f"[*] Found {len(buildings)} buildings")
            print("[*] Clicking first building...")
            clickable = buildings[0].find_element(By.CSS_SELECTOR, "div[role='button']")
            driver.execute_script("arguments[0].click();", clickable)
            time.sleep(5)
            
            print("\n[*] Looking for all buttons on the page...")
            
            # Find all buttons
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"\n[*] Found {len(buttons)} button elements")
            
            for i, btn in enumerate(buttons):
                try:
                    btn_id = btn.get_attribute('id')
                    btn_class = btn.get_attribute('class')
                    btn_text = btn.text.strip()
                    btn_title = btn.get_attribute('title')
                    btn_aria = btn.get_attribute('aria-label')
                    btn_testid = btn.get_attribute('data-testid')
                    
                    # Look for print or layer related buttons
                    if any(keyword in str(x).lower() for x in [btn_id, btn_class, btn_text, btn_title, btn_aria, btn_testid] 
                           for keyword in ['print', 'layer', 'hide', 'show', 'legend', 'marker']):
                        print(f"\n[Button {i+1}]")
                        if btn_id: print(f"  ID: {btn_id}")
                        if btn_testid: print(f"  data-testid: {btn_testid}")
                        if btn_text: print(f"  Text: {btn_text}")
                        if btn_title: print(f"  Title: {btn_title}")
                        if btn_aria: print(f"  aria-label: {btn_aria}")
                        if btn_class: print(f"  Class: {btn_class[:100]}")
                        
                except Exception as e:
                    continue
            
            # Also look for icons (svg, img)
            print("\n\n[*] Looking for icon elements...")
            svgs = driver.find_elements(By.TAG_NAME, "svg")
            
            for i, svg in enumerate(svgs):
                try:
                    parent = svg.find_element(By.XPATH, "..")
                    parent_tag = parent.tag_name
                    parent_role = parent.get_attribute('role')
                    parent_title = parent.get_attribute('title')
                    parent_aria = parent.get_attribute('aria-label')
                    
                    if parent_tag == 'button' or parent_role == 'button':
                        if any(keyword in str(x).lower() for x in [parent_title, parent_aria] 
                               for keyword in ['print', 'layer', 'hide', 'show']):
                            print(f"\n[SVG Icon {i+1}]")
                            print(f"  Parent: {parent_tag}")
                            if parent_title: print(f"  Title: {parent_title}")
                            if parent_aria: print(f"  aria-label: {parent_aria}")
                            
                except Exception as e:
                    continue
            
            print("\n[*] Keeping browser open for 30 seconds for manual inspection...")
            time.sleep(30)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    explore_buttons()
