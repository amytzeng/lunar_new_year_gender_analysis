import os

# 讀取分類檔案
classified_file = "classified_articles.txt"
counts = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

with open(classified_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split()
        if not parts:
            continue
        label = parts[0]
        ids = parts[1:]
        if label in counts:
            counts[label] += len(ids)

total = sum(counts.values())

# 分類對應說明
label_map = {
    "1": "農曆新年與文化慶祝",
    "2": "政治與政策",
    "3": "衝突與安全",
    "4": "經濟與商業",
    "5": "其他/不相關"
}

# 輸出結果
with open("result.txt", "w", encoding="utf-8") as f:
    f.write("新聞文章分類統計\n")
    f.write("=" * 60 + "\n\n")
    for label in ["1", "2", "3", "4", "5"]:
        count = counts[label]
        ratio = (count / total * 100) if total > 0 else 0
        f.write(f"{label} - {label_map[label]}：{count} 篇、{ratio:.2f}%\n")
    f.write("\n" + "=" * 60 + "\n")
    f.write(f"總文章數：{total}\n")

# 同時輸出到終端機
print("=" * 60)
print("新聞文章分類統計")
print("=" * 60)
for label in ["1", "2", "3", "4", "5"]:
    count = counts[label]
    ratio = (count / total * 100) if total > 0 else 0
    print(f"{label} - {label_map[label]}：{count} 篇、{ratio:.2f}%")
print("=" * 60)
print(f"總文章數：{total}")
print()
print("✅ 統計完成，結果已存成 result.txt")

