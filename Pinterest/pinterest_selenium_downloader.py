import os
import sys
import time
import json
import argparse
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import requests

COOKIE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pinterest_cookies.json")

def setup_browser(headless=True):
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--lang=en_US')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    browser = webdriver.Chrome(options=options)
    browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return browser

def save_cookies(browser):
    cookies = browser.get_cookies()
    with open(COOKIE_FILE, "w") as f:
        json.dump(cookies, f)
    print(f"[*] Cookies已保存到 {COOKIE_FILE}")

def load_cookies(browser):
    if not os.path.exists(COOKIE_FILE):
        return False
    with open(COOKIE_FILE, "r") as f:
        cookies = json.load(f)
    # 先打开Pinterest域以便设置cookie
    browser.get("https://www.pinterest.com/")
    time.sleep(2)
    for cookie in cookies:
        # 移除可能导致错误的字段
        for key in ['sameSite', 'expiry', 'httpOnly', 'storeId']:
            cookie.pop(key, None)
        try:
            browser.add_cookie(cookie)
        except Exception:
            pass
    print(f"[*] 已从 {COOKIE_FILE} 加载Cookies")
    return True

def do_login(browser, wait_seconds=60):
    """打开Pinterest首页，等待用户手动登录，然后保存cookies"""
    browser.get("https://www.pinterest.com/login/")
    print("=" * 60)
    print(f"[*] 请在打开的浏览器窗口中手动登录Pinterest")
    print(f"[*] 你有 {wait_seconds} 秒的时间完成登录...")
    print("=" * 60)
    # 轮询等待登录完成（URL不再是login页面）
    for i in range(wait_seconds):
        time.sleep(1)
        try:
            url = browser.current_url
            if 'login' not in url.lower() and 'pinterest.com' in url:
                print(f"[*] 检测到登录成功! 当前页面: {url}")
                time.sleep(3)  # 等待cookie完全写入
                break
        except Exception:
            pass
        if (i + 1) % 10 == 0:
            print(f"[*] 已等待 {i+1} 秒...")
    save_cookies(browser)
    print("[*] 登录完成，cookies已保存。后续运行将自动使用已保存的登录状态。")

def pinterest_search_and_collect_imgs(keywords, num_images=30, out_dir="downloaded_images", headless=True):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    browser = setup_browser(headless=headless)

    # 加载已保存的cookies
    has_cookies = load_cookies(browser)
    if not has_cookies:
        print("[!] 未找到已保存的Cookies，请先运行 --login 登录")
        browser.quit()
        return

    query = keywords.replace(' ', '%20')
    base_url = f"https://www.pinterest.com/search/pins/?q={query}"
    print(f"[*] 打开Pinterest搜索: {base_url}")
    try:
        browser.get(base_url)
    except WebDriverException as e:
        print(f"[!] 启动浏览器失败: {e}")
        browser.quit()
        return

    time.sleep(5)

    # 检查是否需要重新登录
    current_url = browser.current_url
    print(f"[*] 当前页面: {current_url}")
    if 'login' in current_url.lower():
        print("[!] Cookies已过期，请重新运行 --login 登录")
        browser.quit()
        return

    image_links = set()
    scroll_pause = 2
    no_new_count = 0

    last_height = browser.execute_script("return document.body.scrollHeight")
    pbar = tqdm(total=num_images, desc="获取图片链接")

    while len(image_links) < num_images:
        try:
            # 使用JavaScript一次性提取所有img src，避免StaleElementReferenceException
            srcs = browser.execute_script("""
                return Array.from(document.querySelectorAll('img'))
                    .map(img => img.src)
                    .filter(src => src && src.includes('pinimg.com'));
            """)
        except WebDriverException:
            print("[!] 浏览器窗口已关闭或页面异常，停止采集")
            break

        prev_count = len(image_links)
        for src in srcs:
            # 将缩略图URL替换为高分辨率版本
            high_res = src
            for size in ['60x60', '150x150', '236x', '280x280_RS']:
                if f'/{size}/' in src:
                    high_res = src.replace(f'/{size}/', '/736x/')
                    break
            if 'pinimg.com/originals' in high_res or '/736x/' in high_res or '/564x/' in high_res or '/474x/' in high_res:
                if high_res not in image_links:
                    image_links.add(high_res)
                    pbar.update(1)
                if len(image_links) >= num_images:
                    break

        if not srcs:
            print("[!] 当前页面未找到pinimg图片，可能需要重新登录")

        # 滚动至底部加载新内容
        try:
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except WebDriverException:
            break
        time.sleep(scroll_pause)
        try:
            new_height = browser.execute_script("return document.body.scrollHeight")
        except WebDriverException:
            break
        if new_height == last_height and len(image_links) == prev_count:
            no_new_count += 1
            if no_new_count >= 3:
                break
        else:
            no_new_count = 0
        last_height = new_height
    pbar.close()

    print(f"[*] 共获取到{len(image_links)}个图片链接，开始下载...")
    count = 0
    for idx, img_url in enumerate(tqdm(list(image_links)[:num_images], desc="下载图片")):
        ext = os.path.splitext(img_url)[1].split('?')[0]
        filename = os.path.join(out_dir, f"pin_{idx+1}{ext or '.jpg'}")
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            r = requests.get(img_url, timeout=15, headers=headers)
            if r.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(r.content)
                count += 1
            else:
                print(f"[!] 下载失败(HTTP {r.status_code}) {img_url}")
        except Exception as e:
            print(f"[!] 下载异常: {e}")
        time.sleep(0.2)
    print(f"[*] 共下载 {count} 张图片，保存在 {out_dir}/ 目录下")
    browser.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="通过Selenium自动批量下载Pinterest搜索图片")
    parser.add_argument("keywords", nargs='?', default=None, help="Pinterest搜索关键词，如 'floor plan'")
    parser.add_argument("-n", "--num", type=int, default=30, help="下载数量上限")
    parser.add_argument("-o", "--out", type=str, default="downloaded_images", help="保存目录")
    parser.add_argument("--show", action="store_true", help="显示浏览器窗口（默认隐藏）")
    parser.add_argument("--login", action="store_true", help="先登录Pinterest并保存Cookies")
    parser.add_argument("--login-wait", type=int, default=120, help="登录等待时间(秒)，默认120")
    args = parser.parse_args()

    if args.login:
        browser = setup_browser(headless=False)
        do_login(browser, wait_seconds=args.login_wait)
        browser.quit()
    elif args.keywords:
        pinterest_search_and_collect_imgs(
            keywords=args.keywords,
            num_images=args.num,
            out_dir=args.out,
            headless=not args.show
        )
    else:
        parser.print_help()
