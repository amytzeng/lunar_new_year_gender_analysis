import os
import csv
import time
import datetime
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from lunar_mapping import get_lunar_new_year_ranges   # 你原本的函式


SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "org_data", "abc_selenium")
os.makedirs(SAVE_DIR, exist_ok=True)
CSV_PATH = os.path.join(SAVE_DIR, "abc.csv")


def create_driver(headless=False):
    """啟動 ChromeDriver"""
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)
    driver.set_page_load_timeout(30)
    return driver


def get_article_content(driver, url):
    """打開單篇 ABC News 文章並抓取內文"""
    try:
        driver.get(url)
        time.sleep(2)  # 等待頁面渲染
        soup = BeautifulSoup(driver.page_source, "html.parser")
        paragraphs = soup.select("div.Article__Content p")
        return "\n".join([p.get_text(strip=True) for p in paragraphs])
    except Exception as e:
        print(f"抓取文章失敗: {url} ({e})")
        return ""


def search_abc_articles(driver, keyword, start_date, end_date, max_articles, collected_count):
    """
    使用 Selenium 動態爬 ABC News 搜尋結果
    """
    articles = []
    page = 1

    while len(articles) + collected_count < max_articles:
        search_url = f"https://abcnews.go.com/search?searchtext={keyword}&page={page}"
        print(f"開啟 {search_url}")
        driver.get(search_url)
        time.sleep(3)  # 等待 JS 載入

        soup = BeautifulSoup(driver.page_source, "html.parser")
        results = soup.select("div.ContentRollItem")
        if not results:
            break

        for item in results:
            if len(articles) + collected_count >= max_articles:
                break
            link_tag = item.select_one("a[href]")
            if not link_tag:
                continue
            url = link_tag["href"]
            if not url.startswith("http"):
                url = "https://abcnews.go.com" + url
            title = link_tag.get_text(strip=True)

            date_tag = item.select_one("time")
            date_str = date_tag["datetime"] if date_tag and date_tag.has_attr("datetime") else ""
            try:
                pub_date = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date() if date_str else None
            except Exception:
                pub_date = None

            desc_tag = item.select_one("p")
            desc = desc_tag.get_text(strip=True) if desc_tag else ""

            if pub_date and start_date <= pub_date <= end_date:
                content = get_article_content(driver, url)
                articles.append({
                    "id": f"abc_{pub_date}_{len(articles)+collected_count+1}",
                    "platform": "abc",
                    "date": pub_date,
                    "title": title,
                    "desc": desc,
                    "url": url,
                    "content": content
                })

        print(f"ABC News {keyword} 第 {page} 頁解析完畢，已收集 {len(articles)+collected_count} 篇...")
        page += 1
        # 嘗試找下一頁按鈕，若無則停止
        if not soup.select_one("a[aria-label='Next']"):
            break

    return articles


def crawl_abc_lunar_new_year(start_year, end_year, days_before=14, days_after=14,
                             keywords=None, max_articles=500):
    """
    依年份與關鍵字，搜尋農曆新年相關 ABC News 文章 (Selenium 版本)
    """
    if keywords is None:
        keywords = ["Lunar New Year", "Chinese New Year", "Chinese", "New Year"]

    driver = create_driver(headless=True)
    all_articles = []

    try:
        date_ranges = get_lunar_new_year_ranges(start_year, end_year, days_before, days_after)
        for year, (start_date, end_date) in zip(range(start_year, end_year + 1), date_ranges):
            print(f"搜尋 {year} 農曆新年前後文章: {start_date} ~ {end_date}")
            for keyword in keywords:
                if len(all_articles) >= max_articles:
                    break
                arts = search_abc_articles(driver, keyword, start_date, end_date,
                                           max_articles, len(all_articles))
                for a in arts:
                    a["year"] = year
                    a["keyword"] = keyword
                all_articles.extend(arts)
                print(f"目前總收集 {len(all_articles)}/{max_articles} 篇...")
            if len(all_articles) >= max_articles:
                break
    finally:
        driver.quit()

    # 儲存文章內容
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

    # 儲存 CSV
    with open(CSV_PATH, "w", newline='', encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["id", "platform", "year", "keyword",
                         "date", "title", "desc", "url", "content_path"])
        for art in all_articles:
            writer.writerow([
                art["id"], art["platform"], art["year"], art["keyword"],
                art["date"], art["title"], art["desc"], art["url"],
                f"{art['id']}.txt"
            ])

    print(f"已儲存 {len(all_articles)} 筆 ABC News 農曆新年相關文章到 {CSV_PATH}，文章內容存於 {SAVE_DIR}")


if __name__ == "__main__":
    crawl_abc_lunar_new_year(2020, 2025, days_before=14, days_after=14, max_articles=500)
