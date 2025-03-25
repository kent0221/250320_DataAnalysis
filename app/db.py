# データベース関連機能
import mysql.connector
import os
from dotenv import load_dotenv
import time
import pandas as pd
from typing import List, Dict, Any, Optional
from mysql.connector import Error
from contextlib import contextmanager
from app.config import (
    DB_HOST, DB_PORT, DB_NAME, 
    DB_USER, DB_PASSWORD
)

from app.models import VideoData

# 環境変数の読み込み
load_dotenv()

# データベース接続情報
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

class Database:
    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            yield conn
        except Error as e:
            print(f"データベース接続エラー: {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def save_video_data(self, video_data):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO videos (
                    video_id, creator_id, creator_name, video_url,
                    view_count, like_count, comment_count, share_count,
                    post_date, fetch_date, description,
                    music_title, music_author, hashtags
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    view_count = VALUES(view_count),
                    like_count = VALUES(like_count),
                    comment_count = VALUES(comment_count),
                    share_count = VALUES(share_count),
                    fetch_date = VALUES(fetch_date)
            """
            # ... データ挿入処理 ...

def get_connection(max_retries=5, retry_delay=5):
    """データベース接続を取得する関数。接続できない場合はリトライする"""
    retries = 0

    while retries < max_retries:
        try:
            conn = mysql.connector.connect(**db_config)
            print("データベースに接続しました")
            return conn
        except mysql.connector.Error as err:
            print(f"データベース接続エラー: {err}")
            retries += 1
            if retries < max_retries:
                print(f"{retry_delay}秒後にリトライします...")
                time.sleep(retry_delay)
            else:
                raise Exception("データベース接続に失敗しました")

def setup_database():
    """必要なテーブルを作成する関数"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # videos テーブルの作成
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INT AUTO_INCREMENT PRIMARY KEY,
        video_id VARCHAR(255) NOT NULL,
        creator_id VARCHAR(255) NOT NULL,
        creator_name VARCHAR(255) NOT NULL,
        video_url TEXT NOT NULL,
        view_count INT NOT NULL,
        like_count INT NOT NULL,
        comment_count INT NOT NULL,
        share_count INT NOT NULL,
        post_date DATETIME NOT NULL,
        fetch_date DATETIME NOT NULL,
        description TEXT,
        music_title VARCHAR(255),
        music_author VARCHAR(255),
        hashtags TEXT,
        UNIQUE(video_id)
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("データベーステーブルを確認しました")

def save_video_data(videos: List[VideoData]):
    """動画データをデータベースに保存"""
    if not videos:
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for video in videos:
        try:
            cursor.execute("""
            INSERT INTO videos (
                video_id, creator_id, creator_name, video_url, 
                view_count, like_count, comment_count, share_count,
                post_date, fetch_date, description, music_title, 
                music_author, hashtags
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                view_count = %s,
                like_count = %s,
                comment_count = %s,
                share_count = %s,
                fetch_date = %s
            """, (
                video.video_id, video.creator_id, video.creator_name, video.video_url,
                video.view_count, video.like_count, video.comment_count, video.share_count,
                video.post_date, video.fetch_date, video.description, video.music_title,
                video.music_author, video.hashtags,
                # 更新用の値
                video.view_count, video.like_count, video.comment_count, video.share_count,
                video.fetch_date
            ))
        except Exception as e:
            print(f"保存エラー: {e} - 動画ID: {video.video_id}")
    
    conn.commit()
    cursor.close()
    conn.close()

def get_saved_videos(limit: int = 10, offset: int = 0, sort_by: str = "view_count", search_term: Optional[str] = None):
    """保存済みの動画データを取得"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # ソートのマッピング
    sort_field = {
        "views": "view_count",
        "likes": "like_count",
        "comments": "comment_count",
        "shares": "share_count",
        "date": "post_date"
    }.get(sort_by, "view_count")
    
    # 検索条件
    where_clause = ""
    params = []
    
    if search_term:
        where_clause = "WHERE creator_id LIKE %s OR hashtags LIKE %s"
        params = [f"%{search_term}%", f"%{search_term}%"]
    
    # クエリ実行
    query = f"""
    SELECT * FROM videos
    {where_clause}
    ORDER BY {sort_field} DESC
    LIMIT %s OFFSET %s
    """
    
    params.extend([limit, offset])
    cursor.execute(query, params)
    
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return result

def get_video_statistics():
    """動画の統計情報を取得"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    # 動画総数
    cursor.execute("SELECT COUNT(*) as total FROM videos")
    total_videos = cursor.fetchone()["total"]
    
    # 平均エンゲージメント
    cursor.execute("""
    SELECT 
        AVG(view_count) as avg_views,
        AVG(like_count) as avg_likes,
        AVG(comment_count) as avg_comments,
        AVG(share_count) as avg_shares
    FROM videos
    """)
    
    engagement = cursor.fetchone()
    
    # 人気ハッシュタグ（出現回数順）
    cursor.execute("""
    SELECT hashtags, COUNT(*) as count
    FROM videos
    WHERE hashtags IS NOT NULL AND hashtags != ''
    GROUP BY hashtags
    ORDER BY count DESC
    LIMIT 10
    """)
    
    hashtags = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return {
        "total_videos": total_videos,
        "engagement": engagement,
        "popular_hashtags": hashtags
    }

def export_to_csv(data, filename="tiktok_data.csv"):
    """データをCSVファイルに出力"""
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"データをCSVファイル '{filename}' に出力しました")
    return filename
