import os
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# データベース設定を追加
DB_HOST = os.getenv("DB_HOST", "db")  # デフォルト値としてdocker-compose のサービス名
DB_PORT = os.getenv("DB_PORT", 3306)
DB_USER = os.getenv("DB_USER", "tiktok_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "tiktok_analysis")

# API設定
USE_MOCK_API = os.getenv("USE_MOCK_API", "true").lower() == "true"
TIKTOK_API_KEY = os.getenv("TIKTOK_API_KEY", "")
TIKTOK_API_SECRET = os.getenv("TIKTOK_API_SECRET", "")
TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")

# API制限設定を公式の制限に合わせる
API_RATE_LIMIT = 600  # 1分あたりのリクエスト上限（TikTok公式の制限）
API_RATE_WINDOW = 60  # レート制限のウィンドウ（秒）

# データ保持期間
DATA_RETENTION_DAYS = 30

# プライバシー設定
ANONYMIZE_DATA = True
ENCRYPT_STORAGE = True

# 追加が必要な設定
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:3000/auth/callback")  # 開発環境用 

# アプリケーション情報の更新
APP_NAME = "TikTok Data Analytics Tool"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = """
個人利用のためのTikTok動画分析ツール。
以下の機能を提供します：
- 動画統計データの取得
- ローカルデータベースへの保存
- CSV形式でのデータエクスポート
"""

# API設定
API_BASE_URL = "https://open.tiktokapis.com/v2/"
API_TIMEOUT = 30  # seconds

# データベース設定
DB_CHARSET = "utf8mb4"
DB_COLLATION = "utf8mb4_unicode_ci"

# セキュリティ設定
MIN_PASSWORD_LENGTH = 12
HASH_ALGORITHM = "bcrypt"

# プライバシー設定の強化
PRIVACY_POLICY_URL = "https://github.com/kent0221/250320_DataAnalysis/blob/master/docs/PRIVACY.md"
TERMS_URL = "https://github.com/kent0221/250320_DataAnalysis/blob/master/docs/TERMS.md"
SECURITY_POLICY_URL = "https://github.com/kent0221/250320_DataAnalysis/blob/master/docs/SECURITY.md" 