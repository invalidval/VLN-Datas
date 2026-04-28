#!/usr/bin/env python3
"""
Capture API requests from Incheon Airport map website
"""
import asyncio
from playwright.async_api import async_playwright
import json

async def capture_requests():
    api_calls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Listen to all network requests
        def handle_request(request):
            url = request.url
            if 'icnmap.airport.kr' in url and '/API/' in url:
                api_calls.append({
                    'url': url,
                    'method': request.method,
                    'headers': request.headers,
                    'post_data': request.post_data
                })
                print(f"\n[API Request] {request.method} {url}")

        def handle_response(response):
            url = response.url
            if 'icnmap.airport.kr' in url and '/API/' in url:
                print(f"[API Response] {response.status} {url}")

        page.on('request', handle_request)
        page.on('response', handle_response)

        print("Opening airport map website...")
        await page.goto('https://www.airport.kr/geomap/ap_en/view.do', wait_until='networkidle')

        print("\nWaiting 10 seconds for map to load and API calls to complete...")
        await asyncio.sleep(10)

        await browser.close()

    # Save captured API calls
    with open('api_calls.json', 'w', encoding='utf-8') as f:
        json.dump(api_calls, f, indent=2, ensure_ascii=False)

    print(f"\n\nCaptured {len(api_calls)} API calls")
    print("Saved to api_calls.json")

    # Print summary
    print("\n=== API Endpoints ===")
    for call in api_calls:
        print(f"{call['method']} {call['url']}")

if __name__ == '__main__':
    asyncio.run(capture_requests())
