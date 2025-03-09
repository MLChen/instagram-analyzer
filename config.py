import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    # 基礎路徑
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # Instagram 設定
    INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME')
    INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

    # 瀏覽器設定
    HEADLESS_MODE = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')

    # 資料庫設定
    DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, 'data', 'instagram.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 爬蟲設定
    DELAY_BETWEEN_REQUESTS = int(os.getenv('DELAY_BETWEEN_REQUESTS', 2))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))

    # 日誌設定
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', os.path.join(BASE_DIR, 'logs', 'app.log'))

    @staticmethod
    def init_app(app):
        # 確保必要目錄存在
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    HEADLESS_MODE = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
