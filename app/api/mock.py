# モックデータを提供するモジュール
import json
import os
import random
from datetime import datetime, timedelta
import time
from typing import List, Dict, Any, Optional
from app.api.client import APIError  # client.pyからAPIErrorをインポート

# モックデータファイルのパス
MOCK_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'mock_videos.json')

def load_mock_data() -> List[Dict[str, Any]]:
    """モックデータをJSONファイルから読み込む"""
    try:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "mock_videos.json")
        with open(data_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"モックデータ読み込みエラー: {e}")
        # 基本的なモックデータを返す
        return generate_mock_data(30)

def generate_mock_data(count: int = 30) -> List[Dict[str, Any]]:
    """モックデータを生成する関数"""
    videos = []
    creators = ["人気クリエイター", "おもしろクリエイター", "料理の達人", "ダンサー", "メイク職人"]
    hashtags = [["#ダンス", "#流行"], ["#コメディ", "#笑える"], ["#簡単料理", "#時短レシピ"], 
                ["#トレンド", "#おすすめ"], ["#メイク", "#美容"]]
    
    now = datetime.now()
    
    for i in range(count):
        creator_idx = i % len(creators)
        hashtag_idx = i % len(hashtags)
        
        # 再生回数は10万〜100万でランダム
        views = random.randint(100000, 1000000)
        
        # いいね、コメント、シェアは再生回数に対する比率でランダム
        likes = int(views * random.uniform(0.1, 0.3))
        comments = int(views * random.uniform(0.01, 0.05))
        shares = int(views * random.uniform(0.05, 0.15))
        
        # 投稿日時は過去7日以内でランダム
        days_ago = random.randint(0, 7)
        post_date = now - timedelta(days=days_ago)
        
        videos.append({
            "id": f"71{i:012d}",
            "desc": f"モックデータ説明文 {' '.join(hashtags[hashtag_idx])}",
            "createTime": int(post_date.timestamp()),
            "author": {
                "uniqueId": f"creator_{i}",
                "nickname": creators[creator_idx]
            },
            "stats": {
                "diggCount": likes,
                "commentCount": comments,
                "shareCount": shares,
                "playCount": views
            },
            "music": {
                "title": f"人気曲{i+1}",
                "authorName": f"アーティスト{i+1}"
            },
            "video": {
                "playAddr": f"https://example.com/video{i+1}"
            }
        })
    
    # ファイルに保存
    try:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        data_path = os.path.join(data_dir, "mock_videos.json")
        
        with open(data_path, 'w', encoding='utf-8') as file:
            json.dump(videos, file, ensure_ascii=False, indent=2)
        
        print(f"生成したモックデータを {data_path} に保存しました")
    except Exception as e:
        print(f"モックデータ保存エラー: {e}")
    
    return videos

def get_mock_trending_videos(count: int = 20, sort_by: str = "views", min_views: int = 0) -> List[Dict[str, Any]]:
    """
    モックのトレンド動画を取得する関数
    
    Args:
        count: 取得する動画数
        sort_by: ソート基準 ("views", "likes", "comments", "shares")
        min_views: 最小再生回数
    
    Returns:
        動画データのリスト
    """
    print(f"モックデータからトレンド動画を取得します... ソート: {sort_by}, 最小再生回数: {min_views}")
    
    # モックデータの読み込み
    videos = load_mock_data()
    
    # 最小再生回数でフィルタリング
    filtered_videos = [v for v in videos if v["stats"]["playCount"] >= min_views]
    
    # ソート
    if sort_by == "views":
        filtered_videos.sort(key=lambda x: x["stats"]["playCount"], reverse=True)
    elif sort_by == "likes":
        filtered_videos.sort(key=lambda x: x["stats"]["diggCount"], reverse=True)
    elif sort_by == "comments":
        filtered_videos.sort(key=lambda x: x["stats"]["commentCount"], reverse=True)
    elif sort_by == "shares":
        filtered_videos.sort(key=lambda x: x["stats"]["shareCount"], reverse=True)
    
    # 指定の数まで切り詰める
    result_videos = filtered_videos[:count]
    
    # 遅延をシミュレート（API呼び出しのような体験）
    time.sleep(0.5)
    
    print(f"{len(result_videos)}件のトレンド動画を取得しました")
    return result_videos

def get_mock_user_videos(username: str, count: int = 20, sort_by: str = "views") -> List[Dict[str, Any]]:
    """
    モックの特定ユーザーの動画を取得する関数
    
    Args:
        username: TikTokのユーザー名
        count: 取得する動画数
        sort_by: ソート基準 ("views", "likes", "comments", "date")
        
    Returns:
        動画データのリスト
    """
    print(f"モックデータから {username} の動画を取得します... ソート: {sort_by}")
    
    # モックデータの読み込み
    all_videos = load_mock_data()
    
    # ユーザー名に基づくフィルタリング
    # ここでは簡易的に一部一致としています
    filtered_videos = [v for v in all_videos if username.lower() in v["author"]["uniqueId"].lower() or 
                      username.lower() in v["author"]["nickname"].lower()]
    
    # データが少ない場合は追加生成
    if len(filtered_videos) < count:
        extra_videos = []
        now = datetime.now()
        
        for i in range(count - len(filtered_videos)):
            views = random.randint(50000, 800000)
            post_date = now - timedelta(days=random.randint(0, 30))
            
            extra_videos.append({
                "id": f"user_{username}_{i:04d}",
                "desc": f"{username}の動画 #{i+1} #クリエイター",
                "createTime": int(post_date.timestamp()),
                "author": {
                    "uniqueId": username,
                    "nickname": f"{username}のプロフィール名"
                },
                "stats": {
                    "diggCount": int(views * random.uniform(0.1, 0.3)),
                    "commentCount": int(views * random.uniform(0.01, 0.05)),
                    "shareCount": int(views * random.uniform(0.03, 0.1)),
                    "playCount": views
                },
                "music": {
                    "title": f"{username}が使用した曲{i+1}",
                    "authorName": "BGMアーティスト"
                },
                "video": {
                    "playAddr": f"https://example.com/{username}/video{i+1}"
                }
            })
        
        filtered_videos.extend(extra_videos)
    
    # ソート
    if sort_by == "views":
        filtered_videos.sort(key=lambda x: x["stats"]["playCount"], reverse=True)
    elif sort_by == "likes":
        filtered_videos.sort(key=lambda x: x["stats"]["diggCount"], reverse=True)
    elif sort_by == "comments":
        filtered_videos.sort(key=lambda x: x["stats"]["commentCount"], reverse=True)
    elif sort_by == "date":
        filtered_videos.sort(key=lambda x: x["createTime"], reverse=True)
    
    # 指定の数まで切り詰める
    result_videos = filtered_videos[:count]
    
    # 遅延をシミュレート
    time.sleep(0.5)
    
    print(f"{len(result_videos)}件の {username} の動画を取得しました")
    return result_videos

def get_mock_hashtag_videos(hashtag, count=20, sort_by="views", min_views=0):
    """
    モックの特定ハッシュタグの動画を取得する関数
    
    Args:
        hashtag: ハッシュタグ名（#なし）。空の場合は全てのハッシュタグを対象とする
        count: 取得する動画数
        sort_by: ソート基準 ("views", "likes", "comments")
        min_views: 最小再生回数
        
    Returns:
        動画データのリスト
    """
    if not hashtag:
        print(f"モックデータから全てのハッシュタグの動画を取得します... ソート: {sort_by}, 最小再生回数: {min_views}")
    else:
        print(f"モックデータから #{hashtag} の動画を取得します... ソート: {sort_by}, 最小再生回数: {min_views}")
    
    # モックデータの読み込み
    all_videos = load_mock_data()
    
    # ハッシュタグに基づくフィルタリング
    if hashtag:
        tag = f"#{hashtag}"
        filtered_videos = [v for v in all_videos if tag in v["desc"] and v["stats"]["playCount"] >= min_views]
    else:
        # ハッシュタグが指定されていない場合は、再生回数のみでフィルタリング
        filtered_videos = [v for v in all_videos if v["stats"]["playCount"] >= min_views]
    
    # データが少ない場合は追加生成
    if len(filtered_videos) < count:
        extra_videos = []
        now = datetime.now()
        
        creators = ["人気クリエイター", "おもしろクリエイター", "料理の達人", "ダンサー", "メイク職人"]
        
        for i in range(count - len(filtered_videos)):
            creator_idx = i % len(creators)
            views = random.randint(max(min_views, 10000), 1000000)
            post_date = now - timedelta(days=random.randint(0, 14))
            
            hashtag_text = f"#{hashtag}" if hashtag else "#人気 #トレンド"
            
            extra_videos.append({
                "id": f"hashtag_{hashtag or 'trend'}_{i:04d}",
                "desc": f"{hashtag_text} 関連動画 #{i+1}",
                "createTime": int(post_date.timestamp()),
                "author": {
                    "uniqueId": f"creator_{creator_idx}",
                    "nickname": creators[creator_idx]
                },
                "stats": {
                    "diggCount": int(views * random.uniform(0.1, 0.3)),
                    "commentCount": int(views * random.uniform(0.01, 0.05)),
                    "shareCount": int(views * random.uniform(0.03, 0.1)),
                    "playCount": views
                },
                "music": {
                    "title": f"#{hashtag or 'トレンド'}で人気の曲{i+1}",
                    "authorName": "トレンドアーティスト"
                },
                "video": {
                    "playAddr": f"https://example.com/hashtag/{hashtag or 'trend'}/video{i+1}"
                }
            })
        
        filtered_videos.extend(extra_videos)
    
    # ソート
    if sort_by == "views":
        filtered_videos.sort(key=lambda x: x["stats"]["playCount"], reverse=True)
    elif sort_by == "likes":
        filtered_videos.sort(key=lambda x: x["stats"]["diggCount"], reverse=True)
    elif sort_by == "comments":
        filtered_videos.sort(key=lambda x: x["stats"]["commentCount"], reverse=True)
    elif sort_by == "date":
        filtered_videos.sort(key=lambda x: x["createTime"], reverse=True)
    
    # 指定の数まで切り詰める
    result_videos = filtered_videos[:count]
    
    # 遅延をシミュレート
    time.sleep(0.5)
    
    if not hashtag:
        print(f"{len(result_videos)}件のトレンド動画を取得しました")
    else:
        print(f"{len(result_videos)}件の #{hashtag} の動画を取得しました")
    
    return result_videos

def get_mock_video_by_id(video_id):
    """
    モックデータから特定IDの動画を取得する関数
    
    Args:
        video_id: 取得する動画のIDまたはURL
        
    Returns:
        動画データ（見つからない場合はNone）
    """
    print(f"モックデータから動画ID/URL: {video_id} の動画を取得します...")
    
    # モックデータの読み込み
    all_videos = load_mock_data()
    
    # IDに一致する動画を検索
    for video in all_videos:
        # IDでの検索
        if str(video.get("id", "")) == str(video_id):
            print(f"動画ID: {video_id} の動画を取得しました")
            return video
        
        # URLでの検索
        if video.get("video", {}).get("playAddr", "") == video_id:
            print(f"動画URL: {video_id} の動画を取得しました")
            return video
    
    print(f"動画ID/URL: {video_id} の動画は見つかりませんでした")
    
    # 見つからない場合はランダムに生成したモックデータを返す（デモ用）
    if video_id.isdigit():
        # ダミーデータを生成して返す
        import random
        from datetime import datetime, timedelta
        
        view_count = random.randint(50000, 1000000)
        now = datetime.now()
        post_date = now - timedelta(days=random.randint(1, 30))
        
        mock_video = {
            "id": video_id,
            "desc": f"動画ID {video_id} のコンテンツ #テスト #サンプル",
            "createTime": int(post_date.timestamp()),
            "author": {
                "uniqueId": f"user_{random.randint(1000, 9999)}",
                "nickname": f"サンプルユーザー{random.randint(1, 100)}"
            },
            "stats": {
                "diggCount": int(view_count * random.uniform(0.1, 0.3)),
                "commentCount": int(view_count * random.uniform(0.01, 0.05)),
                "shareCount": int(view_count * random.uniform(0.03, 0.1)),
                "playCount": view_count
            },
            "music": {
                "title": f"サンプル曲{random.randint(1, 50)}",
                "authorName": f"サンプルアーティスト{random.randint(1, 20)}"
            },
            "video": {
                "playAddr": f"https://example.com/video/{video_id}"
            }
        }
        print(f"動画ID: {video_id} のダミーデータを生成しました")
        return mock_video
    
    return None

class MockTikTokAPI:
    """モックTikTok APIクライアント"""
    
    # レート制限をシミュレートする機能を追加
    def __init__(self):
        self.requests_count = 0
        self.last_reset = datetime.now()

    def _check_mock_rate_limit(self):
        current_time = datetime.now()
        if (current_time - self.last_reset).seconds >= 60:
            self.requests_count = 0
            self.last_reset = current_time
        
        self.requests_count += 1
        if self.requests_count > 1000:
            raise APIError("Mock rate limit exceeded", 429)

    def get_mock_trending_videos(self, count=10, min_views=0, sort_by="views"):
        """モックのトレンド動画を取得する関数"""
        # レート制限チェックの追加が必要
        self._check_mock_rate_limit()
        return get_mock_trending_videos(count, sort_by, min_views)
    
    def get_mock_user_videos(self, username, count=20, sort_by="views"):
        """モックの特定ユーザーの動画を取得する関数"""
        self._check_mock_rate_limit()
        return get_mock_user_videos(username, count, sort_by)
        
    def get_mock_hashtag_videos(self, hashtag, count=20, sort_by="views", min_views=0):
        """モックの特定ハッシュタグの動画を取得する関数"""
        self._check_mock_rate_limit()
        return get_mock_hashtag_videos(hashtag, count, sort_by, min_views)
        
    def get_mock_video_by_id(self, video_id):
        """モックの特定動画IDから動画を取得する関数"""
        self._check_mock_rate_limit()
        return get_mock_video_by_id(video_id)
