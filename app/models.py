# データモデル定義
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class VideoData:
    """TikTok動画のデータを格納するクラス"""
    
    video_id: str
    creator_id: str
    creator_name: str
    video_url: str
    view_count: int
    like_count: int
    comment_count: int
    share_count: int
    post_date: datetime
    fetch_date: datetime
    description: Optional[str] = None
    music_title: Optional[str] = None
    music_author: Optional[str] = None
    hashtags: Optional[str] = None
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'VideoData':
        """APIレスポンスからVideoDataオブジェクトを作成"""
        # ハッシュタグの抽出
        desc = data.get("desc", "")
        hashtags = " ".join([tag for tag in desc.split() if tag.startswith("#")])
        
        # Unix時間からdatetimeへの変換
        create_time = datetime.fromtimestamp(data.get("createTime", 0))
        
        return cls(
            video_id=data.get("id", ""),
            creator_id=data.get("author", {}).get("uniqueId", ""),
            creator_name=data.get("author", {}).get("nickname", ""),
            video_url=data.get("video", {}).get("playAddr", ""),
            view_count=data.get("stats", {}).get("playCount", 0),
            like_count=data.get("stats", {}).get("diggCount", 0),
            comment_count=data.get("stats", {}).get("commentCount", 0),
            share_count=data.get("stats", {}).get("shareCount", 0),
            post_date=create_time,
            fetch_date=datetime.now(),
            description=desc,
            music_title=data.get("music", {}).get("title", ""),
            music_author=data.get("music", {}).get("authorName", ""),
            hashtags=hashtags
        )

    def remove_sensitive_data(self):
        """機密データを削除"""
        self.creator_id = self._anonymize_id(self.creator_id)
        self.creator_name = "Anonymous"
        return self
    
    @staticmethod
    def _anonymize_id(id_str):
        """IDを匿名化"""
        return f"user_{hash(id_str) % 10000:04d}"
