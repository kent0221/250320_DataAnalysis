# TikTok API公式クライアント
import os
import requests
from datetime import datetime, timedelta
import json
import time
from app.config import (
    USE_MOCK_API, TIKTOK_API_KEY, TIKTOK_API_SECRET, 
    TIKTOK_ACCESS_TOKEN, API_RATE_LIMIT, API_RATE_WINDOW, API_BASE_URL
)
from app.api.exceptions import APIError
from app.api.mock import MockTikTokAPI
import logging
from typing import Dict, Any, Optional, List
import webbrowser
from urllib.parse import urlencode

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

class TikTokAPIClient:
    """TikTok公式APIのクライアントクラス"""
    
    REQUIRED_SCOPES = [
        "user.info.basic",      # 基本情報取得のみ
        "video.list",           # 動画一覧取得
        "video.list.basic",     # 動画基本情報
    ]
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("TikTokAPIClientが初期化されました")
        
        self.use_mock = os.getenv("USE_MOCK_API", "true").lower() == "true"
        self.mock_client = MockTikTokAPI() if self.use_mock else None
        self.base_url = API_BASE_URL
        self.api_key = os.getenv("TIKTOK_API_KEY")
        self.redirect_uri = os.getenv("REDIRECT_URI")
        
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

    async def fetch_videos(self, settings: Dict) -> List[Dict]:
        """設定に基づいてデータを取得"""
        try:
            if settings["type"] == "hashtag":
                if not settings.get("hashtag"):
                    # ハッシュタグが空の場合はトレンド動画を取得
                    return await self.get_trending_videos(
                        count=settings["count"],
                        min_views=settings.get("min_views", 0),
                        sort_by=settings.get("sort_by", "views")
                    )
                return await self.get_hashtag_videos(
                    hashtag=settings["hashtag"],
                    count=settings["count"],
                    min_views=settings.get("min_views", 0),
                    sort_by=settings.get("sort_by", "views")
                )
            elif settings["type"] == "trend":
                return await self.get_trending_videos(
                    count=settings["count"],
                    min_views=settings["min_views"],
                    min_likes=settings.get("min_likes", 0),
                    sort_by=settings.get("sort_by", "views"),
                    days_ago=settings.get("time_range")
                )
            elif settings["type"] == "video":
                videos = []
                for video_id in settings["video_ids"]:
                    video = await self.get_video_by_id(video_id)
                    if video:
                        videos.append(video)
                return videos
                
        except Exception as e:
            print(f"データ取得エラー: {e}")
            return []

    async def get_trending_videos(self, count=10, min_views=1000, min_likes=0, sort_by="views", days_ago=None):
        """トレンド動画の取得"""
        if self.use_mock:
            return self.mock_client.get_mock_trending_videos(
                count=count,
                min_views=min_views,
                sort_by=sort_by
            )
        
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
    
    async def get_hashtag_videos(self, hashtag, count=20, sort_by="views", min_views=0):
        """ハッシュタグ付きの動画を取得する関数"""
        if self.use_mock:
            # モックデータを使用
            from app.api.mock import get_mock_hashtag_videos
            return get_mock_hashtag_videos(hashtag, count, sort_by, min_views)
        
        try:
            endpoint = "video/search/"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # APIリクエストのボディ
            data = {
                "query": {
                    "and": [
                        {
                            "operation": "EQ",
                            "field_name": "hashtag_name",
                            "field_values": [hashtag]
                        }
                    ]
                },
                "max_count": count
            }
            
            self._check_rate_limit()
            response = await self.session.post(
                f"{self.base_url}{endpoint}",
                headers=headers,
                json=data
            )
            
            if response.status != 200:
                raise APIError(f"ハッシュタグ検索エラー: {response.status}", response.status)
            
            result = await response.json()
            videos = result.get("data", {}).get("videos", [])
            
            # データの変換とフィルタリング
            formatted_videos = self._format_video_data(videos, min_views)
            
            # ソート処理
            return self._sort_videos(formatted_videos, sort_by)[:count]
            
        except Exception as e:
            logger.error(f"ハッシュタグ動画取得エラー: {e}")
            return []

    async def get_video_by_id(self, video_id):
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

    async def authenticate(self):
        """TikTok認証処理"""
        try:
            if self.use_mock:
                return True
            
            # 認証パラメータの設定
            auth_params = {
                "client_key": self.api_key,
                "redirect_uri": self.redirect_uri,
                "response_type": "code",
                "scope": "user.info.basic,video.list",
                "state": "your-state-value"
            }
            
            # 認証URLの構築
            auth_url = "https://www.tiktok.com/auth/authorize/?" + urlencode(auth_params)
            
            # ブラウザでTikTokログインページを開く
            print("\nOpening TikTok login page in your browser...")
            webbrowser.open(auth_url)
            
            # ユーザーが認証を完了するまで待機
            input("\nAfter completing authentication in the browser, press Enter to continue...")
            
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
