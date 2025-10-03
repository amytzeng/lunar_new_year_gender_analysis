import requests, time, csv
from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm

def google_news_abc(keyword, start_date, end_date, max_articles=100):
    """
    透過 Google News RSS 找 ABC News 的文章連結
    """
    base = "https://news.google.com/rss/search"
    query = f"{keyword}+site:abcnews.go.com"
    # RFC3339 日期格式 yyyy-mm-dd
    url = f"{base}?q={query}+after:{start_date}+before:{end_date}&hl=en-US&gl=US&ceid=US:en"

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.content, "xml")
        items = soup.find_all("item")
        results = []
        for item in items[:max_articles]:
            link = item.link.text
            title = item.title.text
            pub_date = item.pubDate.text
            
            # 嘗試從Google News連結中提取實際的ABC News URL
            # Google News連結通常包含編碼的實際URL
            try:
                # 解碼Google News連結
                decoded_link = extract_actual_url_from_google_news(link)
                results.append({"title": title, "link": decoded_link, "pub_date": pub_date})
            except:
                # 如果解碼失敗，使用原始連結
                results.append({"title": title, "link": link, "pub_date": pub_date})
        return results
    except Exception as e:
        print(f"Error fetching Google News RSS: {e}")
        return []


def extract_actual_url_from_google_news(google_news_url):
    """
    從Google News連結中提取實際的新聞網站URL
    """
    try:
        # 先獲取重定向
        r = requests.get(google_news_url, timeout=15, allow_redirects=True)
        final_url = r.url
        
        # 如果最終URL仍然是Google News，嘗試其他方法
        if "news.google.com" in final_url:
            # 嘗試從URL參數中提取
            if "url=" in final_url:
                import urllib.parse
                parsed = urllib.parse.parse_qs(urllib.parse.urlparse(final_url).query)
                if 'url' in parsed:
                    return parsed['url'][0]
        
        return final_url
    except:
        return google_news_url


def fetch_abc_article(url):
    """
    下載 ABC News 單篇文章並萃取正文
    """
    try:
        # 處理Google News重定向連結
        if "news.google.com" in url:
            # 先獲取重定向後的實際URL
            r = requests.get(url, timeout=15, allow_redirects=True)
            actual_url = r.url
        else:
            actual_url = url
            
        r = requests.get(actual_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"[Error fetching page: {e}]"

    soup = BeautifulSoup(r.text, "lxml")

    # ABC News 文章內容的選擇器
    selectors = [
        "div[data-module='ArticleBody']",           # 新版 ABC News
        "div.ArticleBody",                          # 舊版 ABC News
        "div.article-body",                         # 其他版本
        "div[data-testid='ArticleBody']",           # 測試版本
        "section[data-module='ArticleBody']",       # 區塊版本
        "div.article-content",                      # 通用內容區塊
        "div.content",                              # 通用內容
        "div[class*='article']",                    # 包含article的class
        "div[class*='story']",                      # 包含story的class
        "div[class*='body']"                        # 包含body的class
    ]
    
    paragraphs = []
    for sel in selectors:
        container = soup.select_one(sel)
        if container:
            # 尋找段落標籤
            paragraph_tags = container.find_all(["p", "div"], recursive=True)
            paragraphs = []
            for tag in paragraph_tags:
                text = tag.get_text(" ", strip=True)
                if text and len(text) > 20:  # 過濾太短的文字
                    paragraphs.append(text)
            if paragraphs:
                break

    # 如果上述選擇器都沒找到，嘗試更通用的方法
    if not paragraphs:
        # 尋找所有段落標籤
        all_paragraphs = soup.find_all("p")
        paragraphs = [p.get_text(" ", strip=True) for p in all_paragraphs 
                     if p.get_text(" ", strip=True) and len(p.get_text(" ", strip=True)) > 20]

    return "\n".join(paragraphs) if paragraphs else "[No article text found]"


def crawl_abc_full(keyword, start_date, end_date, outfile="abc_articles.csv"):
    """
    先抓 URL 再抓全文並存成 CSV
    """
    print(f"Searching for ABC News articles with keyword: '{keyword}'")
    print(f"Date range: {start_date} to {end_date}")
    
    articles = google_news_abc(keyword, start_date, end_date, max_articles=200)
    print(f"找到 {len(articles)} 篇連結，開始抓取全文…")

    if not articles:
        print("No articles found. Please check your search parameters.")
        return

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "pub_date", "content"])
        writer.writeheader()

        for art in tqdm(articles, desc="Fetching ABC News articles"):
            text = fetch_abc_article(art["link"])
            writer.writerow({
                "title": art["title"],
                "link": art["link"],
                "pub_date": art["pub_date"],
                "content": text
            })
            time.sleep(1)  # 禮貌性延遲

    print(f"完成！文章已存到 {outfile}")


def fetch_abc_from_urls(urls_file="abc_urls.txt", outfile="abc_articles.csv"):
    """
    從 urls.txt 檔案讀取 ABC News 連結並抓取全文
    """
    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"URLs file '{urls_file}' not found.")
        return

    print(f"Found {len(urls)} URLs to process")

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "content"])
        writer.writeheader()

        for url in tqdm(urls, desc="Fetching ABC News articles"):
            content = fetch_abc_article(url)
            writer.writerow({"url": url, "content": content})
            time.sleep(1)  # 禮貌性延遲

    print(f"完成！文章已存到 {outfile}")


def search_abc_direct(keyword, max_articles=50):
    """
    直接從ABC News網站搜索文章
    """
    search_url = f"https://abcnews.go.com/search?searchtext={keyword}"
    
    try:
        r = requests.get(search_url, timeout=15)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        
        # 尋找文章連結
        article_links = []
        
        # 嘗試不同的選擇器來找到文章連結
        selectors = [
            "a[href*='/story?id=']",
            "a[href*='/US/']",
            "a[href*='/International/']",
            "a[href*='/Politics/']"
        ]
        
        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and 'abcnews.go.com' in href:
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:
                        article_links.append({
                            "title": title,
                            "link": href if href.startswith('http') else f"https://abcnews.go.com{href}",
                            "pub_date": "Unknown"
                        })
                        if len(article_links) >= max_articles:
                            break
            if article_links:
                break
        
        return article_links[:max_articles]
    except Exception as e:
        print(f"Error searching ABC News directly: {e}")
        return []


def crawl_abc_from_urls(urls_file="abc_urls.txt", outfile="abc_articles.csv"):
    """
    從 urls.txt 檔案讀取 ABC News 連結並抓取全文
    這是主要的爬取方法，類似於CNN爬蟲
    """
    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"URLs file '{urls_file}' not found.")
        print("Please create a file with ABC News URLs, one per line.")
        return

    print(f"Found {len(urls)} URLs to process")

    with open(outfile, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "content"])
        writer.writeheader()

        for url in tqdm(urls, desc="Fetching ABC News articles"):
            content = fetch_abc_article(url)
            writer.writerow({"url": url, "content": content})
            time.sleep(1)  # 禮貌性延遲

    print(f"完成！文章已存到 {outfile}")


def crawl_abc_to_txt_files(urls_file="abc_urls.txt", output_dir="abc_posts"):
    """
    從 urls.txt 檔案讀取 ABC News 連結並抓取全文，保存為單篇.txt檔案
    格式類似於CNN資料
    """
    import os
    from datetime import datetime
    
    try:
        with open(urls_file, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"URLs file '{urls_file}' not found.")
        print("Please create a file with ABC News URLs, one per line.")
        return

    # 創建輸出目錄
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Found {len(urls)} URLs to process")
    print(f"Output directory: {output_dir}")

    for i, url in enumerate(tqdm(urls, desc="Fetching ABC News articles")):
        content = fetch_abc_article(url)
        
        # 生成檔案名稱
        filename = f"abc_{i+1:04d}.txt"
        filepath = os.path.join(output_dir, filename)
        
        # 提取文章標題（從URL或內容中）
        title = extract_title_from_url(url)
        
        # 生成文章ID
        article_id = f"abc_{i+1:04d}"
        
        # 獲取當前日期
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 寫入.txt檔案
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"article_id: {article_id}\n")
            f.write(f"url: {url}\n")
            f.write(f"title: {title}\n")
            f.write(f"date: {current_date}\n")
            f.write(f"author: \n")
            f.write(f"matched_keywords: lunar new year\n")
            f.write(f"content:\n")
            f.write(content)
        
        time.sleep(1)  # 禮貌性延遲

    print(f"完成！文章已存到 {output_dir} 目錄")


def extract_title_from_url(url):
    """
    從URL中提取文章標題
    """
    try:
        # 嘗試從URL中提取標題
        if "/story?id=" in url:
            # 對於ABC News的story格式
            return "ABC News Article"
        elif "/US/" in url:
            return "ABC News US Article"
        elif "/International/" in url:
            return "ABC News International Article"
        else:
            return "ABC News Article"
    except:
        return "ABC News Article"


def create_sample_urls_file():
    """
    創建一個示例URLs檔案，包含一些ABC News文章連結
    """
    sample_urls = [
        "https://abcnews.go.com/US/lunar-new-year-celebrations-kick-off-worldwide/story?id=106123456",
        "https://abcnews.go.com/International/china-celebrates-lunar-new-year-amid-pandemic/story?id=106123457",
        "https://abcnews.go.com/US/communities-celebrate-lunar-new-year-traditional-festivities/story?id=106123458"
    ]
    
    with open("abc_urls.txt", "w", encoding="utf-8") as f:
        for url in sample_urls:
            f.write(url + "\n")
    
    print("Created sample abc_urls.txt file")
    print("Please replace the URLs with actual ABC News article URLs you want to crawl")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "create_sample":
            # 創建示例URLs檔案
            create_sample_urls_file()
            
        elif command == "crawl_urls":
            # 從URLs檔案爬取文章
            urls_file = sys.argv[2] if len(sys.argv) > 2 else "abc_urls.txt"
            outfile = sys.argv[3] if len(sys.argv) > 3 else "abc_articles.csv"
            crawl_abc_from_urls(urls_file, outfile)
            
        elif command == "crawl_txt":
            # 從URLs檔案爬取文章並保存為.txt檔案
            urls_file = sys.argv[2] if len(sys.argv) > 2 else "abc_urls.txt"
            output_dir = sys.argv[3] if len(sys.argv) > 3 else "abc_posts"
            crawl_abc_to_txt_files(urls_file, output_dir)
            
        elif command == "search":
            # 使用Google News搜索
            keyword = sys.argv[2] if len(sys.argv) > 2 else "Lunar New Year"
            start_date = sys.argv[3] if len(sys.argv) > 3 else "2024-01-01"
            end_date = sys.argv[4] if len(sys.argv) > 4 else "2024-02-29"
            outfile = sys.argv[5] if len(sys.argv) > 5 else "abc_articles.csv"
            crawl_abc_full(keyword, start_date, end_date, outfile)
            
        else:
            print("Unknown command. Available commands:")
            print("  create_sample - Create sample URLs file")
            print("  crawl_urls [urls_file] [output_file] - Crawl from URLs file (CSV format)")
            print("  crawl_txt [urls_file] [output_dir] - Crawl from URLs file (TXT format)")
            print("  search [keyword] [start_date] [end_date] [output_file] - Search via Google News")
    else:
        # 預設行為：創建示例檔案並顯示使用說明
        print("ABC News Crawler")
        print("================")
        print()
        print("Usage:")
        print("  python abc_news_crawler.py create_sample")
        print("  python abc_news_crawler.py crawl_urls [urls_file] [output_file]")
        print("  python abc_news_crawler.py crawl_txt [urls_file] [output_dir]")
        print("  python abc_news_crawler.py search [keyword] [start_date] [end_date] [output_file]")
        print()
        print("Examples:")
        print("  python abc_news_crawler.py create_sample")
        print("  python abc_news_crawler.py crawl_urls abc_urls.txt abc_articles.csv")
        print("  python abc_news_crawler.py crawl_txt abc_urls.txt abc_posts")
        print("  python abc_news_crawler.py search 'Lunar New Year' 2024-01-01 2024-02-29 abc_lunar_2024.csv")
        print()
        
        # 創建示例檔案
        create_sample_urls_file()
