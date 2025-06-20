lunar_new_year_gender_analysis

## Lunar New Year Gender Discourse Crawler

本專案旨在探討農曆新年期間的性別角色與社會結構變遷，透過爬蟲技術從多個社群平臺蒐集討論資料，包括 PTT、Dcard、Instagram、Threads、Facebook 等，進行文本分析與語料探勘。

目前已實作：**PTT 爬蟲模組**

---

## 📦 專案結構

lunar_new_year_gender_data/
│
├── src/                                              # 各平台爬蟲模組
│   ├── ptt_crawler.py                        # PTT 爬蟲
│   ├── dcard_crawler.py                   # Dcard 爬蟲
│   ├── instagram_crawler.py            # Instagram 爬蟲
│   ├── threads_crawler.py                # Threads 爬蟲
│   └── facebook_crawler.py             # Facebook 爬蟲
│
├── data/                                           # 爬取資料儲存區
│   ├── ptt/
│   │   ├── post_1.txt                         # 儲存文章 txt（post_id.txt）
│   │   ├── post_1_comment_1.txt    # 儲存留言 txt（post_文章id_comment_留言id.txt）
│   │   ├── post_1_comment_2.txt
│   │   └── ptt.csv                              # 儲存每篇文章的基本資訊（如單獨輸出）
│   ├── dcard/
│   │   └── dcard.csv
│   ├── instagram/
│   │   └── instagram.csv
│   ├── threads/
│   │   └── threads.csv
│   └── facebook/
│       └── facebook.csv
│
├── utils/                                    # 工具模組
│   └── lunar_mapping.py         # 農曆轉新曆對照表（自定義）
│
├── main.py                              # 主執行程式
├── requirements.txt                 # Python 依賴套件清單
├── .gitignore                            # Git 忽略檔案設定
└── README.md                     # 專案說明文件

# 儲存每篇文章的基本資訊（如單獨輸出）

## 📅 關鍵設定

- 關鍵字：`回娘家`、`煮年夜飯`、`婆媳關係`、`過勞`
- 時間範圍：每年**農曆年前後一個月**（自動轉換為新曆）
- PTT 板塊：`WomenTalk`（可自訂）

## ✅ 輸出規範

### 文章 txt（每篇一檔）

posts/

└── post_ABC123.txt

內含：

- 發文者 ID
- 發文時間
- 內文（含標題與內文）

### 留言 txt（每則一檔）

內含：

- 發文者 ID
- 發文時間
- 內文（含標題與內文）

### 留言 txt（每則一檔）

comments/

└── post_ABC123_comment_P1.txt

└── post_ABC123_comment_P2.txt

### 記錄 CSV（以平台命名）

檔案：`ptt.csv`

| post_id | 發文時間 | 觸及率 | 點讚數 | 留言數 | 關鍵字 |
| ------- | -------- | ------ | ------ | ------ | ------ |

---

## 🔧 使用說明（以 PTT 為例）

1. 安裝依賴：
   ```bash
   pip install -r requirements.txt
   ```

* 執行爬蟲（可改參數）：

  ```
  python ptt_crawler.py --start_year 2018 --end_year 2024
  ```
* 執行後自動產出資料於：

  * `posts/`
  * `comments/`
  * `ptt.csv`

---

## 🔮 待開發模組

| 平台      | 狀態      |
| --------- | --------- |
| Dcard     | 🔄 開發中 |
| Instagram | ⏳ 計劃中 |
| Threads   | ⏳ 計劃中 |
| Facebook  | ⏳ 計劃中 |

---

## 🧠 研究背景

此爬蟲工具為「農曆新年性別角色研究」計畫前期語料蒐集使用，目的是蒐集臺灣華語社群中關於春節性別分工、家庭勞動與文化再現的討論文本。

---

## 📜 License

本研究爬取之資料 **僅供學術使用** ，請遵守各平台條款，避免進行未授權的商業使用或再散佈。
