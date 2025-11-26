import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import time
import os
import re
from urllib.parse import urljoin
import traceback
import io
from PyPDF2 import PdfReader

TARGET_ARTICLES = {
    "管理文件-国家政策法规": [
        "https://jwc.ysu.edu.cn/info/1040/2741.htm",
        "https://jwc.ysu.edu.cn/info/1040/1183.htm",
        "https://jwc.ysu.edu.cn/info/1040/1130.htm"
    ],
    "管理文件-学籍管理": [
        "https://jwc.ysu.edu.cn/info/1041/7090.htm",
        "https://jwc.ysu.edu.cn/info/1041/7089.htm",
        "https://jwc.ysu.edu.cn/info/1041/1195.htm",
        "https://jwc.ysu.edu.cn/info/1041/3422.htm",
        "https://jwc.ysu.edu.cn/info/1041/2382.htm"
    ],
    "管理文件-教学管理": [
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1042&wbnewsid=7610",  # .jsp 页面
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1042&wbnewsid=6329",  # .jsp 页面
        "https://jwc.ysu.edu.cn/info/1042/7329.htm",
        "https://jwc.ysu.edu.cn/info/1042/7091.htm",
        "https://jwc.ysu.edu.cn/info/1042/4219.htm",
        "https://jwc.ysu.edu.cn/info/1042/4010.htm",
        "https://jwc.ysu.edu.cn/info/1042/3432.htm",
        "https://jwc.ysu.edu.cn/info/1042/3430.htm",
        "https://jwc.ysu.edu.cn/info/1042/3428.htm",
        "https://jwc.ysu.edu.cn/info/1042/3425.htm",
        "https://jwc.ysu.edu.cn/info/1042/3423.htm",
        "https://jwc.ysu.edu.cn/info/1042/2403.htm",
        "https://jwc.ysu.edu.cn/info/1042/2213.htm",
        "https://jwc.ysu.edu.cn/info/1042/1125.htm",
        # 【注】 您之前的列表中可能包含更多教学管理URL，请确保按此格式添加
    ],
    "管理文件-教学质量监控": [
        "https://jwc.ysu.edu.cn/info/1043/3434.htm",
        "https://jwc.ysu.edu.cn/info/1043/3433.htm",
        "https://jwc.ysu.edu.cn/info/1043/3429.htm",
        "https://jwc.ysu.edu.cn/info/1043/3427.htm",
        "https://jwc.ysu.edu.cn/info/1043/3426.htm",
        "https://jwc.ysu.edu.cn/info/1043/3421.htm",
        # 【注】 您之前的列表中可能包含更多质量监控URL，请确保按此格式添加
    ],
    "管理文件-实践教学": [
        # 【修正】 下方是之前粘在一起的URL被正确分离后的结果
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1044&wbnewsid=6929",
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1044&wbnewsid=6930",
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1044&wbnewsid=6219",
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1044&wbnewsid=5914",
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1044&wbnewsid=5913",
        "https://jwc.ysu.edu.cn/info/1044/5912.htm",
        "https://jwc.ysu.edu.cn/info/1044/1253.htm",
        "https://jwc.ysu.edu.cn/info/1044/1252.htm"
    ],
    "管理文件-教学工作规范": [
        # 【修正】 下方是之前粘在一起的URL被正确分离后的结果
        "https://jwc.ysu.edu.cn/content.jsp?urltype=news.NewsContentUrl&wbtreeid=1045&wbnewsid=6509",
        "https://jwc.ysu.edu.cn/info/1045/3420.htm",
        "https://jwc.ysu.edu.cn/info/1045/1529.htm",
        "https://jwc.ysu.edu.cn/info/1045/1128.htm",
    ]
}

BASE_URL = "https://jwc.ysu.edu.cn"
# --- 通用配置 ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'ysu_jwc_MF.json')
SESSION = requests.Session()
SESSION.headers.update(HEADERS)
requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


# --- 2. 核心函数 (已增强) ---
def make_request(url, **kwargs):
    """
    发起网络请求的封装函数，包含错误处理。
    """
    try:
        response = SESSION.get(url, timeout=30, verify=False, allow_redirects=True, **kwargs)
        response.raise_for_status()
        if not kwargs.get('stream'):
            response.encoding = response.apparent_encoding
        return response, None
    except requests.exceptions.RequestException as e:
        return None, str(e)


def scrape_pdfs_from_page(soup, current_page_url):
    """
    从页面中查找PDF链接并提取文本内容 (此版本中未被积极使用，但保留以备将来扩展)。
    """
    pdf_texts = []
    # 此处可以添加查找pdf链接并下载提取文本的逻辑
    return "\n".join(pdf_texts)  # 确保函数有返回值


def parse_content_page(soup, page_url):
    """
    解析文章详情页，提取标题、日期和正文内容。
    兼容多种页面布局。
    """
    title_tag = soup.find('h3', class_='tit') or soup.find(class_='biaoti') or soup.find(
        class_='wz-title') or soup.find('h1') or soup.find('h2')
    title = title_tag.get_text(strip=True) if title_tag else "标题未找到"
    date_tag = soup.find('li', string=re.compile(r'发布时间')) or soup.find(
        string=re.compile(r'更新时间')) or soup.find(string=re.compile(r'发布于'))
    date_str = "日期未找到"
    if date_tag:
        # 更智能地提取日期，去除前缀
        date_text = date_tag.get_text(strip=True)
        date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', date_text)
        date_str = date_match.group(1) if date_match else date_text.split('：')[-1].strip()
    # 【★★★ 最终升级！增加对.jsp页面特殊div的识别！★★★】
    content_div = (soup.find('div', class_='v_news_content') or  # 模式A: 标准内容区
                   soup.find('div', id='vsb_content') or  # 模式A的变种
                   soup.find('div', class_="main_content") or  # 模式A的变种2
                   soup.find('div', class_='zhengwen') or  # 模式B: iframe内部
                   soup.find('form', {'name': '_newscontent_fromname'})  # 模式C: JSP动态页面
                   )
    if not content_div:
        return None  # 如果连这五种模式都找不到，那就真的没内容
    # 数据净化：移除脚本、样式、iframe等不需要的标签
    for unwanted_tag in content_div.find_all(['script', 'style', 'iframe']):
        unwanted_tag.decompose()
    content = content_div.get_text('\n', strip=True)
    if not content:
        return None

    return {'title': title, 'date': date_str, 'content': content}


def get_article_details(url):
    """
    获取单个文章的详细信息，核心处理逻辑。
    会自动尝试直接解析，如果失败则会尝试钻取iframe。
    """
    try:
        response, error = make_request(url)
        if error:
            return {'status': 'failed', 'reason': f'网络请求失败: {error}'}
        soup = BeautifulSoup(response.text, 'lxml')
        # 步骤1: 尝试直接解析，如果成功就直接返回
        direct_parse_result = parse_content_page(soup, url)
        if direct_parse_result:
            direct_parse_result['status'] = 'success'
            return direct_parse_result
        # 步骤2: 【核心升级】如果直接解析失败，则寻找 iframe
        iframe = soup.find('iframe', id='main_frame') or soup.find('iframe')
        if not iframe:
            return {'status': 'failed', 'reason': '页面结构特殊，且未发现可供钻取的 iframe。'}
        iframe_src = iframe.get('src')
        if not iframe_src:
            return {'status': 'failed', 'reason': '发现了 iframe，但它没有 src 属性。'}
        # 步骤3: 对 iframe 的地址发起第二次请求
        iframe_full_url = urljoin(BASE_URL, iframe_src)

        iframe_response, iframe_error = make_request(iframe_full_url)
        if iframe_error:
            return {'status': 'failed', 'reason': f'成功钻取 iframe，但请求其内部地址失败: {iframe_error}'}
        iframe_soup = BeautifulSoup(iframe_response.text, 'lxml')
        # 步骤4: 用我们的标准解析器去解析 iframe 的内容
        iframe_parse_result = parse_content_page(iframe_soup, iframe_full_url)
        if not iframe_parse_result:
            return {'status': 'failed', 'reason': '成功进入 iframe，但其内部页面结构依然无法解析。'}

        iframe_parse_result['status'] = 'success'
        return iframe_parse_result
    except Exception:
        return {'status': 'failed', 'reason': f'解析过程中发生未知严重错误: {traceback.format_exc()}'}


# --- 3. 主执行逻辑 ---
if __name__ == "__main__":

    all_urls = []
    # 【健壮性升级】 重构URL列表，确保一个URL对象包含自己的分类和地址
    for category, urls in TARGET_ARTICLES.items():
        for url in urls:
            all_urls.append({'category': category, 'url': url})

    print(f"--- 燕山大学教务处 ---\n")
    print(f"检测到 {len(all_urls)} 个有效目标URL待采集。")
    successful_articles, failed_urls = [], []

    with tqdm(all_urls, desc="采集进度", unit="篇") as pbar:
        for url_info in pbar:
            url = url_info['url']
            category = url_info['category']
            pbar.set_description(f"正在采集: {os.path.basename(url)}")
            result = get_article_details(url)

            if result['status'] == 'success':
                successful_articles.append({
                    'category': category,
                    'title': result['title'],
                    'date': result['date'],
                    'url': url,
                    'content': result['content']
                })
                pbar.set_description(f"✓ {str(result.get('title', '无标题'))[:20]}...")
            else:
                failed_urls.append({
                    'category': category,
                    'url': url,
                    'reason': result['reason']
                })
                pbar.set_description(f"✗ 失败: {os.path.basename(url)}")

            time.sleep(0.1)  # 轻微延时，避免对服务器造成过大压力
    # --- 任务结束，生成报告 ---
    print("\n\n" + "=" * 30 + " 【采集任务最终报告】 " + "=" * 30)
    if successful_articles:
        # 确保输出目录存在
        output_dir = os.path.dirname(OUTPUT_FILE)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 使用 pandas 保存为 JSON 文件，格式美观
        pd.DataFrame(successful_articles).to_json(OUTPUT_FILE, orient='records', force_ascii=False, indent=4)
        print(f"\n✓ {len(successful_articles)} 篇采集成功，已保存至: {os.path.abspath(OUTPUT_FILE)}")
    else:
        print("\n- 未能成功采集任何数据。")
    if failed_urls:
        print(f"\n✗ {len(failed_urls)} 个URL采集失败，详细信息如下:")
        for entry in failed_urls:
            print(
                f"  - 分类: {entry['category']}\n    URL : {entry['url']}\n    原因: {entry['reason'].splitlines()[0]}\n" + "-" * 20)
    else:
        print("\n恭喜！所有URL均已成功采集，无任何失败记录！")
    print("\n" + "=" * 80)
    print("--- 爬虫任务结束 ---")