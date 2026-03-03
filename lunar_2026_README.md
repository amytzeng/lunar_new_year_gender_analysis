# 2026 年農曆春節國際媒體報導爬蟲系統

本系統用於爬取多個國際新聞媒體在 2026 年農曆春節前後（2026/2/7 至今）的相關報導，涵蓋農曆新年、年夜飯、春節習俗、回娘家等主題。爬取的文章將儲存在 `lunar_2026_data/` 資料夾中，與舊資料分開存放，並可直接用於後續的新聞文章主題分類。

## 功能特色

- **多媒體支援**：支援 11 個國際新聞媒體的爬取
- **智能搜尋**：透過 Google News RSS 搜尋相關文章，支援多個關鍵字組合
- **自動去重**：自動過濾重複文章（基於 URL）
- **格式相容**：輸出格式符合 `classify_news_gpt` 分類程式的要求
- **進度顯示**：使用進度條顯示爬取進度
- **錯誤處理**：完善的錯誤處理機制，包含重試機制（最多 3 次）和錯誤記錄
- **模組化設計**：媒體配置與爬蟲邏輯分離，易於擴展和維護
- **多選擇器回退**：每個媒體配置多個 CSS 選擇器，自動回退以應對網站改版

## 支援的媒體

本系統支援以下 11 個國際新聞媒體：

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

### 3. 確認檔案結構

確保以下檔案存在：

```
crawlers/
├── multi_news_crawler.py      # 主爬蟲程式
├── news_media_config.py        # 媒體配置檔案
└── utils/
    ├── __init__.py             # Utils 套件初始化
    └── article_extractor.py   # 文章提取工具
```

完整的專案檔案結構：

```
lunar_new_year_gender_analysis/
├── crawlers/                    # 爬蟲程式
│   ├── multi_news_crawler.py   # 主爬蟲程式（2026 年新增）
│   ├── news_media_config.py    # 媒體配置檔案（2026 年新增）
│   └── utils/                  # 工具模組（2026 年新增）
│       ├── __init__.py
│       └── article_extractor.py
├── lunar_2026_data/             # 2026 年春節報導資料（與舊資料分開）
│   ├── 1.txt                   # 文章檔案（數字命名）
│   ├── 2.txt
│   └── ...
├── org_data/                    # 舊資料（保持不變）
│   ├── cnn/
│   ├── abc_posts/
│   └── ...
├── classify_news_gpt/          # 新聞文章主題分類
│   ├── data/                   # 待分類資料
│   ├── classify_news_articles.py
│   └── ...
└── requirements.txt            # Python 套件需求
```

## 使用方式

### 基本使用

使用預設設定爬取所有媒體的文章（日期範圍：2026-02-07 至今）：

```bash
python crawlers/multi_news_crawler.py
```

### 指定媒體來源

只爬取特定媒體的文章：

```bash
python crawlers/multi_news_crawler.py --media cnn bbc reuters
```

### 自訂日期範圍

指定開始和結束日期：

```bash
python crawlers/multi_news_crawler.py --start-date 2026-02-07 --end-date 2026-03-01
```

### 自訂關鍵字

使用自訂關鍵字搜尋：

```bash
python crawlers/multi_news_crawler.py --keywords "Lunar New Year" "Chinese New Year" "Spring Festival"
```

### 調整爬取參數

- `--max-per-keyword`: 每個關鍵字最多爬取的文章數（預設：50）
- `--delay`: 請求之間的延遲時間（秒，預設：1.0）
- `--output-dir`: 輸出資料夾（預設：lunar_2026_data）

完整範例：

```bash
python crawlers/multi_news_crawler.py \
  --media cnn bbc reuters \
  --start-date 2026-02-07 \
  --end-date 2026-03-01 \
  --max-per-keyword 30 \
  --delay 1.5 \
  --output-dir lunar_2026_data
```

### 查看所有選項

```bash
python crawlers/multi_news_crawler.py --help
```

## 輸出格式

### 資料夾結構

爬取的文章將儲存在 `lunar_2026_data/` 資料夾中：

```
lunar_2026_data/
├── 1.txt
├── 2.txt
├── 3.txt
└── ...
```

### 檔案命名

檔案使用純數字命名（`1.txt`, `2.txt`, `3.txt` 等），便於分類程式按照數字順序處理。

### 檔案內容格式

每個 `.txt` 檔案包含以下資訊：

```
article_id: {media_code}_{序號}
url: {文章URL}
title: {文章標題}
date: {發布日期}
author: {作者}
matched_keywords: {匹配的關鍵字}
content:
{文章正文內容}
```

範例：

```
article_id: cnn_0001
url: https://www.cnn.com/2026/02/15/lunar-new-year-guide/index.html
title: Lunar New Year 2026: A Complete Guide
date: 2026-02-15
author: 
matched_keywords: Lunar New Year
content:
The Lunar New Year, also known as Chinese New Year or Spring Festival...
```

**重要說明**：分類程式（`classify_news_gpt/classify_news_articles.py`）會讀取整個檔案內容進行分類，包括 metadata 和文章正文。這意味著 metadata 也會被當作文章內容的一部分，這符合現有設計，有助於分類程式更好地理解文章上下文。

## 與分類程式整合

爬取的文章可以直接用於 `classify_news_gpt` 分類程式進行主題分類。

### 使用流程

1. **執行爬蟲**：爬取文章並儲存到 `lunar_2026_data/`

```bash
python crawlers/multi_news_crawler.py
```

2. **準備分類資料**：將文章複製到分類程式的資料夾

```bash
# 方法一：複製檔案
cp lunar_2026_data/*.txt classify_news_gpt/data/

# 方法二：修改分類程式直接讀取 lunar_2026_data/
# 編輯 classify_news_gpt/classify_news_articles.py
# 將 data_dir 改為 "lunar_2026_data"
```

3. **執行分類**：使用 GPT-4o-mini 進行主題分類

```bash
cd classify_news_gpt
python classify_news_articles.py
```

4. **整理分類結果**：將文章移動到對應的分類資料夾

```bash
python sort.py
```

5. **查看統計結果**：計算各類別的比例

```bash
python prop.py
```

### 分類類別

文章將被分類為以下 5 個類別：

1. **農曆新年與文化慶祝** - 直接討論農曆新年慶祝活動、傳統、習俗、節慶相關的文章
2. **政治與政策** - 政府政策、政治人物、外交關係、政治事件相關的文章
3. **衝突與安全** - 戰爭、恐怖主義、軍事衝突、重大犯罪事件相關的文章
4. **經濟與商業** - 經濟政策、商業活動、金融市場、企業相關的文章
5. **其他/不相關** - 與上述類別無關、內容過於簡短或缺失的文章

## 注意事項

### 網路連線

- 爬蟲需要穩定的網路連線來訪問 Google News RSS 和各新聞網站
- 建議在網路穩定的環境下執行

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

### 檔案編號

- 如果 `lunar_2026_data/` 資料夾中已有檔案，新爬取的文章會從現有最大編號繼續編號
- 例如：如果已有 `1.txt` 到 `100.txt`，新文章會從 `101.txt` 開始

### 日期格式

- 日期格式必須為 `YYYY-MM-DD`（例如：2026-02-07）
- 結束日期預設為執行當日
- 系統內部使用 RFC3339 格式（yyyy-mm-dd）與 Google News RSS API 溝通
- 預設起始日期：2026-02-07（農曆春節前後）

## 技術架構

### 核心設計理念

系統採用模組化設計，將媒體配置與爬蟲邏輯分離。每個媒體的網站結構和文章內容選擇器都定義在配置檔案中，方便後續擴展或調整。爬蟲流程分為兩個階段：第一階段透過 Google News RSS 搜尋符合條件的文章連結，第二階段逐一訪問這些連結並提取文章內容。

### 核心模組

1. **`multi_news_crawler.py`** - 主爬蟲程式
   - Google News RSS 搜尋模組：使用 Google News RSS API 搜尋指定媒體的文章，支援日期範圍篩選和多個關鍵字組合搜尋，處理 Google News 連結的重定向以提取實際的新聞網站 URL
   - 文章去重模組：基於 URL 自動過濾重複文章
   - 檔案儲存模組：按照指定格式儲存文章，確保檔案編號連續

2. **`news_media_config.py`** - 媒體配置檔案
   - 定義各媒體的網站域名（用於 Google News RSS 的 `site:` 操作符）
   - 定義文章內容的 CSS 選擇器（多個備選選擇器，以應對網站改版）
   - 定義媒體代碼（用於檔案命名）
   - 定義搜尋關鍵字列表

3. **`utils/article_extractor.py`** - 文章提取工具
   - 從 Google News 連結提取實際 URL：處理 Google News 重定向連結，提取實際的新聞網站 URL
   - 使用多個 CSS 選擇器提取文章內容：根據媒體配置使用對應的 CSS 選擇器，實作多個備選選擇器的回退機制
   - 清理和格式化提取的文字內容
   - 錯誤處理和回退機制：處理無法訪問、選擇器失效等錯誤情況

### 工作流程

```
Google News RSS 搜尋（多關鍵字）
    ↓
取得文章連結列表
    ↓
處理 Google News 重定向，提取實際 URL
    ↓
去重處理（基於 URL）
    ↓
逐一訪問並提取內容（使用多選擇器回退）
    ↓
清理和格式化文字內容
    ↓
儲存為 TXT 檔案（數字命名）
```

### 技術考量

#### Google News RSS 限制

- Google News RSS 可能對請求頻率有限制，系統預設在每次請求之間延遲 1 秒
- 某些媒體可能不會出現在 Google News 結果中，這是正常現象
- 建議在網路穩定的環境下執行，避免請求失敗

#### 網站結構變化

- 不同媒體的網站結構差異很大，系統為每個媒體定義了專屬的選擇器
- 每個媒體配置多個備選 CSS 選擇器，當主要選擇器失效時自動回退
- 目前實作支援靜態 HTML 爬取，某些需要 JavaScript 渲染的內容可能無法提取

#### 內容過濾

- 系統自動過濾重複的文章（基於 URL 正規化）
- 可以透過關鍵字匹配驗證文章內容是否真的與春節相關（未來可擴展）

## 常見問題

### Q: 為什麼某些媒體沒有爬取到文章？

A: 可能的原因包括：
- Google News RSS 在該日期範圍內沒有相關文章
- 該媒體網站結構改變，需要更新 CSS 選擇器
- 網路連線問題

### Q: 如何新增更多媒體？

A: 系統設計允許輕鬆新增更多媒體，無需修改主程式邏輯。步驟如下：

1. **編輯配置檔案**：打開 `crawlers/news_media_config.py`
2. **新增媒體配置**：在 `NEWS_MEDIA_CONFIG` 字典中新增媒體配置，格式如下：
   ```python
   "media_name": {
       "domain": "example.com",           # 網站域名
       "code": "example",                 # 媒體代碼（用於檔案命名）
       "selectors": [                     # CSS 選擇器列表（按優先順序）
           "div.article-body",            # 主要選擇器
           "div.content",                 # 備選選擇器 1
           "article[itemprop='articleBody']",  # 備選選擇器 2
           # ... 更多備選選擇器
       ]
   }
   ```
3. **測試選擇器**：執行爬蟲測試，確認選擇器能正確提取文章內容
4. **調整選擇器**：如果提取失敗，調整或新增 CSS 選擇器
5. **完成**：無需修改主程式，系統會自動使用新配置

**注意**：建議為每個媒體配置至少 3-5 個備選選擇器，以應對網站改版。

### Q: 如何調整文章內容的提取方式？

A: 編輯 `crawlers/news_media_config.py`，修改對應媒體的 `selectors` 列表，添加或調整 CSS 選擇器。

### Q: 爬取速度太慢怎麼辦？

A: 可以調整以下參數：
- 減少 `--max-per-keyword` 的值
- 減少 `--delay` 的值（但可能增加被封鎖的風險）
- 只爬取特定媒體（使用 `--media` 參數）

### Q: 檔案格式不符合分類程式要求？

A: 確保檔案：
- 使用純數字命名（`1.txt`, `2.txt` 等）
- 包含完整的 metadata 和 content
- 儲存在正確的資料夾中

## 系統擴展性

系統設計允許輕鬆新增更多媒體，無需修改主程式邏輯：

1. **配置驅動**：所有媒體配置都集中在 `news_media_config.py` 中
2. **選擇器回退**：多個備選選擇器確保在網站改版時仍能提取內容
3. **模組化設計**：媒體配置、文章提取、檔案儲存等功能分離，易於維護和擴展

### 擴展步驟

1. 在 `news_media_config.py` 中新增媒體配置
2. 測試並調整 CSS 選擇器
3. 無需修改主程式邏輯

## 更新日誌

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
