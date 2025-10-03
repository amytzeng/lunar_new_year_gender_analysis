# ABC News Crawler

這個爬蟲專門用於爬取ABC News的文章內容，類似於現有的CNN爬蟲。

## 功能特點

1. **多種搜索方式**：
   - 透過Google News RSS搜索ABC News文章
   - 直接從URLs檔案讀取文章連結
   - 直接從ABC News網站搜索

2. **智能內容提取**：
   - 適配ABC News的HTML結構
   - 處理Google News重定向連結
   - 多種選擇器確保內容提取成功

3. **靈活的使用方式**：
   - 命令列介面
   - 可自訂輸出檔案
   - 支援批量處理

## 使用方法

### 1. 基本使用

```bash
# 顯示使用說明
python crawlers/abc_news_crawler.py

# 創建示例URLs檔案
python crawlers/abc_news_crawler.py create_sample
```

### 2. 從URLs檔案爬取

```bash
# 使用預設檔案名稱
python crawlers/abc_news_crawler.py crawl_urls

# 指定檔案名稱
python crawlers/abc_news_crawler.py crawl_urls my_urls.txt my_articles.csv
```

### 3. 透過Google News搜索

```bash
# 使用預設參數
python crawlers/abc_news_crawler.py search

# 指定搜索參數
python crawlers/abc_news_crawler.py search "Lunar New Year" 2024-01-01 2024-02-29 abc_lunar_2024.csv
```

## 檔案格式

### URLs檔案格式 (abc_urls.txt)
每行一個ABC News文章URL：
```
https://abcnews.go.com/US/lunar-new-year-celebrations-kick-off-worldwide/story?id=106123456
https://abcnews.go.com/International/china-celebrates-lunar-new-year-amid-pandemic/story?id=106123457
```

### 輸出CSV格式
包含以下欄位：
- `url`: 文章URL
- `content`: 文章內容
- `title`: 文章標題 (僅限Google News搜索)
- `pub_date`: 發布日期 (僅限Google News搜索)

## 注意事項

1. **禮貌性延遲**：爬蟲會在每次請求間加入1秒延遲，避免對伺服器造成負擔
2. **錯誤處理**：如果某篇文章無法訪問，會記錄錯誤訊息但繼續處理其他文章
3. **內容過濾**：自動過濾太短的文字內容，確保提取到有意義的文章內容

## 與CNN爬蟲的對比

| 功能 | CNN爬蟲 | ABC News爬蟲 |
|------|---------|--------------|
| 文章搜索 | Google News RSS | Google News RSS + 直接搜索 |
| 內容提取 | CNN特定選擇器 | ABC News特定選擇器 |
| 重定向處理 | 基本 | 增強 (處理Google News重定向) |
| 使用方式 | 單一模式 | 多種模式 (URLs檔案、搜索) |

## 範例使用流程

1. **創建URLs檔案**：
   ```bash
   python crawlers/abc_news_crawler.py create_sample
   ```

2. **編輯URLs檔案**：
   將示例URLs替換為實際的ABC News文章連結

3. **執行爬取**：
   ```bash
   python crawlers/abc_news_crawler.py crawl_urls abc_urls.txt abc_articles.csv
   ```

4. **檢查結果**：
   查看生成的CSV檔案，確認文章內容已正確提取

## 故障排除

如果遇到問題：

1. **無法找到文章內容**：檢查URL是否有效，ABC News的HTML結構可能已改變
2. **Google News搜索無結果**：嘗試調整搜索關鍵字或日期範圍
3. **網路錯誤**：檢查網路連接，可能需要使用代理或調整超時設定

## 依賴套件

- requests
- beautifulsoup4
- lxml
- tqdm

確保已安裝所有必要的套件：
```bash
pip install requests beautifulsoup4 lxml tqdm
```
