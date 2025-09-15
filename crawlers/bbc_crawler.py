import requests
from bs4 import BeautifulSoup
import datetime
import time
import csv
import os
from lunar_mapping import get_lunar_new_year_ranges

# 儲存資料夾與 CSV 路徑
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "org_data", "bbc")
os.makedirs(SAVE_DIR, exist_ok=True)
CSV_PATH = os.path.join(SAVE_DIR, "bbc.csv")


def get_article_content(url):
    """抓取 BBC 文章頁面的內文"""
    try:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code != 200:
            return ""
        soup = BeautifulSoup(res.text, "html.parser")

        # BBC 文章內容可能在 <article> 或 <div data-component="text-block"> 中
        paragraphs = soup.select("article p, div[data-component='text-block'] p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return content
    except Exception as e:
        print(f"抓取文章失敗: {url}, 錯誤: {e}")
        return ""


def search_bbc_articles(keyword, start_date, end_date, max_articles, collected_count):
    """搜尋 BBC 文章，依日期過濾"""
    articles = []
    base_url = "https://www.bbc.co.uk/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    page = 1

    while len(articles) + collected_count < max_articles:
        params = {"q": keyword, "page": page}
        response = requests.get(base_url, params=params, headers=headers)

        if response.status_code != 200:
            print(f"BBC 搜尋失敗: {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # 搜尋結果通常在 <ul> -> <li> -> <a>
        results = soup.select("ul li a[href]")
        if not results:
            break

        for link in results:
            if len(articles) + collected_count >= max_articles:
                break

            url = link["href"]
            if not url.startswith("http"):
                url = "https://www.bbc.co.uk" + url
            title = link.get_text(strip=True)

            # 嘗試從同一個 <li> 中找日期與描述
            parent_li = link.find_parent("li")
            date_tag = parent_li.find("time") if parent_li else None
            desc_tag = parent_li.find("p")

            date_str = date_tag["datetime"] if date_tag and date_tag.has_attr("datetime") else ""
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            # BBC 日期格式: "2023-01-22T12:00:00.000Z"
            try:
                pub_date = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date() if date_str else None
            except Exception:
                pub_date = None

            # 僅保留在日期範圍內的文章
            if pub_date and start_date <= pub_date <= end_date:
                content = get_article_content(url)
                articles.append({
                    "id": f"bbc_{pub_date}_{len(articles)+collected_count+1}",
                    "platform": "bbc",
                    "date": pub_date,
                    "title": title,
                    "desc": desc,
                    "url": url,
                    "content": content
                })

        print(f"BBC {keyword} 第 {page} 頁解析完畢，已收集 {len(articles)+collected_count} 篇...")
        time.sleep(1)  # 避免爬太快被封
        page += 1

    return articles


def crawl_bbc_lunar_new_year(start_year, end_year, days_before=14, days_after=14, keywords=None, max_articles=500):
    """依年份與關鍵字，搜尋農曆新年相關 BBC 文章"""
    if keywords is None:
        keywords = ["Lunar New Year", "Chinese New Year", "Chinese", "New Year"]

    # 取得每年農曆新年範圍
    date_ranges = get_lunar_new_year_ranges(start_year, end_year, days_before, days_after)
    all_articles = []

    for year, (start_date, end_date) in zip(range(start_year, end_year + 1), date_ranges):
        print(f"搜尋 {year} 農曆新年前後文章: {start_date} ~ {end_date}")
        for keyword in keywords:
            if len(all_articles) >= max_articles:
                break
            articles = search_bbc_articles(keyword, start_date, end_date, max_articles, len(all_articles))
            for article in articles:
                article["year"] = year
                article["keyword"] = keyword
            all_articles.extend(articles)
            print(f"目前總收集 {len(all_articles)}/{max_articles} 篇...")
        if len(all_articles) >= max_articles:
            break

    # 儲存每篇文章的內容到 txt
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

    # 儲存索引到 CSV
    with open(CSV_PATH, "w", newline='', encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["id", "platform", "year", "keyword", "date", "title", "desc", "url", "content_path"])
        for art in all_articles:
            writer.writerow([
                art["id"], art["platform"], art["year"], art["keyword"],
                art["date"], art["title"], art["desc"], art["url"], f"{art['id']}.txt"
            ])

    print(f"已儲存 {len(all_articles)} 筆 BBC 農曆新年相關文章到 {CSV_PATH}，文章內容存於 {SAVE_DIR}")


if __name__ == "__main__":
    crawl_bbc_lunar_new_year(2020, 2025, days_before=14, days_after=14, max_articles=500)
