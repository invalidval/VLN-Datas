import os
import sys
import time
import json
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

def setup_browser(headless=True, window_size=(1920, 1080)):
    """配置Chrome浏览器"""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument(f'--window-size={window_size[0]},{window_size[1]}')
    options.add_argument('--force-device-scale-factor=2')  # 2x 分辨率

    browser = webdriver.Chrome(options=options)
    return browser

def wait_for_map_load(browser, timeout=15):
    """等待地图完全加载"""
    try:
        # 等待 canvas 元素出现
        WebDriverWait(browser, timeout).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
        # 额外等待地图渲染完成
        time.sleep(5)
        return True
    except TimeoutException:
        print("[!] 地图加载超时")
        return False

def click_floor_button(browser, floor_name):
    """点击楼层按钮切换楼层"""
    try:
        # 尝试多种选择器查找楼层按钮
        selectors = [
            f"//button[contains(text(), '{floor_name}')]",
            f"//div[contains(text(), '{floor_name}')]",
            f"//*[@data-floor='{floor_name}']",
            f"//*[contains(@class, 'floor') and contains(text(), '{floor_name}')]"
        ]

        for selector in selectors:
            try:
                elements = browser.find_elements(By.XPATH, selector)
                for elem in elements:
                    if elem.is_displayed() and elem.is_enabled():
                        elem.click()
                        time.sleep(3)  # 等待楼层切换
                        print(f"[*] 已切换到楼层: {floor_name}")
                        return True
            except Exception:
                continue

        print(f"[!] 未找到楼层按钮: {floor_name}")
        return False
    except Exception as e:
        print(f"[!] 切换楼层失败: {e}")
        return False

def hide_ui_elements(browser):
    """隐藏UI元素，只保留地图"""
    try:
        browser.execute_script("""
            // 隐藏可能的UI元素
            const selectors = [
                '[class*="search"]',
                '[class*="Search"]',
                '[class*="button"]',
                '[class*="Button"]',
                '[class*="control"]',
                '[class*="Control"]',
                '[class*="menu"]',
                '[class*="Menu"]',
                '[class*="header"]',
                '[class*="Header"]'
            ];

            selectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => {
                    // 只隐藏非地图元素
                    if (!el.querySelector('canvas')) {
                        el.style.display = 'none';
                    }
                });
            });
        """)
        time.sleep(1)
    except Exception as e:
        print(f"[!] 隐藏UI元素失败: {e}")

def capture_map_canvas(browser, output_file):
    """截取地图 canvas"""
    try:
        # 查找 canvas 元素
        canvas = browser.find_element(By.TAG_NAME, "canvas")

        # 截取 canvas
        canvas.screenshot(output_file)
        print(f"[*] 已保存: {output_file}")
        return True
    except Exception as e:
        print(f"[!] Canvas 截图失败: {e}")

        # 备用方案：全屏截图
        try:
            browser.save_screenshot(output_file)
            print(f"[*] 已保存全屏截图: {output_file}")
            return True
        except Exception as e2:
            print(f"[!] 全屏截图也失败: {e2}")
            return False

def download_floor_maps(building_id=1, output_dir="airport_floor_maps",
                       floors=None, headless=False):
    """
    下载指定建筑物的楼层地图

    Args:
        building_id: 建筑物ID (1=Terminal1, 2=Terminal2, 3=Concourse)
        output_dir: 输出目录
        floors: 要下载的楼层列表，None表示所有楼层
        headless: 是否无头模式
    """
    os.makedirs(output_dir, exist_ok=True)

    # 建筑物和楼层映射
    building_floors = {
        1: {  # Terminal 1
            'name': 'Terminal1',
            'floors': ['B2', 'B1', '1F', '2F', '3F', '4F']
        },
        2: {  # Terminal 2
            'name': 'Terminal2',
            'floors': ['B1', 'M', '1F', '2F', '3F', '4F', '5F']
        },
        3: {  # Concourse
            'name': 'Concourse',
            'floors': ['B1', '1F', '2F', '3F', '4F']
        }
    }

    if building_id not in building_floors:
        print(f"[!] 无效的建筑物ID: {building_id}")
        return

    building_info = building_floors[building_id]
    building_name = building_info['name']
    available_floors = building_info['floors']

    if floors is None:
        floors = available_floors
    else:
        # 验证楼层
        floors = [f for f in floors if f in available_floors]

    print(f"[*] 建筑物: {building_name}")
    print(f"[*] 楼层: {', '.join(floors)}")

    browser = setup_browser(headless=headless, window_size=(2560, 1440))

    try:
        # 打开地图页面
        # Terminal 1: P01, Terminal 2: P02
        terminal_id = f"P0{building_id}"
        url = f"https://www.airport.kr/geomap/ap_en/view.do?type=2&alertType=0&tmnlId={terminal_id}"

        print(f"[*] 打开地图: {url}")
        browser.get(url)

        # 等待地图加载
        if not wait_for_map_load(browser):
            print("[!] 地图加载失败")
            return

        print("[*] 地图加载完成")

        # 隐藏UI元素
        hide_ui_elements(browser)

        # 截取默认楼层
        default_file = os.path.join(output_dir, f"{building_name}_default.png")
        capture_map_canvas(browser, default_file)

        # 遍历每个楼层
        for floor in floors:
            print(f"\n[*] 处理楼层: {floor}")

            # 尝试切换楼层
            if click_floor_button(browser, floor):
                # 等待地图更新
                time.sleep(3)

                # 隐藏UI
                hide_ui_elements(browser)

                # 截图
                output_file = os.path.join(output_dir, f"{building_name}_{floor}.png")
                capture_map_canvas(browser, output_file)
            else:
                print(f"[!] 无法切换到楼层 {floor}，跳过")

        print(f"\n[*] 完成！地图已保存到 {output_dir}/")

    finally:
        browser.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载韩国仁川机场室内地图（高质量截图）")
    parser.add_argument("-b", "--building", type=int, default=1, choices=[1, 2, 3],
                        help="建筑物ID: 1=Terminal1, 2=Terminal2, 3=Concourse")
    parser.add_argument("-o", "--out", type=str, default="airport_floor_maps",
                        help="输出目录")
    parser.add_argument("-f", "--floors", type=str, nargs='+',
                        help="指定楼层，例如: -f 1F 2F 3F")
    parser.add_argument("--show", action="store_true",
                        help="显示浏览器窗口")
    args = parser.parse_args()

    download_floor_maps(
        building_id=args.building,
        output_dir=args.out,
        floors=args.floors,
        headless=not args.show
    )
