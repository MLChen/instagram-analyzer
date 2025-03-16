import time
import sys
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

class InstagramCrawler:
    def __init__(self, config):
        self.config = config
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.setup_logger()

    def setup_logger(self):
        """設定日誌"""
        log_level = self.config['LOG_LEVEL'] if 'LOG_LEVEL' in self.config else 'INFO'
        self.logger.setLevel(getattr(logging, log_level))
        
        # 檔案處理器
        log_file = self.config['LOG_FILE'] if 'LOG_FILE' in self.config else 'logs/app.log'
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def init_driver(self):
        """初始化瀏覽器"""
        try:
            self.logger.info("開始初始化瀏覽器...")
            chrome_options = webdriver.ChromeOptions()
            headless_mode = self.config['HEADLESS_MODE'] if 'HEADLESS_MODE' in self.config else False
            if headless_mode:
                chrome_options.add_argument('--headless=new')
                self.logger.info("使用 headless 模式")
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-notifications')
            chrome_options.add_argument('--lang=zh-TW')
            chrome_options.add_argument('--window-size=1920,1080')

            # 處理 ChromeDriver 路徑
            chrome_driver_path = self.config.get('CHROME_DRIVER_PATH', None)
            if chrome_driver_path and chrome_driver_path.strip() and chrome_driver_path != '# 可選，預設自動下載':
                self.logger.info("使用指定的 ChromeDriver")
                service = Service(chrome_driver_path)
            else:
                self.logger.info("自動下載並使用最新版本的 ChromeDriver")
                service = Service(ChromeDriverManager().install())

            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            self.driver.implicitly_wait(10)
            self.logger.info("瀏覽器初始化完成")
            return self.driver
            
        except Exception as e:
            self.logger.error(f"初始化瀏覽器失敗: {str(e)}")
            raise

    def login(self):
        """登入 Instagram"""
        try:
            self.logger.info("開始登入 Instagram...")
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)

            self.logger.info("等待登入表單出現...")
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
            )
            self.logger.info("找到使用者名稱輸入框")
            username = self.config['INSTAGRAM_USERNAME'] if 'INSTAGRAM_USERNAME' in self.config else ''
            password = self.config['INSTAGRAM_PASSWORD'] if 'INSTAGRAM_PASSWORD' in self.config else ''
            
            if not username or not password:
                self.logger.error("未設定 Instagram 帳號或密碼")
                return False
                
            username_input.clear()
            username_input.send_keys(username)
            
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            self.logger.info("找到密碼輸入框")
            password_input.clear()
            password_input.send_keys(password)
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            self.logger.info("點擊登入按鈕")
            login_button.click()
            
            time.sleep(5)
            try:
                not_now_button = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button._a9--._ap36._a9_1"))
                )
                self.logger.info("點擊「稍後再試」按鈕")
                not_now_button.click()
            except:
                self.logger.info("沒有出現額外的彈窗")
                
            self.logger.info("登入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"登入失敗: {str(e)}")
            return False

    def scroll_dialog(self):
        """使用 JavaScript 滾動對話框直到沒有新內容"""
        try:
            # 等待對話框和滾動容器出現
            dialog = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            time.sleep(3)  # 等待內容載入

            no_change_count = 0
            prev_count = 0
            attempt = 0
            
            while True:
                attempt += 1
                self.logger.info(f"執行第 {attempt} 次滾動")
                
                # 執行滾動和獲取結果
                # 執行滾動和獲取結果
                scroll_result = self.driver.execute_script("""
                    const dialog = arguments[0];
                    
                    // 尋找所有可能的滾動容器
                    const allContainers = Array.from(dialog.querySelectorAll('div'));
                    const scrollContainers = allContainers.filter(div => {
                        const style = window.getComputedStyle(div);
                        const hasScroll = style.overflowY === 'auto' || style.overflowY === 'scroll';
                        const hasContent = div.scrollHeight > div.clientHeight;
                        return hasScroll && hasContent;
                    });
                    
                    // 按照容器大小排序
                    scrollContainers.sort((a, b) => b.scrollHeight - a.scrollHeight);
                    
                    // 記錄診斷信息
                    console.log('找到的滾動容器:', scrollContainers.map(c => ({
                        class: c.className,
                        height: c.scrollHeight,
                        visible: c.clientHeight
                    })));
                    
                    // 選擇最合適的容器
                    const container = scrollContainers[0];
                    if (!container) {
                        return { success: false, error: 'No suitable scroll container found' };
                    }
                    
                    // 執行滾動
                    const oldScrollTop = container.scrollTop;
                    container.scrollTop += 500;
                    
                    return {
                        success: true,
                        container: container.className,
                        itemCount: dialog.querySelectorAll('a[role="link"]').length,
                        oldHeight: oldScrollTop,
                        newHeight: container.scrollTop,
                        scrollHeight: container.scrollHeight,
                        clientHeight: container.clientHeight
                    };
                """, dialog)
                    
                if not scroll_result.get('success'):
                    self.logger.error(f"滾動錯誤: {scroll_result.get('error')}")
                    return False
                    
                current_count = scroll_result['itemCount']
                new_height = scroll_result['newHeight']
                container_type = scroll_result.get('container', 'unknown')
                
                self.logger.info(f"使用容器類型: {container_type}, 當前項目數: {current_count}")
                
                if current_count > prev_count:
                    self.logger.info(f"發現新項目: {current_count - prev_count} 個")
                    no_change_count = 0
                    prev_count = current_count
                else:
                    no_change_count += 1
                    self.logger.info(f"沒有新項目 ({no_change_count}/3)")
                
                if no_change_count >= 3:
                    self.logger.info("執行最終滾動檢查")
                    self.driver.execute_script("""
                        const scroll_box = arguments[0].querySelector('div._aano');
                        if (scroll_box) {
                            scroll_box.scrollTop = scroll_box.scrollHeight;
                        }
                    """, dialog)
                    time.sleep(3)
                    break
                
                # 等待內容載入
                wait_time = 1.5
                time.sleep(wait_time)
                
            return True
            
        except Exception as e:
            self.logger.error(f"滾動過程錯誤: {str(e)}")
            return False

    def get_following_list(self):
        """獲取追蹤清單"""
        try:
            username = self.config['INSTAGRAM_USERNAME'] if 'INSTAGRAM_USERNAME' in self.config else ''
            if not username:
                self.logger.error("未設定 Instagram 帳號")
                return []
                
            self.logger.info("開始獲取追蹤清單...")
            self.driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(5)

            self.logger.info("尋找追蹤中按鈕...")
            following_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/following')]"))
            )
            self.logger.info(f"找到追蹤中連結: {following_link.text}")
            following_count = int(''.join(filter(str.isdigit, following_link.text)))
            self.logger.info(f"追蹤人數: {following_count}")
            following_link.click()
            time.sleep(3)

            dialog = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
            )
            
            if dialog:
                # 開始滾動並蒐集，最多嘗試3次
                for attempt in range(3):
                    self.logger.info(f"開始第 {attempt + 1} 次嘗試蒐集追蹤名單...")
                    
                    # 重置滾動位置
                    self.driver.execute_script("""
                        const dialog = document.querySelector('div[role="dialog"]');
                        if (dialog) {
                            const container = dialog.querySelector('div._aano > div');
                            if (container) container.scrollTop = 0;
                        }
                    """)
                    time.sleep(2)
                    
                    # 進行滾動載入
                    if not self.scroll_dialog():  # 移除最大嘗試次數限制
                        self.logger.warning("滾動過程出現問題，重試...")
                        continue
                    
                    # 收集用戶名稱
                    elements = dialog.find_elements(By.CSS_SELECTOR, "div[role='dialog'] a[role='link']")
                    following_list = []
                    usernames_found = set()
                    
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and '/following' not in href:
                            username = href.split('/')[-2]
                            if username and username not in usernames_found:
                                usernames_found.add(username)
                                following_list.append(username)
                    
                    # 檢查蒐集品質
                    collection_ratio = len(following_list) / following_count
                    self.logger.info(f"蒐集效率: {collection_ratio:.2%} ({len(following_list)}/{following_count})")
                    
                    if collection_ratio >= 0.9:  # 蒐集到90%以上就認為成功
                        self.logger.info(f"已成功蒐集 {len(following_list)} 個追蹤帳號")
                        return following_list
                    else:
                        self.logger.warning(f"蒐集數量不足，已蒐集: {len(following_list)}，目標: {following_count}")
                
                self.logger.error("多次嘗試後仍無法蒐集足夠的追蹤名單")
                return []  # 返回空列表表示蒐集失敗
            else:
                self.logger.error("找不到正確的對話框")
                return []

        except Exception as e:
            self.logger.error(f"獲取追蹤清單失敗: {str(e)}")
            return []

    def check_follows_me(self, username):
        """檢查用戶是否追蹤我"""
        try:
            self.logger.info(f"檢查用戶 {username} 是否追蹤我...")
            self.driver.get(f"https://www.instagram.com/{username}/")
            time.sleep(3)

            # 檢查我的用戶名是否已設定
            my_username = self.config['INSTAGRAM_USERNAME'] if 'INSTAGRAM_USERNAME' in self.config else ''
            if not my_username:
                self.logger.error("未設定 Instagram 帳號")
                return False

            # 先尋找追蹤數量的連結或按鈕
            try:
                # 嘗試多種可能的選擇器
                selectors = [
                    "//a[contains(@href, '/following')]/span/span",  # 一般用戶頁面的連結
                    "//a[contains(@href, '/following')]",            # 備用連結格式
                    "//div[contains(@class, '_ab8w')]//span",       # 數字容器
                    "//button[.//span[contains(text(), '追蹤中')]]"  # 按鈕內的文字
                ]
                
                following_element = None
                following_count = 0
                
                for selector in selectors:
                    try:
                        following_element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        # 找到元素後，獲取數字
                        text = following_element.text
                        self.logger.info(f"找到追蹤資訊元素: {text}")
                        if text:
                            count = int(''.join(filter(str.isdigit, text.split('\n')[0])))
                            if count >= 0:
                                following_count = count
                                break
                    except (TimeoutException, ValueError, NoSuchElementException):
                        continue
                        
                if following_count == 0:
                    self.logger.info(f"用戶 {username} 沒有追蹤任何人，因此確定沒有追蹤我")
                    return False
                    
                self.logger.info(f"用戶 {username} 總共追蹤了 {following_count} 人")
                
                # 點擊追蹤清單
                if following_element:
                    self.logger.info(f"開始檢查 {username} 的追蹤列表...")
                    following_element.click()
                    time.sleep(5)  # 增加等待時間確保對話框完全載入
                    
                    # 檢查對話框是否出現
                    dialog = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
                    )
                    
                    # 增加短暫等待確保內容載入
                    time.sleep(2)
                    
                    # 檢查前5個用戶
                    first_users = dialog.find_elements(By.XPATH, ".//a[@role='link' and contains(@href, '/')]")[:5]
                    if not first_users:
                        self.logger.error("無法找到用戶列表")
                        return False
                        
                    my_profile = f"instagram.com/{my_username}/"
                    follows_me = any(my_profile in user.get_attribute('href').lower() for user in first_users)
                    
                    self.logger.info(f"用戶 {username} {'有' if follows_me else '沒有'}追蹤我")
                    return follows_me
                else:
                    self.logger.error("無法點擊追蹤清單")
                    return False
                    
            except (TimeoutException, NoSuchElementException) as e:
                self.logger.error(f"檢查過程發生錯誤: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"檢查用戶 {username} 是否追蹤我時失敗: {str(e)}")
            return False

    def close(self):
        """關閉瀏覽器"""
        if self.driver:
            self.logger.info("關閉瀏覽器")
            self.driver.quit()
