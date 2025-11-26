import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import os
import re
import traceback

# --- 1. 配置区域 ---
TARGET_CATEGORIES = [
    {
        "name": "通知公告",
        "url": "https://jwc.ysu.edu.cn/tzgg1.htm"
    },
    {
        "name": "教学新闻",
        "url": "https://jwc.ysu.edu.cn/jxxw1.htm"
    },
    {
        "name": "教学工作简报",
        "url": "https://jwc.ysu.edu.cn/jxgzjb1.htm"
    }
]

BASE_URL = "https://jwc.ysu.edu.cn/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
COMBINED_OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'ysu_jwc_TJJ.json')

SESSION = requests.Session()
SESSION.headers.update(HEADERS)
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


# --- 2. 核心功能函数 (已验证其健壮性) ---

def make_request(url):
    try:
        response = SESSION.get(url, timeout=20, verify=False, allow_redirects=True)
        response.raise_for_status()
        response.encoding = 'utf-8'
        return response
    except requests.exceptions.RequestException:
        return None


def get_total_pages(category_url):
    response = make_request(category_url)
    if not response: return 1
    html_text = response.text
    js_match = re.search(r'\_gotopage\_fun\((\d+),', html_text)
    if js_match:
        return int(js_match.group(1))
    soup = BeautifulSoup(html_text, 'lxml')
    page_text = soup.get_text()
    match = re.search(r'共\s*(\d+)\s*页', page_text)
    if match:
        return int(match.group(1))
    return 1


def get_article_links_from_page(list_page_url):
    links, response = [], make_request(list_page_url)
    if not response: return links

    soup = BeautifulSoup(response.text, 'lxml')
    list_container = soup.find('div', class_='moreContant') or soup.find('div', class_='nrys')
    if not list_container: return links

    for item in list_container.find_all('li'):
        a_tag = item.find('a')
        if a_tag and a_tag.has_attr('href'):
            title = a_tag.get('title', a_tag.get_text()).strip()
            # 简化并统一URL拼接逻辑
            full_url = requests.compat.urljoin(BASE_URL, a_tag['href'].lstrip('./'))
            links.append({'title': title, 'url': full_url})

    return links


def get_article_details(article_url):
    try:
        response = make_request(article_url)
        if not response: return None
        soup = BeautifulSoup(response.text, 'lxml')
        content_div = (soup.find('div', class_='v_news_content') or
                       soup.find('div', id='vsb_content') or
                       soup.find('div', class_="main_content"))
        if content_div:
            for unwanted_tag in content_div.find_all(['style', 'script']):
                unwanted_tag.decompose()
            return content_div.get_text('\n', strip=True)
        return "正文内容获取失败"
    except Exception:
        return None


# --- 3. 主执行逻辑 ---
def process_category(category_config):
    category_name, category_url = category_config["name"], category_config["url"]
    print(f"\n===== 开始处理板块: 【{category_name}】=====")

    try:
        total_pages = get_total_pages(category_url)
        print(f"  [1/3] 检测到 {total_pages} 页内容...")

        # 【BUG 修复处】采用更简洁可靠的分页URL生成逻辑
        url_base_for_pagination = category_url.replace('.htm', '')
        page_urls = [category_url]  # 包含第一页
        # 添加从 (总页数-1) 到 1 的倒序页面
        if total_pages > 1:
            # `tzgg1.htm` 的其他页面是 `tzgg1/84.htm`, `tzgg1/83.htm`...
            page_urls.extend(f"{url_base_for_pagination}/{i}.htm" for i in range(total_pages - 1, 0, -1))

        all_links = []
        for url in tqdm(page_urls, desc="  [2/3] 提取链接", unit="页", leave=False):
            all_links.extend(get_article_links_from_page(url))
            time.sleep(0.05)

        unique_links = [dict(t) for t in {tuple(d.items()) for d in all_links}]
        print(f"  - 找到 {len(unique_links)} 篇独特的文章。")

        articles_data = []
        for link_info in tqdm(unique_links, desc="  [3/3] 爬取内容", unit="篇", leave=False):
            content = get_article_details(link_info['url'])
            if content and content != "正文内容获取失败":
                articles_data.append({
                    'category': category_name,
                    'title': link_info['title'],
                    'url': link_info['url'],
                    'content': content
                })
            time.sleep(0.05)

        print(f"  ✓ 【{category_name}】板块处理完成, 成功获取 {len(articles_data)} 篇文章。")
        return articles_data
    except Exception:
        print(f"  ✗ 处理板块【{category_name}】时发生未知错误。")
        traceback.print_exc()
        return []


if __name__ == "__main__":
    print("--- 燕山大学教务处多板块爬虫启动 (YSUScraper_v2.1 - Patched) ---")
    all_site_data = []

    for category in TARGET_CATEGORIES:
        category_data = process_category(category)
        all_site_data.extend(category_data)

    if all_site_data:
        df = pd.DataFrame(all_site_data)
        output_dir = os.path.dirname(COMBINED_OUTPUT_FILE)
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        df.to_json(COMBINED_OUTPUT_FILE, orient='records', force_ascii=False, indent=4)
        print(f"\n\n{'=' * 25} 所有任务已完成! {'=' * 25}")
        print(f"✓ 所有板块的数据已合并保存至: {os.path.abspath(COMBINED_OUTPUT_FILE)}")

        category_counts = df['category'].value_counts()
        print("\n--- 数据统计 ---")
        for name, count in category_counts.items():
            print(f" - {name}: {count} 篇")
        print(f" - 总计: {len(df)} 篇")
        print("--------------------")
    else:
        print("\n✗ 未能从任何板块抓取到有效数据。")

    print("\n--- 爬虫任务结束 ---")
