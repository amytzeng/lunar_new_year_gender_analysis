# -*- coding: utf-8 -*-
import os, time, csv
from datetime import datetime
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ✏️ 請填入你的帳號密碼
FB_EMAIL = "textmining714@gmail.com"
FB_PASSWORD = "txtmining7144"
TARGET_USER = "coobepowtf"    # 粉專名稱，不能是社團
KEYWORDS = ["年夜飯", "圍爐", "春節", "娘家", "婆媳"]
MAX_POSTS = 100

POST_DIR = "data/facebook/post"
COMMENT_DIR = "data/facebook/comment"
CSV_PATH = "data/facebook/facebook.csv"
os.makedirs(POST_DIR, exist_ok=True)
os.makedirs(COMMENT_DIR, exist_ok=True)
os.makedirs("data/facebook", exist_ok=True)

# 🧰 啟動 Chrome 與登入
driver = webdriver.Chrome(service=Service())
driver.get("https://www.facebook.com/login")
WebDriverWait(driver,10).until(EC.presence_of_element_located((By.NAME,"email")))
driver.find_element(By.NAME,"email").send_keys(FB_EMAIL)
driver.find_element(By.NAME,"pass").send_keys(FB_PASSWORD)
driver.find_element(By.NAME,"login").click()
time.sleep(5)

# 🔄 取得粉專頁面並滾動
driver.get(f"https://www.facebook.com/{TARGET_USER}/posts")
time.sleep(3)
post_urls = set()
last_h = driver.execute_script("return document.body.scrollHeight")

while len(post_urls) < MAX_POSTS:
    cards = driver.find_elements(By.XPATH,"//a[contains(@href,'/posts/')]")
    for a in cards:
        href = a.get_attribute("href")
        post_urls.add(href.split('?')[0])
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    new_h = driver.execute_script("return document.body.scrollHeight")
    if new_h == last_h:
        break
    last_h = new_h

urls = list(post_urls)[:MAX_POSTS]
print(f"共找到 {len(urls)} 篇貼文")

# 📝 爬每篇貼文
results = []
for i, url in enumerate(tqdm(urls, desc="貼文進度")):
    driver.get(url)
    time.sleep(3)
    try:
        content = driver.find_element(By.XPATH,"//div[@data-ad-comet-preview='message']").text
    except:
        content = ""
    # if not any(kw in content for kw in KEYWORDS):
    #     continue
    try:
        meta = driver.find_element(By.XPATH,"//a[contains(@href,'/reactions/type')]")
        like_count = int(meta.text.split()[0].replace(',',''))
    except:
        like_count = 0
    comments = []
    try:
        show_more = driver.find_elements(By.XPATH,"//div[contains(text(),'留言')]")
        for btn in show_more:
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1)
        cm_elems = driver.find_elements(By.XPATH,"//div[@aria-label='留言']")
        for c in cm_elems:
            comments.append(c.text)
    except:
        pass

    pid = url.split("/")[-1]
    with open(f"{POST_DIR}/{pid}.txt","w",encoding="utf-8") as f: f.write(content)
    for j, c in enumerate(comments):
        with open(f"{COMMENT_DIR}/post_{pid}_comment_{j}.txt","w",encoding="utf-8") as f: f.write(c)

    results.append({
        "id": pid, "platform":"facebook",
        "date":datetime.now().isoformat(),
        "title":content[:50], "like_count":like_count,
        "comment_count":len(comments),"reach":None,
        "keywords":",".join([kw for kw in KEYWORDS if kw in content])
    })

driver.quit()

# 🧾 寫入 CSV
with open(CSV_PATH,"w",newline="",encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=results[0].keys())
    w.writeheader(); w.writerows(results)

print(f"完成")
