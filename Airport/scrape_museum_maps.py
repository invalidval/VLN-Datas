#!/usr/bin/env python3
"""
National Museum of Singapore Indoor Map Scraper
用于下载新加坡国家博物馆的室内地图，用于VLN训练数据
"""

import os
import time
import json
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class MuseumMapScraper:
    def __init__(self, base_url, output_dir="museum_maps"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.metadata = []

    def create_directories(self):
        """创建输出目录结构"""
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)

    def fetch_page(self, url):
        """获取网页内容"""
        try:
            print(f"正在获取页面: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"获取页面失败: {e}")
            return None

    def extract_map_images(self, html_content):
        """从HTML中提取地图图片URL"""
        soup = BeautifulSoup(html_content, 'html.parser')
        image_urls = []

        # 查找所有图片标签
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                # 过滤出可能是地图的图片
                if any(keyword in src.lower() for keyword in ['map', 'floor', 'plan', 'level']):
                    full_url = urljoin(self.base_url, src)
                    alt_text = img.get('alt', '')
                    title = img.get('title', '')

                    image_urls.append({
                        'url': full_url,
                        'alt': alt_text,
                        'title': title,
                        'src_original': src
                    })

        # 也查找可能在其他标签中的图片链接
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']):
                if any(keyword in href.lower() for keyword in ['map', 'floor', 'plan', 'level']):
                    full_url = urljoin(self.base_url, href)
                    image_urls.append({
                        'url': full_url,
                        'alt': link.get_text(strip=True),
                        'title': '',
                        'src_original': href
                    })

        # 如果没有找到特定关键词的图片，获取所有图片
        if not image_urls:
            print("未找到包含关键词的地图图片，尝试获取所有图片...")
            for img in soup.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(self.base_url, src)
                    image_urls.append({
                        'url': full_url,
                        'alt': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'src_original': src
                    })

        return image_urls

    def download_image(self, image_info, index):
        """下载单个图片"""
        url = image_info['url']

        try:
            print(f"正在下载 [{index}]: {url}")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # 生成文件名
            parsed_url = urlparse(url)
            original_filename = os.path.basename(parsed_url.path)
            ext = os.path.splitext(original_filename)[1] or '.jpg'

            # 使用索引和描述生成有意义的文件名
            alt_text = image_info.get('alt', '').replace(' ', '_').replace('/', '_')[:50]
            if alt_text:
                filename = f"map_{index:03d}_{alt_text}{ext}"
            else:
                filename = f"map_{index:03d}{ext}"

            # 清理文件名中的非法字符
            filename = "".join(c for c in filename if c.isalnum() or c in ('_', '-', '.'))

            filepath = self.output_dir / "images" / filename

            # 保存图片
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 计算文件哈希
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()

            # 保存元数据
            metadata = {
                'index': index,
                'filename': filename,
                'original_url': url,
                'alt_text': image_info.get('alt', ''),
                'title': image_info.get('title', ''),
                'file_size': os.path.getsize(filepath),
                'md5_hash': file_hash,
                'download_time': datetime.now().isoformat()
            }
            self.metadata.append(metadata)

            print(f"✓ 已保存: {filename} ({metadata['file_size']} bytes)")
            return True

        except requests.RequestException as e:
            print(f"✗ 下载失败: {e}")
            return False

    def save_metadata(self):
        """保存元数据到JSON文件"""
        metadata_file = self.output_dir / "metadata" / "download_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source_url': self.base_url,
                'download_date': datetime.now().isoformat(),
                'total_images': len(self.metadata),
                'images': self.metadata
            }, f, indent=2, ensure_ascii=False)
        print(f"\n元数据已保存到: {metadata_file}")

    def run(self):
        """执行爬取流程"""
        print("=" * 60)
        print("新加坡国家博物馆室内地图爬虫")
        print("=" * 60)

        # 创建目录
        self.create_directories()

        # 获取页面
        html_content = self.fetch_page(self.base_url)
        if not html_content:
            print("无法获取页面内容，退出")
            return

        # 提取图片URL
        image_urls = self.extract_map_images(html_content)
        print(f"\n找到 {len(image_urls)} 个图片")

        if not image_urls:
            print("未找到任何图片，请检查URL或页面结构")
            return

        # 下载图片
        print("\n开始下载图片...")
        success_count = 0
        for idx, img_info in enumerate(image_urls, 1):
            if self.download_image(img_info, idx):
                success_count += 1
            # 礼貌延迟，避免对服务器造成压力
            time.sleep(1)

        # 保存元数据
        self.save_metadata()

        # 输出统计
        print("\n" + "=" * 60)
        print(f"下载完成！")
        print(f"成功: {success_count}/{len(image_urls)}")
        print(f"输出目录: {self.output_dir.absolute()}")
        print("=" * 60)


def main():
    # 目标URL
    url = "https://www.nhb.gov.sg/nationalmuseum/plan-your-visit/museum-map"

    # 创建爬虫实例并运行
    scraper = MuseumMapScraper(url, output_dir="museum_maps")
    scraper.run()


if __name__ == "__main__":
    main()
