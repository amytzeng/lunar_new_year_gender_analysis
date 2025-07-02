import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.ptt_crawler import run_ptt
from src.dcard_crawler import run_dcard
from src.instagram_crawler import run_instagram

if __name__ == "__main__":
    start_year = 2019
    end_year = 2024
    keywords = ["回娘家", "煮年夜飯", "婆媳關係"]

    # run_ptt(start_year, end_year, keywords)
    # run_dcard(start_year, end_year, keywords)
    run_instagram(keywords)  #（最多處理 100 篇）
    # print("已完成所有爬蟲任務！")