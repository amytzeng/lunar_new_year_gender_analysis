# 2026 年農曆春節國際媒體報導爬蟲與分類系統

本系統用於爬取多個國際新聞媒體在 2026 年農曆春節前後（2026/2/1 至 2/28）的相關報導，涵蓋農曆新年、年夜飯、春節習俗、回娘家等主題。系統包含完整的資料處理流程：從 Google News RSS 搜尋文章連結、解碼 Google News URL、爬取文章內容，到使用 GPT 進行文章篩選和主題分類。


## 爬取的目標媒體

1. **CNN** (cnn.com)
2. **ABC News** (abcnews.go.com)
3. **BBC News** (bbc.com)
4. **Reuters** (reuters.com)
5. **Associated Press** (apnews.com)
6. **The Guardian** (theguardian.com)
7. **Washington Post** (washingtonpost.com)
8. **New York Times** (nytimes.com)
9. **NBC News** (nbcnews.com)
10. **CBS News** (cbsnews.com)
11. **Fox News** (foxnews.com)

## 搜尋關鍵字

系統預設搜尋以下農曆春節相關關鍵字：

- Lunar New Year
- Chinese New Year
- Spring Festival
- reunion dinner
- red envelope / hongbao
- temple fair
- dragon dance
- lion dance
- returning to parents' home
- family reunion
- Chinese zodiac
- Year of the Horse（2026 年為馬年）
- lunar calendar
- Chinese traditions

### 搜尋策略

系統採用以下搜尋策略：
1. **分別搜尋**：對每個關鍵字分別在 Google News RSS 中搜尋
2. **合併結果**：將所有關鍵字的搜尋結果合併
3. **自動去重**：基於 URL 自動過濾重複的文章
4. **日期篩選**：只保留指定日期範圍內的文章

## 安裝與設定

### 1. 確認環境

確保已安裝 Python 3.7 或更高版本：

```bash
python3 --version
```

### 2. 安裝依賴套件

專案所需的套件已列在 `requirements.txt` 中，執行以下命令安裝：

```bash
pip install -r requirements.txt
```

主要依賴套件包括：
- `requests` - HTTP 請求庫
- `beautifulsoup4` - HTML 解析庫
- `lxml` - XML/HTML 解析器
- `tqdm` - 進度條顯示
- `googlenewsdecoder` - Google News URL 解碼套件（可選，用於快速解碼）
- `openai` - OpenAI API 客戶端（用於 GPT 分類）

### 3. 檔案結構

```
lunar_new_year_gender_analysis/
├── crawlers/                           # 爬蟲程式
│   ├── multi_news_crawler.py          # 主爬蟲程式（爬取 URL）
│   ├── decode_google_news_urls.py     # Google News URL 解碼程式
│   ├── retry_failed_urls.py           # 重試失敗的 URL 解碼
│   ├── fetch_decoded_articles.py      # 從解碼 URL 爬取文章
│   ├── news_media_config.py           # 媒體配置檔案
│   └── utils/                         # 工具模組
│       ├── __init__.py
│       ├── article_extractor.py       # 文章提取工具
│       └── google_news_decoder.py     # Google News URL 解碼工具
├── classify_lunar_2026_articles/      # 2026 年文章分類程式
│   ├── filter_relevant_articles.py    # 篩選相關文章
│   ├── classify_lunar_2026_articles.py # 分類相關文章
│   ├── relevant_articles.txt          # 相關文章 ID 列表（執行後生成）
│   ├── filter_statistics.txt          # 篩選統計結果（執行後生成）
│   ├── classified_articles.txt        # 分類結果（執行後生成）
│   ├── classification_statistics.txt  # 分類統計結果（執行後生成）
│   └── disputed_articles.txt         # 爭議文章（執行後生成）
├── lunar_2026_data/                   # 2026 年春節報導資料
│   ├── cnn.txt                        # 各媒體的 Google News URL 列表
│   ├── bbc.txt
│   ├── cnn_decoded.txt                # 解碼後的 URL 列表
│   ├── bbc_decoded.txt
│   └── ...
├── lunar_2026_articles/               # 爬取的文章內容
│   ├── cnn/                           # 按媒體分類的文章
│   │   ├── 1.txt
│   │   ├── 2.txt
│   │   └── ...
│   ├── bbc/
│   └── ...
├── org_data/                          # 舊資料（保持不變）
│   ├── cnn/
│   ├── abc_posts/
│   └── ...
├── classify_news_gpt/                 # 舊版新聞文章主題分類
│   ├── data/                          # 待分類資料
│   ├── classify_news_articles.py
│   └── ...
└── requirements.txt                   # Python 套件需求
```

## 流程

```
步驟 1：Google News RSS 搜尋（多關鍵字）
    ↓
取得 Google News URL 列表
    ↓
儲存到各媒體的 .txt 檔案
    ↓
步驟 2：解碼 Google News URL
    ↓
使用 googlenewsdecoder 或 requests 解碼
    ↓
儲存解碼後的 URL 到 *_decoded.txt 檔案
    ↓
（可選）重試失敗的 URL
    ↓
步驟 3：爬取文章內容
    ↓
根據域名識別媒體來源
    ↓
使用對應的 CSS 選擇器提取內容
    ↓
按媒體分類儲存文章
    ↓
步驟 4：篩選相關文章
    ↓
使用 GPT 判斷是否與農曆春節相關
    ↓
輸出相關文章 ID 列表
    ↓
步驟 5：分類相關文章
    ↓
使用 GPT 進行主題分類（多數決機制）
    ↓
輸出分類結果和統計資訊
```

系統採用多步驟處理流程，從搜尋文章連結到最終分類。以下是各步驟的詳細流程：

### 步驟 1：搜尋並儲存文章 URL

使用 Google News RSS 搜尋相關文章，並將 Google News URL 儲存到檔案：

```bash
python crawlers/multi_news_crawler.py
```

各媒體的 Google News URL 儲存在 `lunar_2026_data/` 目錄中：

```
lunar_2026_data/
├── cnn.txt          # CNN 的 Google News URL 列表
├── bbc.txt          # BBC 的 Google News URL 列表
├── reuters.txt      # Reuters 的 Google News URL 列表
└── ...
```

每個檔案每行一個 Google News URL（格式：`https://news.google.com/rss/articles/...`）。

### 步驟 2：解碼 Google News URL

將 Google News 編碼 URL 解碼為實際的文章 URL：

```bash
python crawlers/decode_google_news_urls.py
```

這會生成解碼後的 URL 檔案（如 `cnn_decoded.txt`, `bbc_decoded.txt` 等），儲存在 `lunar_2026_data/` 目錄中：

```
lunar_2026_data/
├── cnn_decoded.txt      # CNN 解碼後的 URL 列表
├── bbc_decoded.txt      # BBC 解碼後的 URL 列表
├── reuters_decoded.txt  # Reuters 解碼後的 URL 列表
└── ...
```

每個檔案每行一個實際的文章 URL。如果解碼失敗，會保留原始 Google News URL 並加上註解。

**重試失敗的 URL**

如果部分 URL 解碼失敗，可以使用增強方法重試：

```bash
python crawlers/retry_failed_urls.py
```

### 步驟 3：爬取文章內容

從解碼後的 URL 爬取實際的文章內容：

```bash
python crawlers/fetch_decoded_articles.py
```

爬取的文章內容儲存在 `lunar_2026_articles/` 目錄中，按媒體分類：

```
lunar_2026_articles/
├── cnn/
│   ├── 1.txt
│   ├── 2.txt
│   └── ...
├── bbc/
│   ├── 1.txt
│   ├── 2.txt
│   └── ...
└── ...
```

每個文章檔案包含以下資訊：

```
article_id: {media_code}_{序號}
url: {文章URL}
title: {文章標題}
date: {發布日期}
author: 
matched_keywords: Lunar New Year
content:
{文章正文內容}
```

範例：

```
article_id: cnn_1
url: https://www.cnn.com/2026/02/15/lunar-new-year-guide/index.html
title: Lunar New Year 2026: A Complete Guide
date: 2026-03-06
author: 
matched_keywords: Lunar New Year
content:
The Lunar New Year, also known as Chinese New Year or Spring Festival...
```

### 步驟 4：篩選相關文章

使用 GPT 判斷文章是否與農曆春節相關：

```bash
python classify_lunar_2026_articles/filter_relevant_articles.py
```

篩選結果儲存在 `classify_lunar_2026_articles/` 目錄中：
- `relevant_articles.txt`：相關文章的 ID 列表（每行一個 article_id）
- `filter_statistics.txt`：篩選統計結果，包含總文章數、相關文章數、比例、處理時間等

**注意**：執行前請在程式碼中設定 OpenAI API Key。

### 步驟 5：分類相關文章

對篩選出的相關文章進行主題分類：

```bash
python classify_lunar_2026_articles/classify_lunar_2026_articles.py
```

分類結果儲存在 `classify_lunar_2026_articles/` 目錄中：

- **`classified_articles.txt`**：分類結果，格式為 `類別編號 article_id1 article_id2 ...`
- **`classification_statistics.txt`**：分類統計結果，包含各類別的文章數量和比例
- **`disputed_articles.txt`**：需要人工判斷的文章列表

**注意**：執行前請在程式碼中設定 OpenAI API Key。

### 查看所有選項

每個腳本都支援 `--help` 參數查看詳細選項：

```bash
python crawlers/multi_news_crawler.py --help
python crawlers/decode_google_news_urls.py --help
python crawlers/fetch_decoded_articles.py --help
```

## 文章篩選與分類機制

系統使用 GPT-4o-mini 進行兩階段處理：先篩選與農曆春節相關的文章，再對相關文章進行主題分類。

### 篩選標準

篩選程式會判斷文章是否與農曆春節相關，判斷標準包括：

- 過年習俗（如：貼春聯、放鞭炮、發紅包）
- 年夜飯、團圓飯
- 回娘家、探親
- 農曆新年慶祝活動
- 傳統節慶習俗
- 春節相關文化活動

### 分類類別

相關文章將被分類為以下 5 個類別：

1. **農曆新年與文化慶祝** - 直接討論農曆新年慶祝活動、傳統、習俗、節慶相關的文章
2. **政治與政策** - 政府政策、政治人物、外交關係、政治事件相關的文章
3. **衝突與安全** - 戰爭、恐怖主義、軍事衝突、重大犯罪事件相關的文章
4. **經濟與商業** - 經濟政策、商業活動、金融市場、企業相關的文章
5. **其他/不相關** - 與上述類別無關、內容過於簡短或缺失的文章

### 分類機制

- **多數決機制**：每個批次進行 3 次分類，使用多數決決定最終分類
- **爭議處理**：如果 3 次分類結果不一致，標記為需要人工判斷
- **批次處理**：預設每批次處理 5 篇文章，可調整 `BATCH_SIZE` 參數

### 請求頻率

- 系統預設在每次請求之間延遲 1 秒，避免被封鎖
- 如需調整延遲時間，使用 `--delay` 參數

### 錯誤處理

系統實作完善的錯誤處理機制：

- **重試機制**：每個請求最多重試 3 次，提高成功率
- **錯誤記錄**：記錄失敗的文章 URL 和錯誤原因
- **繼續處理**：如果某篇文章無法爬取，系統會記錄錯誤並繼續處理下一篇文章
- **統計資訊**：最終會顯示統計資訊，包括成功和失敗的文章數量
- **優雅降級**：如果主要 CSS 選擇器失效，系統會自動嘗試備選選擇器

### 資料使用

- 本系統爬取的資料僅供學術研究使用
- 所有文章版權屬於原作者和新聞媒體
- 請遵守各新聞網站的使用條款和 robots.txt 規範

## 技術架構

### 核心設計理念

系統採用模組化設計，將媒體配置與爬蟲邏輯分離。每個媒體的網站結構和文章內容選擇器都定義在配置檔案中，方便後續擴展或調整。爬蟲流程分為兩個階段：第一階段透過 Google News RSS 搜尋符合條件的文章連結，第二階段逐一訪問這些連結並提取文章內容。

### 核心模組

1. **`multi_news_crawler.py`** - 主爬蟲程式（步驟 1）
   - Google News RSS 搜尋模組：使用 Google News RSS API 搜尋指定媒體的文章，支援日期範圍篩選和多個關鍵字組合搜尋
   - 文章去重模組：基於 URL 自動過濾重複文章
   - URL 儲存模組：將 Google News URL 儲存到檔案

2. **`decode_google_news_urls.py`** - URL 解碼程式（步驟 2）
   - 批次解碼模組：讀取所有媒體的 Google News URL 檔案
   - 雙重解碼機制：優先使用 `googlenewsdecoder` 套件（快速、無需網路請求），失敗時使用 `requests` 追蹤重定向
   - 結果儲存模組：將解碼後的 URL 儲存到新檔案

3. **`retry_failed_urls.py`** - 重試解碼程式（步驟 2 可選）
   - 失敗 URL 識別：從解碼結果中找出失敗的 URL
   - 增強解碼方法：使用更強的 HTML 解析方法重新嘗試解碼
   - 自動更新：將成功解碼的 URL 更新到原檔案

4. **`fetch_decoded_articles.py`** - 文章爬取程式（步驟 3）
   - 媒體識別模組：根據 URL 域名自動識別新聞媒體來源
   - 選擇器匹配模組：使用對應媒體的 CSS 選擇器配置
   - 文章提取模組：使用 `article_extractor.py` 提取文章內容
   - 檔案儲存模組：按媒體分類儲存文章

5. **`filter_relevant_articles.py`** - 文章篩選程式（步驟 4）
   - GPT 判斷模組：使用 GPT-4o-mini 判斷文章是否與農曆春節相關
   - 批次處理模組：批次處理文章以提高效率
   - 統計輸出模組：輸出篩選統計結果

6. **`classify_lunar_2026_articles.py`** - 文章分類程式（步驟 5）
   - 相關文章讀取：只處理篩選出的相關文章
   - GPT 分類模組：使用 GPT-4o-mini 進行主題分類
   - 多數決機制：每個批次進行 3 次分類，使用多數決決定最終分類
   - 結果輸出模組：輸出分類結果和統計資訊

7. **`news_media_config.py`** - 媒體配置檔案
   - 定義各媒體的網站域名（用於 Google News RSS 的 `site:` 操作符）
   - 定義文章內容的 CSS 選擇器（多個備選選擇器，以應對網站改版）
   - 定義媒體代碼（用於檔案命名）
   - 定義搜尋關鍵字列表

8. **`utils/article_extractor.py`** - 文章提取工具
   - 使用多個 CSS 選擇器提取文章內容：根據媒體配置使用對應的 CSS 選擇器，實作多個備選選擇器的回退機制
   - 清理和格式化提取的文字內容
   - 錯誤處理和回退機制：處理無法訪問、選擇器失效等錯誤情況

9. **`utils/google_news_decoder.py`** - Google News URL 解碼工具
   - 解碼方法 1：使用 `googlenewsdecoder` 套件進行演算法解碼（快速、無需網路請求）
   - 解碼方法 2：使用 `requests` 追蹤重定向（備援方法）
   - 增強解碼方法：使用更強的 HTML 解析方法（用於重試）
   - URL 格式標準化：處理 `/rss/articles/` 和 `/articles/` 格式差異

### 技術考量

#### Google News URL 解碼

- **解碼方法**：系統使用兩種方法解碼 Google News URL
  - 方法 1：`googlenewsdecoder` 套件（推薦）- 使用演算法解碼，速度快且不會被 Google 封鎖 IP
  - 方法 2：`requests` 追蹤重定向（備援）- 當方法 1 失敗時自動使用
- **URL 格式**：系統自動處理 `/rss/articles/` 和 `/articles/` 格式差異
- **解碼成功率**：不同媒體的解碼成功率可能不同，部分媒體可能需要使用重試機制

#### Google News RSS 限制

- Google News RSS 可能對請求頻率有限制，系統預設在每次請求之間延遲 1 秒
- 某些媒體可能不會出現在 Google News 結果中，這是正常現象
- 建議在網路穩定的環境下執行，避免請求失敗

#### 網站結構變化

- 不同媒體的網站結構差異很大，系統為每個媒體定義了專屬的選擇器
- 每個媒體配置多個備選 CSS 選擇器，當主要選擇器失效時自動回退
- 目前實作支援靜態 HTML 爬取，某些需要 JavaScript 渲染的內容可能無法提取

#### GPT 分類

- **API Key 設定**：執行篩選和分類前，需要在對應腳本中設定 OpenAI API Key
- **批次處理**：預設每批次處理 5-10 篇文章，可調整 `BATCH_SIZE` 參數
- **多數決機制**：每個批次進行 3 次分類，使用多數決決定最終分類，提高準確性
- **成本考量**：大量文章的分類會產生 API 費用，建議先測試小批量

#### 內容過濾

- 系統自動過濾重複的文章（基於 URL 正規化）
- 使用 GPT 自動判斷文章是否與農曆春節相關，過濾不相關文章

## 更新日誌

- **2026-03** - 完整流程版本
  - 新增 Google News URL 解碼功能（`decode_google_news_urls.py`）
  - 新增失敗 URL 重試功能（`retry_failed_urls.py`）
  - 新增從解碼 URL 爬取文章功能（`fetch_decoded_articles.py`）
  - 新增文章篩選功能（`filter_relevant_articles.py`）
  - 新增文章分類功能（`classify_lunar_2026_articles.py`）
  - 實作兩步驟處理流程：先篩選再分類
  - 新增統計結果輸出功能
  - 支援多種 URL 解碼方法（googlenewsdecoder 和 requests）

- **2026-02** - 初始版本
  - 支援 11 個國際新聞媒體
  - 整合 Google News RSS 搜尋
  - 實作多選擇器回退機制
  - 輸出格式符合分類程式要求
  - 模組化設計，易於擴展

## 授權

本專案程式碼以 MIT License 釋出。

## 聯絡資訊

如有問題或建議，請參考主專案的 README.md 或提交 Issue。
