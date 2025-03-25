# TikTok API公式クライアント
import os
import requests
from datetime import datetime, timedelta
import json
import time
from app.config import (
    USE_MOCK_API, TIKTOK_API_KEY, TIKTOK_API_SECRET, 
    TIKTOK_ACCESS_TOKEN, API_RATE_LIMIT, API_RATE_WINDOW
)
import logging
from typing import Dict, Any, Optional

# ロガーの設定
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

class APIError(Exception):
    """TikTok API固有のエラー"""
    def __init__(self, message, status_code=None, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

class TikTokAPIClient:
    """TikTok公式APIのクライアントクラス"""
    
    REQUIRED_SCOPES = [
        "user.info.basic",      # 基本情報取得のみ
        "video.list",           # 動画一覧取得
        "video.list.basic",     # 動画基本情報
    ]
    
    def __init__(self, use_mock=None):
        self.logger = logging.getLogger(__name__)
        self.logger.info("TikTokAPIClientが初期化されました")
        
        # use_mockのデフォルト値をconfigから取得
        if use_mock is None:
            use_mock = USE_MOCK_API
            
        self.use_mock = use_mock
        
        # モックモードの場合、mock_clientを初期化
        if self.use_mock:
            from app.api.mock import MockTikTokAPI
            self.mock_client = MockTikTokAPI()
        else:
            self.api_key = TIKTOK_API_KEY
            self.api_secret = TIKTOK_API_SECRET
            self.access_token = TIKTOK_ACCESS_TOKEN
        
        self._initialize_rate_limit()
    
    def _initialize_rate_limit(self):
        """レート制限の初期化"""
        self.rate_limit = {
            "requests": 0,
            "reset_time": datetime.now()
        }
        logger.debug("レート制限が初期化されました")
    
    def _check_rate_limit(self):
        """レート制限をチェック（600回/分に修正）"""
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=API_RATE_WINDOW)
        
        if current_time >= self.rate_limit["reset_time"]:
            self.rate_limit["requests"] = 0
            self.rate_limit["reset_time"] = current_time + timedelta(seconds=API_RATE_WINDOW)
            logger.debug("レート制限カウンターがリセットされました")
            
        if self.rate_limit["requests"] >= 600:  # TikTok APIの制限に合わせて修正
            logger.warning("レート制限に達しました")
            raise APIError("Rate limit exceeded", status_code=429)
            
        self.rate_limit["requests"] += 1
    
    def _handle_api_error(self, response):
        """APIエラーのハンドリング"""
        error_codes = {
            400: "不正なリクエストです",
            401: "認証に失敗しました",
            403: "アクセス権限がありません",
            404: "リソースが見つかりません",
            429: "APIレート制限を超過しました",
            500: "TikTok APIサーバーエラー"
        }
        
        if response.status_code != 200:
            error_message = error_codes.get(
                response.status_code, 
                f"APIエラー: {response.status_code}"
            )
            raise APIError(
                message=error_message,
                status_code=response.status_code,
                error_code=response.json().get("error_code")
            )

    async def get_trending_videos(self, count=10, sort_by="views", min_views=1000, min_likes=0, days_ago=None):
        """
        トレンド動画を取得する関数（非同期ではなく同期的に動作）
        
        Args:
            count: 取得する動画数
            sort_by: ソート基準 ("views", "likes", "comments", "shares")
            min_views: 最小再生回数
            min_likes: 最小いいね数
            days_ago: 過去の日数
            
        Returns:
            動画データのリスト
        """
        if self.use_mock:
            # モッククライアントも同期的なメソッドを呼び出す
            return self.mock_client.get_mock_trending_videos(count, min_views, sort_by)
        
        # 実際のAPI呼び出し
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        params = {"fields": "id,desc,createTime,stats,video.playAddr,author.uniqueId"}
        
        data = {
            "max_count": count,
            "filters": {
                "stats.viewCount": {"gte": min_views},
                "like_count": {"gte": min_likes}
            },
            "sort_type": sort_by
        }
        
        try:
            self._check_rate_limit()
            response = requests.post(
                f"{self.base_url}video/list/",
                headers=headers,
                json=data
            )
            
            self._handle_api_error(response)
            
            data = response.json()
            videos = data.get("data", {}).get("videos", [])
            
            # データの変換とフィルタリング
            formatted_videos = []
            for video in videos:
                if video.get("view_count", 0) >= min_views:
                    formatted_videos.append({
                        "id": video.get("id"),
                        "desc": video.get("video_description", ""),
                        "createTime": datetime.fromisoformat(video.get("create_time")).timestamp(),
                        "author": {
                            "uniqueId": video.get("author", {}).get("username", ""),
                            "nickname": video.get("author", {}).get("display_name", "")
                        },
                        "stats": {
                            "diggCount": video.get("like_count", 0),
                            "commentCount": video.get("comment_count", 0),
                            "shareCount": video.get("share_count", 0),
                            "playCount": video.get("view_count", 0)
                        },
                        "music": {
                            "title": video.get("music_info", {}).get("title", ""),
                            "authorName": video.get("music_info", {}).get("author", "")
                        },
                        "video": {
                            "playAddr": video.get("embed_link", "")
                        }
                    })
            
            # ソート
            if sort_by == "views":
                formatted_videos.sort(key=lambda x: x["stats"]["playCount"], reverse=True)
            elif sort_by == "likes":
                formatted_videos.sort(key=lambda x: x["stats"]["diggCount"], reverse=True)
            elif sort_by == "comments":
                formatted_videos.sort(key=lambda x: x["stats"]["commentCount"], reverse=True)
            elif sort_by == "shares":
                formatted_videos.sort(key=lambda x: x["stats"]["shareCount"], reverse=True)
            
            return formatted_videos[:count]
            
        except APIError as e:
            logger.error(f"API Error: {e.message}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise APIError("予期せぬエラーが発生しました", 500)
    
    def get_user_videos(self, username, count=20, sort_by="views"):
        """
        特定ユーザーの動画を取得する関数
        
        Args:
            username: TikTokのユーザー名
            count: 取得する動画数
            sort_by: ソート基準 ("views", "likes", "comments", "date")
            
        Returns:
            動画データのリスト
        """
        if self.use_mock:
            # モックデータを使用
            from app.api.mock import get_mock_user_videos
            return get_mock_user_videos(username, count, sort_by)
        
        # 実際のAPI呼び出し
        try:
            # ユーザー情報を取得
            user_endpoint = "user/info/"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            params = {
                "username": username,
                "fields": "user_id,username,display_name"
            }
            
            user_response = requests.get(
                f"{self.base_url}{user_endpoint}",
                headers=headers,
                params=params
            )
            
            if user_response.status_code != 200:
                print(f"ユーザー情報取得エラー: ステータスコード {user_response.status_code}")
                print(f"レスポンス: {user_response.text}")
                return []
            
            user_data = user_response.json()
            user_id = user_data.get("data", {}).get("user", {}).get("user_id")
            
            if not user_id:
                print(f"ユーザーID取得エラー: {username}")
                return []
            
            # ユーザーの動画を取得
            video_endpoint = "video/list/"
            params = {
                "user_id": user_id,
                "fields": "id,video_description,create_time,like_count,comment_count,share_count,view_count,music_info,author,embed_link",
                "max_count": count
            }
            
            video_response = requests.get(
                f"{self.base_url}{video_endpoint}",
                headers=headers,
                params=params
            )
            
            if video_response.status_code != 200:
                print(f"動画取得エラー: ステータスコード {video_response.status_code}")
                print(f"レスポンス: {video_response.text}")
                return []
            
            data = video_response.json()
            videos = data.get("data", {}).get("videos", [])
            
            # データの変換
            formatted_videos = []
            for video in videos:
                formatted_videos.append({
                    "id": video.get("id"),
                    "desc": video.get("video_description", ""),
                    "createTime": datetime.fromisoformat(video.get("create_time")).timestamp(),
                    "author": {
                        "uniqueId": video.get("author", {}).get("username", ""),
                        "nickname": video.get("author", {}).get("display_name", "")
                    },
                    "stats": {
                        "diggCount": video.get("like_count", 0),
                        "commentCount": video.get("comment_count", 0),
                        "shareCount": video.get("share_count", 0),
                        "playCount": video.get("view_count", 0)
                    },
                    "music": {
                        "title": video.get("music_info", {}).get("title", ""),
                        "authorName": video.get("music_info", {}).get("author", "")
                    },
                    "video": {
                        "playAddr": video.get("embed_link", "")
                    }
                })
            
            # エンゲージメント率の計算
            for video in formatted_videos:
                stats = video["stats"]
                plays = stats["playCount"]
                likes = stats["diggCount"]
                comments = stats["commentCount"]
                shares = stats["shareCount"]
                
                video["engagement_rate"] = (likes + comments + shares) / plays if plays > 0 else 0
                video["like_rate"] = likes / plays if plays > 0 else 0
            
            # ソート
            if sort_by == "views":
                formatted_videos.sort(key=lambda x: x["stats"]["playCount"], reverse=True)
            elif sort_by == "likes":
                formatted_videos.sort(key=lambda x: x["stats"]["diggCount"], reverse=True)
            elif sort_by == "comments":
                formatted_videos.sort(key=lambda x: x["stats"]["commentCount"], reverse=True)
            elif sort_by == "date":
                formatted_videos.sort(key=lambda x: x["createTime"], reverse=True)
            
            return formatted_videos[:count]
            
        except Exception as e:
            print(f"ユーザー動画取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_hashtag_videos(self, hashtag, count=20, sort_by="views", min_views=0):
        """
        特定ハッシュタグの動画を取得する関数
        
        Args:
            hashtag: ハッシュタグ名（#なし）
            count: 取得する動画数
            sort_by: ソート基準 ("views", "likes", "comments")
            min_views: 最小再生回数
            
        Returns:
            動画データのリスト
        """
        if self.use_mock:
            # モックデータを使用
            from app.api.mock import get_mock_hashtag_videos
            return get_mock_hashtag_videos(hashtag, count, sort_by, min_views)
        
        # 実際のAPI呼び出し
        try:
            endpoint = "video/search/"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            params = {
                "query": f"#{hashtag}",
                "fields": "id,video_description,create_time,like_count,comment_count,share_count,view_count,music_info,author,embed_link",
                "max_count": count * 2  # より多く取得して後でフィルタリング
            }
            
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                print(f"ハッシュタグ検索エラー: ステータスコード {response.status_code}")
                print(f"レスポンス: {response.text}")
                return []
            
            data = response.json()
            videos = data.get("data", {}).get("videos", [])
            
            # データの変換とフィルタリング
            formatted_videos = []
            for video in videos:
                if video.get("view_count", 0) >= min_views:
                    formatted_videos.append({
                        "id": video.get("id"),
                        "desc": video.get("video_description", ""),
                        "createTime": datetime.fromisoformat(video.get("create_time")).timestamp(),
                        "author": {
                            "uniqueId": video.get("author", {}).get("username", ""),
                            "nickname": video.get("author", {}).get("display_name", "")
                        },
                        "stats": {
                            "diggCount": video.get("like_count", 0),
                            "commentCount": video.get("comment_count", 0),
                            "shareCount": video.get("share_count", 0),
                            "playCount": video.get("view_count", 0)
                        },
                        "music": {
                            "title": video.get("music_info", {}).get("title", ""),
                            "authorName": video.get("music_info", {}).get("author", "")
                        },
                        "video": {
                            "playAddr": video.get("embed_link", "")
                        }
                    })
            
            # ソート
            if sort_by == "views":
                formatted_videos.sort(key=lambda x: x["stats"]["playCount"], reverse=True)
            elif sort_by == "likes":
                formatted_videos.sort(key=lambda x: x["stats"]["diggCount"], reverse=True)
            elif sort_by == "comments":
                formatted_videos.sort(key=lambda x: x["stats"]["commentCount"], reverse=True)
            
            # ハッシュタグ分析データの追加
            result_videos = formatted_videos[:count]
            
            return result_videos
            
        except Exception as e:
            print(f"ハッシュタグ動画取得エラー: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_video_by_id(self, video_id):
        """
        特定の動画IDから動画を取得する関数
        
        Args:
            video_id: 取得する動画のID
            
        Returns:
            動画データ（取得できない場合はNone）
        """
        if self.use_mock:
            # モックデータを使用
            from app.api.mock import get_mock_video_by_id
            return get_mock_video_by_id(video_id)
            
        # 以下は公式API使用時の実装
        try:
            url = f"{self.base_url}video/query/"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "filters": {
                    "video_ids": [video_id]
                },
                "fields": ["id", "title", "video_description", "duration", "cover_image_url", 
                          "share_url", "embed_link", "like_count", "comment_count", "share_count", "view_count"]
            }
            
            self._check_rate_limit()  # レート制限チェックの追加
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 429:
                raise APIError("Rate limit exceeded", 429, response)
            elif response.status_code != 200:
                raise APIError(f"API error: {response.text}", response.status_code, response)
            
            result = response.json()
            
            if not result.get("data"):
                raise APIError("No data returned from API", response.status_code)
            return result["data"]
                
        except APIError as e:
            raise  # APIエラーは上位で処理
        except Exception as e:
            raise APIError(f"Unexpected error: {str(e)}", None)

    def _handle_error_response(self, response):
        """APIエラーレスポンスを処理"""
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            if response.status_code == 429:
                error_message = "Rate limit exceeded: Please wait before making more requests"
            elif response.status_code == 401:
                error_message = "Authentication failed: Please check your API credentials"
            elif response.status_code == 403:
                error_message = "Access forbidden: Please check your API permissions"
            raise APIError(error_message, response.status_code, response)
        except ValueError:
            raise APIError("Invalid API response", response.status_code, response)
