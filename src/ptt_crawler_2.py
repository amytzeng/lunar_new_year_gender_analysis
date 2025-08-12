# ptt_crawler.py
import os
import re
import csv
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

PTT_URL = "https://www.ptt.cc"
HEADERS = {"cookie": "over18=1"}
KEYWORDS = ["回娘家", "年夜飯", "婆媳", "春節", "性別", "女", "媳婦"]

SAVE_DIR = "data/ptt"
POST_DIR = os.path.join(SAVE_DIR, "posts")
COMMENT_DIR = os.path.join(SAVE_DIR, "comments")
CSV_PATH = os.path.join(SAVE_DIR, "ptt.csv")

os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(COMMENT_DIR, exist_ok=True)


def get_articles(board, keywords):
    count = 0
    page = get_last_page(board)
    collected = []

    while page > 0:
        print(f"解析第 {page} 頁中（目前已收集 {count} 篇）...")
        try:
            res = requests.get(f"{PTT_URL}/bbs/{board}/index{page}.html", headers=HEADERS, timeout=10)
        except Exception as e:
            print(f"[錯誤] 無法請求第 {page} 頁：{e}")
            page -= 1
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("div.r-ent")

        for art in articles:
            try:
                title_tag = art.select_one(".title a")
                if not title_tag:
                    continue
                link = title_tag['href']
                url = f"{PTT_URL}{link}"
                article_id = link.split('/')[-1].replace(".html", "")

                article_res = requests.get(url, headers=HEADERS)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                main_content = article_soup.select_one("#main-content").text
                meta = article_soup.select(".article-metaline")

                if len(meta) < 2:
                    continue

                date_str = meta[2].select_one(".article-meta-value").text
                try:
                    dt = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
                except Exception:
                    continue

                matched_keywords = [k for k in keywords if k in main_content]
                if not matched_keywords:
                    continue

                post_path = os.path.join(POST_DIR, f"{article_id}.txt")
                with open(post_path, "w", encoding="utf-8") as f:
                    f.write(f"post_id: {article_id}\n")
                    f.write(f"date: {dt.date()}\n")
                    f.write(f"title: {title_tag.text.strip()}\n")
                    f.write("content:\n")
                    f.write(main_content)

                comments = article_soup.select(".push")
                for idx, com in enumerate(comments):
                    comment_text = com.text.strip()
                    com_path = os.path.join(COMMENT_DIR, f"post_{article_id}_comment_{idx}.txt")
                    with open(com_path, "w", encoding="utf-8") as fc:
                        fc.write(comment_text)

                collected.append([
                    article_id, "ptt", dt.date(), title_tag.text.strip(),
                    main_content.count("推"), len(comments), "N/A", ','.join(matched_keywords)
                ])
                count += 1

            except Exception:
                continue

        time.sleep(1)  # 控制爬蟲速度，避免被封鎖
        page -= 1

    with open(CSV_PATH, "w", newline='', encoding="utf-8") as cf:
        writer = csv.writer(cf)
        writer.writerow(["id", "platform", "date", "title", "like_count", "comment_count", "reach", "keywords"])
        writer.writerows(collected)


def run_ptt(keywords, board="marriage"):
    get_articles(board, keywords)


def get_last_page(board):
    try:
        res = requests.get(f"{PTT_URL}/bbs/{board}/index.html", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        btn = soup.select(".btn.wide")
        href = btn[1]['href'] if len(btn) > 1 else btn[0]['href']
        return int(href.split("index")[-1].split(".html")[0]) + 1
    except Exception as e:
        print(f"[錯誤] 無法取得 PTT 頁面：{e}")
        return 0


if __name__ == "__main__":
    get_articles("marriage", ["回娘家", "年夜飯", "婆媳", "春節", "性別", "女", "媳婦"])