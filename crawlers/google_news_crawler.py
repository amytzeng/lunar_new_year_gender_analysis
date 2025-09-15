import requests, time, csv
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm

def google_news_cnn(keyword, start_date, end_date, max_articles=100):
    """
    透過 Google News RSS 找 CNN 的文章連結
    """
    base = "https://news.google.com/rss/search"
    query = f"{keyword}+site:cnn.com"
    # RFC3339 日期格式 yyyy-mm-dd
    url = f"{base}?q={query}+after:{start_date}+before:{end_date}&hl=en-US&gl=US&ceid=US:en"

    r = requests.get(url, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.content, "xml")
    items = soup.find_all("item")
    results = []
    for item in items[:max_articles]:
        link = item.link.text
        title = item.title.text
        pub_date = item.pubDate.text
        results.append({"title": title, "link": link, "pub_date": pub_date})
    return results


def fetch_cnn_article(url):
    """
    下載 CNN 單篇文章並萃取正文
    """
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"[Error fetching page: {e}]"

    soup = BeautifulSoup(r.text, "lxml")

    # 嘗試不同版型的容器
    selectors = [
        "section[name='bodyText']",        # 新版 CNN
        "div.article__content",            # 舊版
        "div.l-container"                  # 其他長篇報導
    ]
    paragraphs = []
    for sel in selectors:
        container = soup.select_one(sel)
        if container:
            paragraphs = [p.get_text(" ", strip=True)
                          for p in container.find_all("p")]
            break

    return "\n".join(paragraphs) if paragraphs else "[No article text found]"


def crawl_cnn_full(keyword, start_date, end_date, outfile="cnn_articles.csv"):
    """
    先抓 URL 再抓全文並存成 CSV
    """
    articles = google_news_cnn(keyword, start_date, end_date, max_articles=200)
    print(f"找到 {len(articles)} 篇連結，開始抓取全文…")

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "pub_date", "content"])
        writer.writeheader()

        for art in tqdm(articles):
            text = fetch_cnn_article(art["link"])
            writer.writerow({
                "title": art["title"],
                "link": art["link"],
                "pub_date": art["pub_date"],
                "content": text
            })
            time.sleep(1)  # 禮貌性延遲

    print(f"完成！文章已存到 {outfile}")


if __name__ == "__main__":
    # 範例：抓 2020 農曆新年前後
    crawl_cnn_full(
        keyword="Lunar New Year",
        start_date="2020-01-11",
        end_date="2020-02-08",
        outfile="cnn_lunar_2020.csv"
    )
