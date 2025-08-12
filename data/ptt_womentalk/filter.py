import os
from pathlib import Path

def filter_posts_and_comments(post_dir, comment_dir, keyword):
    post_dir = Path(post_dir)
    comment_dir = Path(comment_dir)

    csv_path = Path("data/ptt/ptt.csv")
    if not csv_path.exists():
        print(f"CSV file {csv_path} does not exist.")
        return

    to_delete_posts = set()
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line in lines[1:]:  # Skip header
        parts = line.strip().split(',')
        if len(parts) < 8:
            continue
        post_id = parts[0]
        keywords = parts[7]  # 這裡是整行關鍵字組成的字串
        if keyword in keywords.split(','):
            to_delete_posts.add(post_id)
    
    if not to_delete_posts:
        print(f"❌ 找不到包含關鍵字「{keyword}」的文章。")
    else:
        print(f"✅ 準備刪除 {len(to_delete_posts)} 篇包含「{keyword}」的文章及留言")

    for post_file in post_dir.glob("*.txt"):
        post_id = post_file.stem
        if post_id in to_delete_posts:
            print(f"🗑 刪除文章：{post_file}")
            post_file.unlink()

    for comment_file in comment_dir.glob("*.txt"):
        comment_id = comment_file.stem.split('_')[1]
        if comment_id in to_delete_posts:
            print(f"🗑 刪除留言：{comment_file}")
            comment_file.unlink()

if __name__ == "__main__":
    post_directory = "data/ptt/posts"
    comment_directory = "data/ptt/comments"
    keyword_to_filter = "過勞"

    filter_posts_and_comments(post_directory, comment_directory, keyword_to_filter)
    print("✅ 過濾完成")



# # 過濾掉 keyword == "過勞" 的文章
# # 刪除這些文章以及對應的留言
# # 分別在 post, comment 資料夾中
# import os
# import json
# from pathlib import Path
# def filter_posts_and_comments(post_dir, comment_dir, keyword):
#     post_dir = Path(post_dir)
#     comment_dir = Path(comment_dir)

#     # Filter posts
#     # 開 csv 檔，看 keyword 欄位
#     csv_path = "data/ptt/ptt.csv"
#     csv_path = Path(csv_path)
#     if not csv_path.exists():
#         print(f"CSV file {csv_path} does not exist.")
#         return
#     with open(csv_path, 'r', encoding='utf-8') as f:
#         lines = f.readlines()
#     to_delete_posts = set()
#     for line in lines[1:]:  # Skip header
#         parts = line.strip().split(',')
#         if len(parts) < 2:
#             continue
#         post_id = parts[0]
#     if len(parts) >= 8:
#         keywords = parts[7]  # 這是一個用逗號分隔的字串
#         if keyword in keywords.split(','):
#             to_delete_posts.add(post_id)
    
#     # 遍歷 post 資料夾，刪除符合條件的文章
#     for post_file in post_dir.glob("*.txt"):
#         post_id = post_file.stem  # Get the file name without extension
#         if post_id in to_delete_posts:
#             print(f"Deleting post: {post_file}")
#             post_file.unlink()  # Delete the file

#     # Filter comments
#     # 直接看檔名，與要刪除的文章有相同 id 的留言即刪除
#     for comment_file in comment_dir.glob("*.txt"):
#         comment_id = comment_file.stem.split('_')[1]  # Get the post id from the filename
#         if comment_id in to_delete_posts:
#             print(f"Deleting comment: {comment_file}")
#             comment_file.unlink()  # Delete the file

# if __name__ == "__main__":
#     post_directory = "data/ptt/posts"
#     comment_directory = "data/ptt/comments"
#     keyword_to_filter = "過勞"

#     filter_posts_and_comments(post_directory, comment_directory, keyword_to_filter)
#     print("過濾完成。")