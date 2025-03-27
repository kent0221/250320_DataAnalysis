# TikTokデータ取得・分析アプリのメインスクリプト
import asyncio
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse
import pandas as pd
from typing import Dict, List
import pytz

from app.api.client import TikTokAPIClient
from app.db import setup_database, save_video_data, get_saved_videos, get_video_statistics, export_to_csv
from app.models import VideoData
from app.config import USE_MOCK_API
from app.ui.terminal_ui import TerminalUI
from app.utils import extract_video_id

# 環境変数の読み込み
load_dotenv()

async def get_videos_by_mode(api_client, mode, search_term=None, count=10, sort_by="views", min_views=1000, min_likes=0, days_ago=None):
    """
    指定したモードに応じて動画を取得する
    
    Args:
        api_client: APIクライアント
        mode: 取得モード
        search_term: 検索語
        count: 取得数
        sort_by: ソート基準
        min_views: 最小再生回数
        min_likes: 最小いいね数
        days_ago: 何日前までの動画を対象にするか
        
    Returns:
        取得した動画リスト
    """
    videos = []
    
    if mode == "trend":
        print(f"トレンド動画を取得しています...")
        videos = await api_client.get_trending_videos(
            count=count,
            sort_by=sort_by,
            min_views=min_views,
            min_likes=min_likes,
            days_ago=days_ago
        )
        
    elif mode == "hashtag":
        if not search_term:
            # ハッシュタグが指定されていない場合はトレンド動画を取得
            print(f"トレンド動画を取得しています...")
            videos = await api_client.get_trending_videos(
                count=count,
                sort_by=sort_by,
                min_views=min_views,
                min_likes=min_likes,
                days_ago=days_ago
            )
        else:
            # ハッシュタグが指定されている場合
            hashtag = search_term.replace("#", "")
            print(f"ハッシュタグ '#{hashtag}' の動画を取得しています...")
            videos = await api_client.get_hashtag_videos(hashtag=hashtag, count=count, sort_by=sort_by, min_views=min_views)
        
    elif mode == "video":
        print(f"指定された動画を取得しています...")
        videos = []
        for url in search_term:
            video_id = extract_video_id(url)
            if video_id:
                try:
                    video = await api_client.get_video_by_id(video_id)
                    if video:
                        videos.append(video)
                except Exception as e:
                    print(f"動画ID {video_id} の取得に失敗しました: {e}")
                    continue
    
    # 日付フィルタリング
    if days_ago and videos:
        cutoff_date = datetime.now() - timedelta(days=days_ago)
        cutoff_timestamp = int(cutoff_date.timestamp())
        videos = [v for v in videos if v.get('createTime', 0) >= cutoff_timestamp]
    
    # いいね数でフィルタリング
    if min_likes > 0 and videos:
        videos = [v for v in videos if v.get('stats', {}).get('diggCount', 0) >= min_likes]
    
    return videos

async def interactive_mode():
    """インタラクティブモードのメイン処理"""
    ui = TerminalUI()
    api_client = TikTokAPIClient()

    while True:
        choice = ui.initial_screen()
        if choice == "4":  # 終了
            break
            
        if choice == "1":  # データ取得
            settings = ui.data_settings_screen()
            if settings:
                data = await fetch_data(api_client, settings)
                if data:
                    stats = calculate_stats(data)
                    while True:
                        result_choice = ui.results_screen(stats)
                        if handle_results(result_choice, data, ui):
                            break
                else:
                    print("\nデータが取得できませんでした。")
                    input("Enterキーで続行...")

def calculate_stats(data: List[Dict]) -> Dict:
    """データの統計情報を計算"""
    total_views = sum(v.get("stats", {}).get("playCount", 0) for v in data)
    total_likes = sum(v.get("stats", {}).get("diggCount", 0) for v in data)
    
    return {
        "total_videos": len(data),
        "total_views": total_views,
        "total_likes": total_likes,
        "avg_views": total_views / len(data) if data else 0,
        "avg_likes": total_likes / len(data) if data else 0
    }

def handle_results(choice: str, data: List[Dict], ui: TerminalUI) -> bool:
    """結果画面での選択を処理"""
    if choice == "1":  # CSVエクスポート
        # 日本時間の日付を取得
        jst = pytz.timezone('Asia/Tokyo')
        current_time = datetime.now(jst)
        
        # CSVファイル名の生成
        mode = data[0].get("type", "trend")  # データから取得モードを取得
        if mode == "trend":
            filename_prefix = "trend"
        elif mode == "hashtag":
            hashtag = data[0].get("hashtag", "")
            filename_prefix = f"hashtag_{hashtag}" if hashtag else "trend"
        else:  # video mode
            filename_prefix = "specific"
        
        csv_filename = f"{filename_prefix}_{current_time.strftime('%Y%m%d_%H%M%S')}.csv"
        export_to_csv(data, csv_filename)
        print(f"\nデータを {csv_filename} にエクスポートしました")
        input("\nEnterキーで続行...")
        return False
        
    elif choice == "2":  # データサマリー表示
        ui.display_data_summary(data)
        return False
        
    elif choice == "3":  # データ削除
        if input("\nデータを削除しますか？ (y/N): ").lower() == 'y':
            # データベースから削除する処理を実装
            print("\nデータを削除しました")
            input("Enterキーで続行...")
        return True
    elif choice == "4":  # 終了
        return True
    return False

def display_videos_table(data: List[Dict]):
    """動画データをテーブル形式で表示"""
    if not data:
        print("\n表示するデータがありません。")
        return

    # データ構造のデバッグ出力を追加
    print("\nデータ構造確認:", data[0] if data else "データなし")
    
    try:
        # 表示するデータの準備
        table_data = []
        for video in data:
            stats = video.get("stats", {})
            author = video.get("author", {})
            
            # 行データの作成（データ構造に合わせて修正）
            row = {
                "投稿日時": datetime.fromtimestamp(int(video.get("createTime", 0))).strftime("%Y/%m/%d %H:%M"),
                "作成者": author.get("uniqueId", "不明"),
                "再生数": f'{stats.get("playCount", 0):,}',
                "いいね数": f'{stats.get("diggCount", 0):,}',
                "コメント数": f'{stats.get("commentCount", 0):,}',
                "シェア数": f'{stats.get("shareCount", 0):,}',
                "動画URL": video.get("video", {}).get("playAddr", "")
            }
            table_data.append(row)

        # pandasを使用してテーブル表示
        df = pd.DataFrame(table_data)
        print("\n=== 取得した動画のサマリー ===")
        print(df.to_string(index=False))
        
        # 統計情報の表示
        print("\n=== 統計情報 ===")
        print(f"総動画数: {len(data):,}")
        print(f"総再生数: {sum(v.get('stats', {}).get('playCount', 0) for v in data):,}")
        print(f"総いいね数: {sum(v.get('stats', {}).get('diggCount', 0) for v in data):,}")
        
    except Exception as e:
        print(f"データ表示エラー: {e}")

def format_number(num):
    """数値を読みやすい形式にフォーマット"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def parse_args():
    """コマンドライン引数をパース"""
    parser = argparse.ArgumentParser(description="TikTok Data Retrieval Tool")
    parser.add_argument("--interactive", action="store_true", help="対話モードで実行")
    parser.add_argument("--mode", choices=["trend", "user", "hashtag"], default="trend",
                        help="取得モード: trend=トレンド動画, user=特定ユーザー, hashtag=ハッシュタグ")
    parser.add_argument("--search", type=str, help="検索語（ユーザー名またはハッシュタグ）")
    parser.add_argument("--count", type=int, default=10, help="取得する動画数")
    parser.add_argument("--sort", choices=["views", "likes", "comments", "date"], default="views",
                        help="ソート基準")
    parser.add_argument("--min-views", type=int, default=1000, help="最小再生回数")
    parser.add_argument("--force-mock", action="store_true", help="Force using mock API")
    parser.add_argument("--force-real-api", action="store_true", help="Force using real API")
    
    return parser.parse_args()

async def fetch_data(api_client: TikTokAPIClient, settings: Dict) -> List[Dict]:
    """データ取得とソート処理"""
    try:
        # APIからデータを取得
        data = await api_client.fetch_videos(settings)
        
        if data:
            # ソートキーの設定
            sort_keys = {
                "views": ("stats", "playCount"),
                "likes": ("stats", "diggCount"),
                "comments": ("stats", "commentCount"),
                "shares": ("stats", "shareCount")
            }
            
            # ソート処理
            sort_by = settings.get("sort_by", "views")
            if sort_by in sort_keys:
                key1, key2 = sort_keys[sort_by]
                data.sort(key=lambda x: x.get(key1, {}).get(key2, 0), reverse=True)
        
        if data:
            # データベースに保存
            video_objects = [VideoData.from_api_response(v) for v in data]
            save_video_data(video_objects)
            return data
        return []
    except Exception as e:
        print(f"データ取得エラー: {e}")
        return []

async def main(mode="trend", search_term=None, count=10, sort_by="views", min_views=1000):
    """
    メイン実行関数（コマンドライン引数用）
    """
    print(f"TikTok検索を開始します... モード: {mode}, ソート: {sort_by}")
    
    # データベース初期化
    setup_database()
    print("データベースを初期化しました")
    
    # 引数でモック設定を上書きできるようにする
    use_mock = USE_MOCK_API
    if args.force_mock:
        use_mock = True
    elif args.force_real_api:
        use_mock = False
    
    # APIクライアントの初期化
    api_client = TikTokAPIClient(use_mock=use_mock)
    
    # 動画データ取得
    videos = await get_videos_by_mode(api_client, mode, search_term, count, sort_by, min_views)
    
    if not videos:
        print("条件に合う動画が見つかりませんでした。")
        return
        
    # VideoDataオブジェクトに変換
    video_objects = [VideoData.from_api_response(v) for v in videos]
    
    # データベースに保存
    save_video_data(video_objects)
    print("データをデータベースに保存しました")
    
    # 動画情報をテーブル形式で表示
    display_videos_table(videos)
    
    # 日本時間の日付を取得
    jst = pytz.timezone('Asia/Tokyo')
    current_time = datetime.now(jst)
    
    # CSVファイル名の生成
    if mode == "trend":
        filename_prefix = "trend"
    elif mode == "hashtag":
        filename_prefix = f"hashtag_{search_term.replace('#', '')}" if search_term else "trend"
    else:  # video mode
        filename_prefix = "specific"
    
    # 日本時間でのタイムスタンプを追加
    csv_filename = f"{filename_prefix}_{current_time.strftime('%Y%m%d_%H%M%S')}.csv"
    
    # CSVに出力
    export_to_csv([v.__dict__ for v in video_objects], csv_filename)

if __name__ == "__main__":
    args = parse_args()
    
    if args.interactive:
        # 対話モードで実行
        asyncio.run(interactive_mode())
    else:
        # コマンドライン引数モードで実行
        asyncio.run(main(
            mode=args.mode,
            search_term=args.search,
            count=args.count,
            sort_by=args.sort,
            min_views=args.min_views
        ))