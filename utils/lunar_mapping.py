# crawlers/utils/lunar_mapping.py

import datetime

# 農曆新年日期對照表（可依需求擴充）
LUNAR_NEW_YEARS = {
    2019: "2019-02-05",
    2020: "2020-01-25",
    2021: "2021-02-12",
    2022: "2022-02-01",
    2023: "2023-01-22",
    2024: "2024-02-10",
    2025: "2025-01-29",
    2026: "2026-02-17",
    2027: "2027-02-06",
}

def get_lunar_new_year_ranges(start_year: int, end_year: int,
                              days_before: int = 30, days_after: int = 30):
    """
    傳回指定年份範圍內，農曆新年前後日期區間（預設各30天）。

    :param start_year: 起始西元年（含）
    :param end_year: 結束西元年（含）
    :param days_before: 從農曆初一往前計算幾天（預設 30）
    :param days_after: 從農曆初一往後計算幾天（預設 30）
    :return: List of tuples，格式為 (start_date, end_date)，皆為 datetime.date 型別
    """
    date_ranges = []
    for year in range(start_year, end_year + 1):
        lunar_str = LUNAR_NEW_YEARS.get(year)
        if not lunar_str:
            continue

        lunar_date = datetime.datetime.strptime(lunar_str, "%Y-%m-%d").date()
        start_date = lunar_date - datetime.timedelta(days=days_before)
        end_date = lunar_date + datetime.timedelta(days=days_after)
        date_ranges.append((start_date, end_date))

    return date_ranges

# 使用範例（直接執行此檔案時會印出）
# if __name__ == "__main__":
#     # 查詢 2020～2025 年，每年農曆新年前後「各 14 天」的範圍
#     ranges = get_lunar_new_year_ranges(2020, 2025, days_before=14, days_after=14)

#     print("農曆新年前後各14天的日期範圍如下：")
#     for year, (start, end) in zip(range(2020, 2026), ranges):
#         print(f"{year}：從 {start} 到 {end}")


# 使用說明：
# 1. 導入模組：
# from crawlers.utils.lunar_mapping import get_lunar_new_year_ranges

# 2. 取得時間區間（以前 30 天、後 30 天為例）：
# date_ranges = get_lunar_new_year_ranges(2020, 2025)

# 3. 自訂前後天數範圍（如：前 14 天、後 7 天）：
# date_ranges = get_lunar_new_year_ranges(2020, 2025, days_before=14, days_after=7)