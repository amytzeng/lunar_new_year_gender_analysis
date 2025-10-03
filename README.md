lunar_new_year_gender_analysis

# 春節期間多平台文本性別分析研究

本研究透過 Python 3.12.1 與 OpenAI API (GPT-4o-mini)，蒐集並分析 PTT、Instagram、ABC News 與 CNN 上與春節相關的文本，重點關注「回娘家、年夜飯、婆媳互動、性別角色」等議題。研究目標在於探索節慶期間的性別互動、家庭角色與情緒表達，並進行跨平臺比較分析。

## 📑 目錄

- [研究工具](#研究工具)
- [研究方法](#研究方法)
- [研究結果](#研究結果)
- [使用方式](#使用方式)
- [資料結構](#資料結構)
- [注意事項](#注意事項)
- [授權](#授權)

## 研究工具

程式語言：Python 3.12.1

爬蟲：

- requests + BeautifulSoup (PTT, ABC News)

- Selenium + BeautifulSoup (Instagram)

- Google News RSS (ABC News 文章搜索)

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

- 逐篇爬取貼文

3. ABC News 資料蒐集

- 透過 Google News RSS 搜索農曆新年相關文章

- 直接從 ABC News 網站爬取文章內容

- 輸出格式：.txt 檔案，包含網址與文章內容

- 已成功爬取 15 篇文章

4. CNN 資料蒐集

- 透過 Google News RSS 搜索 CNN 網站上的農曆新年相關文章，並將網址爬下後，手動爬下文章內容

- 包含多種 CNN 報導（如新聞、旅遊、照片等）中的內文

- 輸出格式：.txt 檔案


### 資料分類

#### 社群媒體（PTT、Instagram）文章情緒分類（classify_gpt）

- 人工標註 + SVM

   - 1 成資料人工分類，9 成交由模型分類

   - 特徵抽取：BERT [CLS] 向量 (768 維)

   - 分類器：SVM (RBF kernel, class_weight=balanced)

- AI 輔助分類

   - OpenAI GPT-4o-mini 判斷情緒類別

   - 進行三次判斷並取多數決

   - 無法判斷之案例輸出供人工處理

- 分類規則：

   1 - 正面、贊成

   2 - 中性、問問題

   3 - 無奈、抱怨

   4 - 生氣、負面

   5 - 無關（如廣告）

#### 新聞文章主題分類（classify_news_gpt）

- AI 主題分類

   - OpenAI GPT-4o-mini 判斷新聞主題類別

   - 批次處理（每批 5 篇）+ 多數決機制（3 次判斷）

   - 自動整理分類結果到對應資料夾

- 分類規則：

   1 - 農曆新年與文化慶祝

   2 - 政治與政策

   3 - 衝突與安全

   4 - 經濟與商業

   5 - 其他/不相關

## 研究結果

### 社群媒體文章情緒分析結果

- 總貼文數：11,227 篇

- 分類比例：

   1 - 正面、贊成：1171 篇（10.43 %）
   
   2 - 中性、問問題：3781 篇（33.68 %）
   
   3 - 無奈、抱怨：5128 篇（45.68 %）
   
   4 - 生氣、負面：947 篇（8.44 %）
   
   5 - 無關（廣告）：200 篇（1.77%）

### 新聞文章主題分析結果

- 總文章數：94 篇（ABC News + CNN）

- 分類比例：

   1 - 農曆新年與文化慶祝：73 篇（77.66%）
   
   2 - 政治與政策：4 篇（4.26%）
   
   3 - 衝突與安全：7 篇（7.45%）
   
   4 - 經濟與商業：4 篇（4.26%）
   
   5 - 其他/不相關：6 篇（6.38%）

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

執行爬蟲

```bash
# PTT 爬蟲
python crawlers/ptt_crawler.py

# Instagram 爬蟲
python crawlers/instagram_crawler.py

# ABC News 爬蟲
python crawlers/abc_news_crawler.py crawl_txt urls.txt abc_posts
```

執行分類

```bash
# PTT 文章情緒分類
cd classify_gpt
python gpt_classify.py

# 新聞文章主題分類
cd classify_news_gpt
python classify_news_articles.py

# 整理分類結果
python sort.py

# 計算分類比例
python prop.py
```

## 資料結構

```
lunar_new_year_gender_analysis/
├── org_data/                    # 原始資料
│   ├── ptt/                    # PTT 文章
│   │   ├── posts/              # 文章內容
│   │   └── comments/           # 留言內容
│   ├── instagram/              # Instagram 貼文
│   │   └── post/               # 貼文內容
│   ├── abc_posts/              # ABC News 文章
│   └── cnn/                    # CNN 文章
├── crawlers/                    # 爬蟲程式
│   ├── ptt_crawler.py          # PTT 爬蟲
│   ├── instagram_crawler.py    # Instagram 爬蟲
│   ├── abc_news_crawler.py     # ABC News 爬蟲
│   └── lunar_mapping.py        # 農曆日期對應
├── classify_gpt/               # PTT 文章情緒分類
│   ├── data/                   # 待分類資料
│   ├── gpt_classify.py         # GPT 分類程式
│   ├── gpt_classify_retry.py   # 重試分類
│   ├── sort.py                 # 整理分類檔案
│   ├── prop.py                 # 計算分類比例
│   ├── classified_posts.txt    # 分類結果
│   └── disputed_cases.txt      # 爭議案例
├── classify_news_gpt/          # 新聞文章主題分類
│   ├── data/                   # 待分類資料
│   │   ├── 1/                  # 類別1資料夾
│   │   ├── 2/                  # 類別2資料夾
│   │   ├── 3/                  # 類別3資料夾
│   │   ├── 4/                  # 類別4資料夾
│   │   └── 5/                  # 類別5資料夾
│   ├── classify_news_articles.py      # 主分類程式
│   ├── classify_news_articles_retry.py # 重試分類
│   ├── sort.py                        # 整理分類檔案
│   ├── prop.py                        # 計算分類比例
│   ├── classified_articles.txt        # 分類結果
│   ├── disputed_articles.txt          # 爭議案例
│   ├── result.txt                     # 統計結果
│   └── README.md                      # 使用說明
├── classify_model/             # BERT+SVM 分類模型
│   ├── training/               # 訓練資料
│   ├── testing/                # 測試資料
│   └── bert+svm.py             # 模型程式
├── requirements.txt            # Python 套件需求
└── README.md                   # 專案說明
```

## 注意事項

### 使用說明

1. **OpenAI API Key 設定**
   - 使用分類功能前，需在程式中設定你的 OpenAI API Key：將 `YOUR_API_KEY_HERE` 替換為你的實際 API Key

2. **資料使用限制**
   - 本研究資料僅作為學術研究用途，請勿用於商業或再散佈
   - PTT、Instagram、ABC News 與 CNN 之資料版權屬原作者所有

3. PTT、Instagram 與 ABC News 之資料版權屬原作者所有。

## 授權

本專案程式碼以 MIT License 釋出。
