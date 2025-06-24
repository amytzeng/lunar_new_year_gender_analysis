from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import os
import pandas as pd
from tqdm import tqdm
from datetime import datetime

DATA_DIR = "data"
POST_DIR = os.path.join(DATA_DIR, "posts")
CSV_PATH = os.path.join(DATA_DIR, "dcard_selenium.csv")
os.makedirs(POST_DIR, exist_ok=True)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 無介面模式
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_dcard_posts_selenium(driver, keyword, limit=30):
    search_url = f"https://www.dcard.tw/search/posts?query={keyword}"
    driver.get(search_url)
    time.sleep(3)

    posts = []
    seen_ids = set()
    scroll_count = 0

    while len(posts) < limit and scroll_count < 30:
        elements = driver.find_elements(By.CSS_SELECTOR, "a[data-entry-id]")

        for el in elements:
            post_url = el.get_attribute("href")
            post_id = el.get_attribute("data-entry-id")

            if post_id not in seen_ids:
                seen_ids.add(post_id)
                posts.append({"id": post_id, "url": post_url})
                if len(posts) >= limit:
                    break

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        scroll_count += 1

    return posts

def fetch_post_content(driver, post_url):
    driver.get(post_url)
    time.sleep(2)

    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
        content_div = driver.find_element(By.CSS_SELECTOR, "div[data-testid='post-content']")
        content = content_div.text.strip()
        date_elem = driver.find_element(By.CSS_SELECTOR, "span[data-testid='timestamp']")
        date_text = date_elem.text.strip()
        dt = datetime.strptime(date_text, "%Y/%m/%d %H:%M")
        return title, content, dt
    except NoSuchElementException:
        return None, None, None

def run_dcard_selenium(keywords, limit=30, start_year=2020, end_year=2025):
    driver = setup_driver()
    df_rows = []

    for kw in keywords:
        print(f"[Dcard] 關鍵字：{kw}")
        posts = fetch_dcard_posts_selenium(driver, kw, limit=limit)
        for idx, post in enumerate(tqdm(posts, desc=f"處理關鍵字：{kw}")):
            title, content, dt = fetch_post_content(driver, post['url'])

            if not title or not dt:
                continue

            if not (start_year <= dt.year <= end_year):
                continue

            full_text = f"{title}\n\n{content}"
            post_path = os.path.join(POST_DIR, f"post_{post['id']}.txt")
            with open(post_path, "w", encoding="utf-8") as f:
                f.write(full_text)

            df_rows.append({
                "post_id": post["id"],
                "發文時間": dt.strftime("%Y-%m-%d %H:%M"),
                "標題": title[:30],
                "關鍵字": kw,
                "網址": post["url"]
            })
            print(f"✅ 第 {idx + 1}/{limit} 篇完成：{title[:30]}")

    driver.quit()
    df = pd.DataFrame(df_rows)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")
    print(f"[Dcard] 已儲存 {len(df)} 筆資料到 {CSV_PATH}")

if __name__ == "__main__":
    run_dcard_selenium(["回娘家", "婆媳關係", "煮年夜飯"], limit=10)
