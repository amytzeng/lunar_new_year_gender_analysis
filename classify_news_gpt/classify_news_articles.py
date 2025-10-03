from openai import OpenAI
import os
from collections import Counter, defaultdict
import time

# 初始化 OpenAI 客戶端
client = OpenAI(api_key="YOUR_API_KEY_HERE")

# 批次大小
BATCH_SIZE = 5

# 定義批次分類
def classify_batch(batch):
    """
    batch: list of (article_id, text)
    return: dict {article_id: label}
    """
    system_prompt = """你是一個新聞文章分類助手。
請依照以下規則判斷每篇文章的主題分類，僅輸出編號與對應數字，格式為「編號: 分類」。

分類規則：
1 - 農曆新年與文化慶祝：直接討論農曆新年慶祝活動、傳統、習俗、節慶相關的文章
2 - 政治與政策：政府政策、政治人物、外交關係、政治事件相關的文章
3 - 衝突與安全：戰爭、恐怖主義、軍事衝突、重大犯罪事件相關的文章
4 - 經濟與商業：經濟政策、商業活動、金融市場、企業相關的文章
5 - 其他/不相關：與上述類別無關、內容過於簡短或缺失的文章

只回傳分類結果，不要有解釋。"""

    # 拼接使用者輸入
    user_prompt = "以下是多篇文章，請依規則輸出分類：\n\n"
    for article_id, text in batch:
        snippet = text[:500]  # 避免太長
        user_prompt += f"{article_id}: {snippet}\n"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0
        )

        output = response.choices[0].message.content.strip()
        results = {}
        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                try:
                    aid, label = line.split(":", 1)
                    results[aid.strip()] = label.strip()
                except:
                    continue
        return results
    except Exception as e:
        print(f"API 錯誤: {e}")
        return {}

# 多數決分類（整批）
def classify_batch_with_majority(batch, trials=3):
    """
    batch: list of (article_id, text)
    return: dict {article_id: (final_label, [trial_results])}
    """
    all_results = []
    for _ in range(trials):
        res = classify_batch(batch)
        all_results.append(res)
        time.sleep(0.5)

    results_dict = {}
    for article_id, _ in batch:
        votes = [res.get(article_id, "error") for res in all_results]
        counter = Counter(votes)
        most_common = counter.most_common()
        if len(most_common) == 1:
            results_dict[article_id] = (most_common[0][0], votes)
        elif most_common[0][1] > most_common[1][1]:
            results_dict[article_id] = (most_common[0][0], votes)
        else:
            results_dict[article_id] = ("需要人工判斷", votes)
    return results_dict

# 讀取 data 資料夾
data_dir = "classify_news_gpt/data"
files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]

# 按照數字排序（重要：確保順序正確）
def get_file_number(filename):
    """從檔名提取數字用於排序"""
    try:
        return int(os.path.splitext(filename)[0])
    except:
        return 999999

files.sort(key=get_file_number)

classified_groups = defaultdict(list)
disputed_cases = []

# 總數
total_files = len(files)
processed = 0

print(f"找到 {total_files} 個文章檔案")
print(f"開始分類...\n")

for i in range(0, total_files, BATCH_SIZE):
    batch_files = files[i:i+BATCH_SIZE]
    batch_data = []
    for fname in batch_files:
        article_id = os.path.splitext(fname)[0]
        with open(os.path.join(data_dir, fname), "r", encoding="utf-8") as f:
            text = f.read().strip()
        batch_data.append((article_id, text))

    batch_results = classify_batch_with_majority(batch_data)

    for article_id, (label, votes) in batch_results.items():
        if label == "需要人工判斷":
            # 找到對應的文章文本
            article_text = ""
            for aid, text in batch_data:
                if aid == article_id:
                    article_text = text[:50]
                    break
            disputed_cases.append({"id": article_id, "results": votes, "text": article_text})
        else:
            classified_groups[label].append(article_id)

    processed += len(batch_data)
    if processed % 10 == 0 or processed == total_files:
        percent = processed / total_files * 100
        print(f"進度: {processed}/{total_files} ({percent:.2f}%)")

# --- 輸出分類結果 ---
with open("classified_articles.txt", "w", encoding="utf-8") as f:
    for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        ids = " ".join(classified_groups[label])
        f.write(f"{label} {ids}\n")

# --- 輸出需要人工判斷 ---
with open("disputed_articles.txt", "w", encoding="utf-8") as f:
    for case in disputed_cases:
        f.write(f"編號: {case['id']} | 判斷結果: {case['results']} | 內文前50字: {case['text']}\n")

# --- 統計比例 ---
total = sum(len(v) for v in classified_groups.values())

print("\n" + "=" * 60)
print("分類統計：")
print("=" * 60)

category_names = {
    "1": "農曆新年與文化慶祝",
    "2": "政治與政策",
    "3": "衝突與安全",
    "4": "經濟與商業",
    "5": "其他/不相關"
}

for label in sorted(classified_groups.keys(), key=lambda x: int(x) if x.isdigit() else 999):
    count = len(classified_groups[label])
    ratio = count / total * 100 if total > 0 else 0
    category_name = category_names.get(label, "未知")
    print(f"類別 {label} ({category_name}): {count} 篇 ({ratio:.2f}%)")

print(f"\n需要人工判斷: {len(disputed_cases)} 篇，已存成 disputed_articles.txt")
print("分類完成，結果存成 classified_articles.txt")
print("=" * 60)
