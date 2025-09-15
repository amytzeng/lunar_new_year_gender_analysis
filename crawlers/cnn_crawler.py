import os
import csv
import time
import math
import datetime
import requests
from bs4 import BeautifulSoup
from lunar_mapping import get_lunar_new_year_ranges   # 你的農曆日期工具

# ---------- 參數與輸出路徑 ----------
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "org_data", "cnn")
os.makedirs(SAVE_DIR, exist_ok=True)
CSV_PATH = os.path.join(SAVE_DIR, "cnn.csv")

API_URL = "https://search.api.cnn.io/content"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---------- 抓取單篇文章全文 ----------
def get_article_content(url):
    """用 requests 抓 CNN 文章內文"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # CNN 新版文章內文常見結構
        paras = soup.select("div.article__content p") \
                or soup.select("section#body-text p") \
                or soup.select("div.zn-body__paragraph")
        return "\n".join([p.get_text(strip=True) for p in paras])
    except Exception as e:
        print(f"[文章抓取失敗] {url}: {e}")
        return ""

# ---------- 使用 CNN 官方 JSON API ----------
def search_cnn_articles(keyword, start_date, end_date, max_articles, collected_count):
    """
    直接呼叫 CNN 官方搜尋 API
    :param keyword: 搜尋關鍵字
    :param start_date, end_date: datetime.date 篩選
    :param max_articles: 全部最大數量
    :param collected_count: 已收集的篇數，用於計算剩餘
    """
    articles = []
    size = 50  # 一頁最多 50 筆
    page = 1
    fetched_total = 0

    while len(articles) + collected_count < max_articles:
        params = {
            "q": keyword,
            "size": size,
            "page": page,
            "from": start_date.strftime("%Y-%m-%d"),
            "to": end_date.strftime("%Y-%m-%d"),
            "sort": "newest"
        }
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"[API失敗] {r.status_code}")
            break
        data = r.json()
        results = data.get("result", [])
        if not results:
            break

        # CNN API 會回傳 total 給我們做進度
        total = data.get("total", 0)
        total_pages = math.ceil(total / size)
        print(f"關鍵字: {keyword} - 第 {page}/{total_pages} 頁 (共 {total} 筆)")

        for item in results:
            if len(articles) + collected_count >= max_articles:
                break
            # API 回傳時間格式例如 "2024-02-10T04:32:00Z"
            try:
                pub_date = datetime.datetime.strptime(item.get("published_date","")[:10], "%Y-%m-%d").date()
            except Exception:
                pub_date = None
            if not pub_date or pub_date < start_date or pub_date > end_date:
                continue

            url = item.get("url", "")
            title = item.get("headline", "")
            desc = item.get("description", "")

            content = get_article_content(url)
            articles.append({
                "id": f"cnn_{pub_date}_{len(articles)+collected_count+1}",
                "platform": "cnn",
                "date": pub_date,
                "title": title,
                "desc": desc,
                "url": url,
                "content": content
            })
        if len(results) < size:
            break
        page += 1
        time.sleep(1)
    return articles

# ---------- 主流程 ----------
def crawl_cnn_lunar_new_year(start_year, end_year, days_before=14, days_after=14,
                             keywords=None, max_articles=500):
    """
    從 CNN API 依農曆新年前後日期抓取新聞
    """
    if keywords is None:
        keywords = ["Lunar New Year", "Chinese New Year", "Chinese", "New Year"]

    all_articles = []
    date_ranges = get_lunar_new_year_ranges(start_year, end_year, days_before, days_after)

    for year, (start_date, end_date) in zip(range(start_year, end_year + 1), date_ranges):
        print(f"\n=== {year} 農曆新年前後: {start_date} ~ {end_date} ===")
        for keyword in keywords:
            if len(all_articles) >= max_articles:
                break
            arts = search_cnn_articles(keyword, start_date, end_date,
                                       max_articles, len(all_articles))
            for a in arts:
                a["year"] = year
                a["keyword"] = keyword
            all_articles.extend(arts)
            print(f"目前總收集 {len(all_articles)}/{max_articles} 篇")
        if len(all_articles) >= max_articles:
            break

    # 儲存文章內容到單檔 txt
    for art in all_articles:
        art_path = os.path.join(SAVE_DIR, f"{art['id']}.txt")
        with open(art_path, "w", encoding="utf-8") as f:
            f.write(f"id: {art['id']}\n")
            f.write(f"date: {art['date']}\n")
            f.write(f"title: {art['title']}\n")
            f.write(f"url: {art['url']}\n")
            f.write(f"desc: {art['desc']}\n")
            f.write("content:\n")
            f.write(art['content'])

    # CSV 索引
    with open(CSV_PATH, "w", newline='', encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["id", "platform", "year", "keyword", "date",
                         "title", "desc", "url", "content_path"])
        for art in all_articles:
            writer.writerow([
                art["id"], art["platform"], art["year"], art["keyword"],
                art["date"], art["title"], art["desc"], art["url"],
                f"{art['id']}.txt"
            ])
    print(f"\n已儲存 {len(all_articles)} 筆 CNN 農曆新年相關文章到 {CSV_PATH}")

# ---------- 直接執行 ----------
if __name__ == "__main__":
    crawl_cnn_lunar_new_year(2020, 2025, days_before=14, days_after=14, max_articles=500)
