# TikTokデータ取得・分析アプリのメインスクリプト
import asyncio
import time
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse
import pandas as pd

from app.api.client import TikTokAPIClient
from app.db import setup_database, save_video_data, get_saved_videos, get_video_statistics, export_to_csv
from app.models import VideoData
from app.config import USE_MOCK_API

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
        # #が含まれている場合は削除
        hashtag = search_term.replace("#", "")
        print(f"ハッシュタグ '#{hashtag}' の動画を取得しています...")
        videos = api_client.get_hashtag_videos(hashtag=hashtag, count=count, sort_by=sort_by, min_views=min_views)
        
    elif mode == "video":
        # 動画URLまたはIDのリストから取得
        print(f"指定された動画を取得しています...")
        videos = []
        for url in search_term:
            # URLから動画IDを抽出
            video_id = extract_video_id(url)
            if video_id:
                video = api_client.get_video_by_id(video_id)
                if video:
                    videos.append(video)
    
    # 日付フィルタリング
    if days_ago and videos:
        cutoff_date = datetime.now() - timedelta(days=days_ago)
        cutoff_timestamp = int(cutoff_date.timestamp())
        videos = [v for v in videos if v.get('createTime', 0) >= cutoff_timestamp]
    
    # いいね数でフィルタリング
    if min_likes > 0 and videos:
        videos = [v for v in videos if v.get('stats', {}).get('diggCount', 0) >= min_likes]
    
    return videos

def extract_video_id(url):
    """
    TikTok動画URLからIDを抽出する
    
    Args:
        url: TikTok動画URL
        
    Returns:
        抽出した動画ID、抽出できない場合はそのままURLを返す
    """
    # 1. URLから直接IDを抽出する試み
    import re
    match = re.search(r'video/(\d+)', url)
    if match:
        return match.group(1)
    
    # 2. 数字のみの場合はそのままIDとして返す
    if url.isdigit():
        return url
    
    # 抽出できない場合はそのまま返す
    return url

async def interactive_mode():
    """対話式インターフェースのメイン関数"""
    print("===== TikTok動画データ取得・分析アプリ =====")
    print("データベースを初期化しています...")
    
    # データベース初期化
    setup_database()
    
    # APIクライアントの初期化（環境変数から設定を読み込む）
    api_client = TikTokAPIClient()
    
    while True:
        print("\n取得モードを選択してください:")
        print("1. トレンド動画")
        print("2. ハッシュタグ指定")
        print("3. 動画URL指定")
        print("0. 終了")
        
        mode_choice = input("選択 (0-3): ").strip()
        
        if mode_choice == "0":
            print("アプリケーションを終了します。")
            break
            
        # パラメータの初期値
        search_term = None
        count = 10
        sort_by = "views"
        min_views = 1000
        min_likes = 0
        days_ago = None
        
        # モード別の処理
        if mode_choice == "1":
            mode = "trend"
            # トレンド動画の場合のパラメータ入力
            count = int(input("取得する動画数 (デフォルト: 10): ").strip() or "10")
            
            print("ソート基準を選択してください:")
            print("1. 再生回数 (多い順)")
            print("2. いいね数 (多い順)")
            print("3. 投稿日時 (新しい順)")
            sort_choice = input("選択 (1-3, デフォルト: 1): ").strip() or "1"
            
            sort_mapping = {"1": "views", "2": "likes", "3": "date"}
            sort_by = sort_mapping.get(sort_choice, "views")
            
            min_views_input = input("最小再生回数 (デフォルト: 1000): ").strip()
            min_views = int(min_views_input) if min_views_input else 1000
            
            min_likes_input = input("最小いいね数 (デフォルト: 0): ").strip()
            min_likes = int(min_likes_input) if min_likes_input else 0
            
            days_ago_input = input("何日前までの動画を対象にするか (デフォルト: 指定なし): ").strip()
            days_ago = int(days_ago_input) if days_ago_input else None
            
        elif mode_choice == "2":
            mode = "hashtag"
            # ハッシュタグ指定の場合のパラメータ入力
            search_term = input("ハッシュタグを入力 (#は省略可, 空の場合は全てのハッシュタグ): ").strip()
            
            # ハッシュタグが空の場合は特別に処理（トレンド動画と同様に扱う）
            is_empty_hashtag = not search_term
            
            count = int(input("取得する動画数 (デフォルト: 10): ").strip() or "10")
            
            print("ソート基準を選択してください:")
            print("1. 再生回数 (多い順)")
            print("2. いいね数 (多い順)")
            print("3. 投稿日時 (新しい順)")
            sort_choice = input("選択 (1-3, デフォルト: 1): ").strip() or "1"
            
            sort_mapping = {"1": "views", "2": "likes", "3": "date"}
            sort_by = sort_mapping.get(sort_choice, "views")
            
            min_views_input = input("最小再生回数 (デフォルト: 1000): ").strip()
            min_views = int(min_views_input) if min_views_input else 1000
            
            min_likes_input = input("最小いいね数 (デフォルト: 0): ").strip()
            min_likes = int(min_likes_input) if min_likes_input else 0
            
            days_ago_input = input("何日前までの動画を対象にするか (デフォルト: 指定なし): ").strip()
            days_ago = int(days_ago_input) if days_ago_input else None
            
        elif mode_choice == "3":
            mode = "video"
            # 動画URL指定の場合のパラメータ入力
            video_urls = []
            while True:
                url = input("動画URLまたはIDを入力: ").strip()
                if url:
                    video_urls.append(url)
                
                add_more = input("さらに動画URLを追加しますか？ (y/n): ").strip().lower()
                if add_more != 'y':
                    break
                    
            if not video_urls:
                print("動画URLが指定されていません。最初からやり直してください。")
                continue
                
            search_term = video_urls
            
            # 動画URL指定の場合は他の条件指定は不要
            count = len(video_urls)  # URLの数と同じにする
            
        else:
            print("無効な選択です。もう一度お試しください。")
            continue
        
        # パラメータ確認
        print("\n=== 実行パラメータ ===")
        print(f"取得モード: {mode}")
        
        if mode == "hashtag":
            if is_empty_hashtag:
                print("ハッシュタグ: 指定なし（全ハッシュタグ対象）")
            else:
                print(f"ハッシュタグ: {search_term}")
            print(f"取得数: {count}")
            print(f"ソート基準: {sort_by}")
            print(f"最小再生回数: {min_views}")
            if min_likes > 0:
                print(f"最小いいね数: {min_likes}")
            if days_ago:
                print(f"対象期間: 過去{days_ago}日以内")
                
        elif mode == "trend":
            print(f"取得数: {count}")
            print(f"ソート基準: {sort_by}")
            print(f"最小再生回数: {min_views}")
            if min_likes > 0:
                print(f"最小いいね数: {min_likes}")
            if days_ago:
                print(f"対象期間: 過去{days_ago}日以内")
                
        elif mode == "video":
            # 動画URL指定の場合は、URLのみ表示
            print(f"動画URL: {', '.join(search_term)}")
        
        # 実行確認
        confirm = input("\n上記の条件で実行しますか？ (y/n): ").strip().lower()
        if confirm != 'y':
            print("実行をキャンセルしました。")
            continue
        
        # 動画データ取得
        if mode == "hashtag" and is_empty_hashtag:
            # 空のハッシュタグの場合はトレンド動画として扱う
            print("ハッシュタグが指定されていないため、トレンド動画を取得します...")
            videos = await get_videos_by_mode(
                api_client, 
                "trend",  # トレンドモードで取得
                search_term=None,
                count=count, 
                sort_by=sort_by, 
                min_views=min_views,
                min_likes=min_likes,
                days_ago=days_ago
            )
        else:
            videos = await get_videos_by_mode(
                api_client, 
                mode, 
                search_term=search_term, 
                count=count, 
                sort_by=sort_by, 
                min_views=min_views,
                min_likes=min_likes,
                days_ago=days_ago
            )
        
        if not videos:
            print("条件に合う動画が見つかりませんでした。")
            continue
            
        print(f"{len(videos)}件の動画を取得しました")
        
        # VideoDataオブジェクトに変換
        video_objects = [VideoData.from_api_response(v) for v in videos]
        
        # データベースに保存
        save_video_data(video_objects)
        print("データをデータベースに保存しました")
        
        # 動画情報をテーブル形式で表示
        display_videos_table(videos)
        
        # CSVに出力
        csv_filename = f"tiktok_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        export_to_csv([v.__dict__ for v in video_objects], csv_filename)
        
        # 次の操作の確認
        next_action = input("\n続けて別の検索を行いますか？ (y/n): ").strip().lower()
        if next_action != 'y':
            print("アプリケーションを終了します。")
            break

def display_videos_table(videos):
    """動画情報をテーブル形式で表示"""
    # pandas DataFrameに変換
    data = []
    for video in videos:
        data.append({
            "ID": video.get("id", "")[:10] + "...",
            "クリエイター": video.get("author", {}).get("nickname", ""),
            "説明": video.get("desc", "")[:30] + "..." if len(video.get("desc", "")) > 30 else video.get("desc", ""),
            "再生数": format_number(video.get("stats", {}).get("playCount", 0)),
            "いいね数": format_number(video.get("stats", {}).get("diggCount", 0)),
            "コメント数": format_number(video.get("stats", {}).get("commentCount", 0)),
            "投稿日": datetime.fromtimestamp(video.get("createTime", 0)).strftime('%Y-%m-%d')
        })
    
    if not data:
        print("表示するデータがありません。")
        return
        
    df = pd.DataFrame(data)
    print("\n=== 取得した動画 ===")
    print(df.to_string(index=False))
    print("=" * 80)

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

async def main(mode="trend", search_term=None, count=10, sort_by="views", min_views=1000):
    """
    メイン実行関数（コマンドライン引数用）
    
    Args:
        mode: 検索モード（"trend", "user", "hashtag"）
        search_term: 検索する用語（ユーザー名またはハッシュタグ）
        count: 取得する動画数
        sort_by: ソート基準 ("views", "likes", "comments"等)
        min_views: 最小再生回数
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
    
    # APIクライアントの初期化（コマンドライン引数で上書き可能）
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
    
    # CSVに出力
    csv_filename = f"tiktok_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
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