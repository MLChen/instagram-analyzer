import os
from datetime import datetime
import logging
from flask import Flask
from app.crawler.instagram import InstagramCrawler
from app.database.models import db, Following, FollowHistory
from app.web.routes import web
from config import config

def create_app():
    """創建 Flask 應用"""
    app = Flask(__name__)
    
    # 載入配置
    config_name = os.getenv('FLASK_ENV', 'development')
    app_config = config[config_name]
    app.config.from_object(app_config)
    
    # 確保數據庫目錄存在
    db_path = os.path.abspath(getattr(app_config, 'DATABASE_PATH', 'data/instagram.db'))
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    # 設置絕對路徑的數據庫 URI
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    print(f"Database path: {db_path}")
    print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # 確保日誌目錄存在
    log_file = getattr(app_config, 'LOG_FILE', 'logs/app.log')
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # 初始化資料庫
    db.init_app(app)
    with app.app_context():
        db.create_all()
    
    # 註冊藍圖
    app.register_blueprint(web)
    
    return app

def setup_logger(app_config):
    """設定日誌"""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # 確保日誌目錄存在
    log_file = getattr(app_config, 'LOG_FILE', 'logs/app.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 檔案處理器
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def update_following_status(crawler, app, logger):
    """更新追蹤狀態"""
    with app.app_context():
        # 獲取追蹤清單
        following_list = crawler.get_following_list()
        if not following_list:
            logger.error("獲取追蹤清單失敗")
            return False

        # 更新所有用戶狀態為非活動
        Following.query.update({Following.current_status: False})
        db.session.commit()
        
        # 處理每個追蹤的用戶
        for username in following_list:
            user = Following.query.filter_by(username=username).first()
            
            if user:
                # 更新現有用戶
                if not user.current_status:
                    # 用戶重新開始追蹤
                    history = FollowHistory(
                        username=username,
                        event_type='new_follow'
                    )
                    db.session.add(history)
                user.current_status = True
                user.last_seen = datetime.utcnow()
            else:
                # 新用戶
                user = Following(
                    username=username,
                    current_status=True
                )
                db.session.add(user)
                
                history = FollowHistory(
                    username=username,
                    event_type='new_follow'
                )
                db.session.add(history)
            
            db.session.commit()
            
            # 檢查是否互相追蹤
            follows_me = crawler.check_follows_me(username)
            user.follows_me = follows_me
            db.session.commit()
        
        # 記錄取消追蹤的用戶
        unfollowed_users = Following.query.filter_by(current_status=False).all()
        for user in unfollowed_users:
            history = FollowHistory(
                username=user.username,
                event_type='unfollow'
            )
            db.session.add(history)
        
        db.session.commit()
        return True

def run_crawler():
    """執行爬蟲"""
    # 創建應用配置
    config_name = os.getenv('FLASK_ENV', 'development')
    app_config = config[config_name]
    
    # 初始化日誌
    logger = setup_logger(app_config)
    logger.info("開始執行 Instagram 追蹤分析")
    
    # 創建應用
    app = create_app()
    
    try:
        # 初始化爬蟲
        crawler = InstagramCrawler(app.config)
        crawler.init_driver()
        
        # 登入
        if not crawler.login():
            logger.error("登入失敗")
            return
        
        # 更新追蹤狀態
        if update_following_status(crawler, app, logger):
            logger.info("追蹤狀態更新完成")
        else:
            logger.error("追蹤狀態更新失敗")
            
    except Exception as e:
        logger.error(f"執行過程中發生錯誤: {str(e)}")
        raise
    
    finally:
        if crawler:
            crawler.close()
            logger.info("已關閉瀏覽器")

def test_check_follows_me(username):
    """測試特定帳號的追蹤檢查"""
    app = create_app()  # 創建應用以獲得正確的配置
    logger = setup_logger(app.config)
    crawler = None
    
    try:
        crawler = InstagramCrawler(app.config)
        crawler.init_driver()
        
        if not crawler.login():
            logger.error("登入失敗")
            return
        
        result = crawler.check_follows_me(username)
        logger.info(f"測試結果: {username} {'有' if result else '沒有'}追蹤我")
        
    except Exception as e:
        logger.error(f"測試過程中發生錯誤: {str(e)}")
        raise
    
    finally:
        if crawler:
            crawler.close()

def generate_static_report(app_config, output_path=None):
    """生成靜態HTML報告"""
    from app.report.generator import ReportGenerator
    
    try:
        # 創建應用上下文
        app = create_app()
        
        # 初始化報告生成器
        generator = ReportGenerator(app)
        
        # 生成報告
        report_path = generator.generate_report(output_path) if output_path else generator.generate_report()
        print(f"報告已生成: {report_path}")
        
        # 在瀏覽器中打開報告
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(report_path)}")
        return True
    except Exception as e:
        print(f"生成報告時發生錯誤: {str(e)}")
        return False

def main():
    """主程式"""
    import sys
    
    if len(sys.argv) > 1:
        # 創建應用配置
        config_name = os.getenv('FLASK_ENV', 'development')
        app_config = config[config_name]
        
        if sys.argv[1] == 'crawl':
            # 執行爬蟲
            run_crawler()
        elif sys.argv[1] == 'test' and len(sys.argv) > 2:
            # 測試特定帳號
            test_check_follows_me(sys.argv[2])
        elif sys.argv[1] == 'generate-report':
            # 生成靜態報告
            output_path = sys.argv[2] if len(sys.argv) > 2 else None
            generate_static_report(app_config, output_path)
        else:
            print("可用命令:")
            print("  crawl              - 執行 Instagram 追蹤分析爬蟲")
            print("  test <username>    - 測試檢查特定帳號是否互相追蹤")
            print("  generate-report    - 生成靜態 HTML 報告")
            print("  generate-report <output_path>  - 生成報告到指定路徑")
    else:
        # 啟動網頁服務
        app = create_app()
        app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
