import requests
from bs4 import BeautifulSoup
import csv, time
from tqdm import tqdm

def fetch_cnn_article(url: str) -> str:
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
        "section[name='bodyText']",     # 新版 CNN
        "div.article__content",         # 舊版 CNN
        "div.l-container"               # 其他長篇報導
    ]
    paragraphs = []
    for sel in selectors:
        container = soup.select_one(sel)
        if container:
            paragraphs = [p.get_text(" ", strip=True)
                          for p in container.find_all("p")]
            break

    return "\n".join(paragraphs) if paragraphs else "[No article text found]"

def main():
    # 讀取 urls.txt（每行一個 CNN 連結）
    with open("urls.txt", "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    with open("cnn_articles.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["url", "content"])
        writer.writeheader()

        for url in tqdm(urls, desc="Fetching CNN articles"):
            content = fetch_cnn_article(url)
            writer.writerow({"url": url, "content": content})
            time.sleep(1)  # 禮貌性延遲，避免被封鎖

    print("完成！文章已存到 cnn_articles.csv")

if __name__ == "__main__":
    main()
