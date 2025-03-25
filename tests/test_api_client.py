import pytest
from datetime import datetime, timedelta
from app.api.client import TikTokAPIClient, APIError
from app.api.mock import MockTikTokAPI
from app.config import API_RATE_LIMIT

def test_rate_limit():
    """レート制限のテスト"""
    client = TikTokAPIClient()
    
    # 1000回のリクエストは許可される
    for _ in range(1000):
        client._check_rate_limit()
    
    # 1001回目で429エラーが発生する
    with pytest.raises(APIError) as exc_info:
        client._check_rate_limit()
    
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in str(exc_info.value)

def test_mock_rate_limit():
    client = MockTikTokAPI()
    for _ in range(1000):
        client._check_mock_rate_limit()
    
    with pytest.raises(APIError) as exc_info:
        client._check_mock_rate_limit()
    assert exc_info.value.status_code == 429
    assert "Mock rate limit exceeded" in str(exc_info.value)

class TestTikTokAPIClient:
    @pytest.fixture
    def api_client(self):
        return TikTokAPIClient(use_mock=True)

    def test_rate_limit(self, api_client):
        """レート制限のテスト"""
        # 1000回までのリクエストは許可
        for _ in range(API_RATE_LIMIT):
            api_client._check_rate_limit()
        
        # 1001回目で例外発生
        with pytest.raises(APIError) as exc_info:
            api_client._check_rate_limit()
        assert exc_info.value.status_code == 429

    @pytest.mark.asyncio
    async def test_get_trending_videos(self, api_client):
        """トレンド動画取得のテスト"""
        videos = await api_client.get_trending_videos(count=5)
        assert len(videos) == 5
        for video in videos:
            assert all(hasattr(video, attr) for attr in [
                'video_id', 'creator_id', 'view_count'
            ])

    def test_data_encryption(self, api_client):
        """データ暗号化のテスト"""
        from app.security.data_protection import DataProtection
        dp = DataProtection()
        test_data = {"video_id": "123", "views": 1000}
        encrypted = dp.encrypt_data(str(test_data))
        decrypted = dp.decrypt_data(encrypted)
        assert str(test_data) == decrypted 