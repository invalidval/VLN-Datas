import os
import sys
import time
import requests
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
from pinterest_downloader import Pinterest, PinterestError
from tqdm import tqdm

def download_images_by_keywords(keywords, limit=30, out_dir="downloaded_images"):
    os.makedirs(out_dir, exist_ok=True)
    p = Pinterest()
    print(f"[*] 搜索关键词: {keywords}")
    try:
        results = p.search(keywords)
    except PinterestError as e:
        print(f"[!] 搜索失败: {e}")
        return
    
    # 如果返回为字典且有 'data' 键，或直接为列表
    if isinstance(results, dict) and 'data' in results:
        pins = results['data']
    elif isinstance(results, list):
        pins = results
    else:
        print(f"[!] 未获取到有效图片数据")
        return

    if not pins:
        print("[!] 未获取到任何图片")
        return

    count = 0
    for item in tqdm(pins, desc="下载进度"):
        img_url = None
        if isinstance(item, dict):
            images = item.get("images")
            if isinstance(images, dict):
                img_url = images.get("orig")
            if not img_url:
                img_url = item.get("default_image")
        if img_url:
            ext = os.path.splitext(img_url)[1].split('?')[0]
            filename = os.path.join(out_dir, f"pin_{count+1}{ext or '.jpg'}")
            try:
                r = requests.get(img_url, timeout=10)
                if r.status_code == 200:
                    with open(filename, "wb") as f:
                        f.write(r.content)
                    count += 1
                else:
                    print(f"[!] 下载失败，状态码: {r.status_code}，图片链接: {img_url}")
            except Exception as e:
                print(f"[!] 下载出错: {e}")
        if count >= limit:
            break
        time.sleep(0.5)
    print(f"[*] 共下载 {count} 张图片，保存在 {out_dir}/ 目录下")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="批量下载 Pinterest 搜索关键词的所有图片")
    parser.add_argument("keywords", help="Pinterest搜索关键词，如 'floor plan'")
    parser.add_argument("-n", "--num", type=int, default=30, help="下载数量上限")
    parser.add_argument("-o", "--out", type=str, default="downloaded_images", help="保存目录")
    args = parser.parse_args()

    download_images_by_keywords(args.keywords, limit=args.num, out_dir=args.out)
