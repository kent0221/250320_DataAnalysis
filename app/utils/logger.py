import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

def setup_logger():
    logger = logging.getLogger('tiktok_analytics')
    logger.setLevel(logging.INFO)

    # ログディレクトリの作成
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)

    # ファイルハンドラの設定
    log_file = os.path.join(
        log_dir, 
        f'app_{datetime.now().strftime("%Y%m%d")}.log'
    )
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024*1024,
        backupCount=5
    )
    
    # フォーマットの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger 