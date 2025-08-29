lunar_new_year_gender_analysis

# 春節期間 PTT 與 Instagram 婆媳相關文本研究

本研究透過 Python 3.12.1 與 OpenAI API (GPT-4o-mini)，蒐集並分析 PTT 與 Instagram 上與春節相關的貼文，重點關注「回娘家、年夜飯、婆媳互動、性別角色」等議題。研究目標在於探索節慶期間的性別互動、家庭角色與情緒表達。

## 研究工具

程式語言：Python 3.12.1

爬蟲：

- requests + BeautifulSoup (PTT)

- Selenium + BeautifulSoup (Instagram)

NLP 工具：

- BERT (特徵抽取)

- 支援向量機 (SVM, 初始分類器)

- OpenAI API（GPT-4o-mini，最終分類）

## 研究方法

1. PTT 資料蒐集

- 研究看板：WomenTalk、Marriage

- 篩選條件：

   - 春節前後三十天（利用 lunar_mapping.py 計算農曆新年）

   - 關鍵字：「回娘家」、「年夜飯」、「婆媳」、「春節」、「性別」、「媳婦」

- 輸出內容：

   - 文章 ID、日期、標題、內文、推文數、留言數、關鍵字

   - 存檔格式：.txt + .csv

2. Instagram 資料蒐集

- 透過 Hashtag 搜尋相關貼文

- Selenium 自動化登入與滾動載入

- 逐篇爬取貼文與留言

- 每個關鍵字最多蒐集 100 篇 貼文

3. 資料分類

- 人工標註 + SVM

   - 1 成資料人工分類，9 成交由模型分類

   - 特徵抽取：BERT [CLS] 向量 (768 維)

   - 分類器：SVM (RBF kernel, class_weight=balanced)

- AI 輔助分類

   - OpenAI GPT-4o-mini 判斷情緒類別

   - 進行三次判斷並取多數決

   - 無法判斷之案例輸出供人工處理

4. 分類規則

   1 - 正面、贊成

   2 - 中性、問問題

   3 - 無奈、抱怨

   4 - 生氣、負面

   5 - 無關（如廣告）

## 研究結果

- 總貼文數：11,227 篇

- 分類比例：

   1 - 正面、贊成：1171 篇（10.43 %）
   
   2 - 中性、問問題：3781 篇（33.68 %）
   
   3 - 無奈、抱怨：5128 篇（45.68 %）
   
   4 - 生氣、負面：947 篇（8.44 %）
   
   5 - 無關（廣告）：200 篇（1.77 %）

---

## 使用方式

下載專案

```bash
git clone https://github.com/yourname/yourrepo.git
cd yourrepo
```

安裝需求

```bash
pip install -r requirements.txt
```

執行爬蟲（範例：PTT）

```bash
python ptt_crawler.py
```

執行分類（範例：使用 GPT 分類）

```bash
python gpt_classify.py
```

## 注意事項

本研究資料僅作為學術研究用途，請勿用於商業或再散佈。

PTT 與 Instagram 之資料版權屬原作者所有。

## 授權

本專案程式碼以 MIT License 釋出。
