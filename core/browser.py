"""
Tarayıcı yönetimi sınıfı
"""
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

from .config import BROWSER_CONFIG, CSS_SELECTORS

class BrowserManager:
    """
    Tarayıcı işlemlerini yöneten sınıf
    """
    def __init__(self, update_status_callback=None):
        """
        Tarayıcı yöneticisini başlat
        
        Args:
            update_status_callback: Durum güncellemesi yapacak callback fonksiyonu
        """
        self.driver = None
        self.update_status = update_status_callback or (lambda msg: None)
        
    def initialize(self):
        """
        Tarayıcıyı başlat ve ayarla
        """
        if self.driver is not None:
            self.close()
            
        # Chrome seçeneklerini ayarla
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={BROWSER_CONFIG['user_agent']}")
        options.add_argument(f"window-size={BROWSER_CONFIG['window_size'][0]},{BROWSER_CONFIG['window_size'][1]}")
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-notifications')
        options.add_argument('--log-level=3')
        
        # Headless mod gerekirse ekle
        if BROWSER_CONFIG['headless']:
            options.add_argument('--headless')
        
        # Chrome tarayıcıyı başlat
        self.driver = webdriver.Chrome(options=options)
        
        # Timeout ayarları
        self.driver.set_page_load_timeout(BROWSER_CONFIG['timeout'])
        
        # Bot tespitini engelle
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        self.update_status("Tarayıcı başlatıldı")
        return self.driver
    
    def close(self):
        """
        Tarayıcıyı kapat
        """
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                
    def random_sleep(self, min_time=None, max_time=None):
        """
        Rastgele bekleme süresi
        """
        min_time = min_time or BROWSER_CONFIG['sleep_min']
        max_time = max_time or BROWSER_CONFIG['sleep_max']
        time.sleep(random.uniform(min_time, max_time))
        
    def open_new_window(self, url):
        """
        Yeni bir tarayıcı penceresi açar
        
        Args:
            url: Açılacak URL
            
        Returns:
            WebDriver: Yeni açılan pencereyi kontrol eden WebDriver
        """
        if not self.driver:
            return None
            
        try:
            # Mevcut pencere tanımlayıcısını sakla
            original_window = self.driver.current_window_handle
            
            # Yeni pencere aç
            self.driver.execute_script("window.open('', '_blank');")
            
            # Yeni pencereye geç
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # URL'yi yükle
            self.driver.get(url)
            self.random_sleep()
            
            return original_window
        except Exception as e:
            self.update_status(f"Yeni pencere açma hatası: {str(e)}")
            return None
            
    def close_current_and_switch_to(self, original_window):
        """
        Mevcut pencereyi kapatır ve belirtilen pencereye geri döner
        
        Args:
            original_window: Geri dönülecek pencere tanımlayıcısı
        """
        if not self.driver:
            return
            
        try:
            # Mevcut pencereyi kapat
            self.driver.close()
            
            # Orijinal pencereye geri dön
            self.driver.switch_to.window(original_window)
            self.random_sleep(1, 2)
        except Exception as e:
            self.update_status(f"Pencere kapatma hatası: {str(e)}")
    
    def safely_navigate_back(self, original_url=None):
        """
        Güvenli bir şekilde geri navigasyonu sağlar
        
        Args:
            original_url: Başarısızlık durumunda kullanılacak URL
            
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        if not self.driver:
            return False
            
        try:
            # Önce back butonunu dene
            back_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, ", ".join(CSS_SELECTORS["back_buttons"])
            )
            
            if back_buttons and len(back_buttons) > 0:
                try:
                    self.update_status("Geri düğmesi bulundu, tıklanıyor...")
                    # Try with ActionChains
                    ActionChains(self.driver).move_to_element(back_buttons[0]).click().perform()
                    self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
                    return True
                except:
                    try:
                        # Try with JavaScript
                        self.update_status("ActionChains başarısız, JavaScript ile deneniyor...")
                        self.driver.execute_script("arguments[0].click();", back_buttons[0])
                        self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
                        return True
                    except:
                        pass
        except Exception as e:
            self.update_status(f"Geri butonu hatası: {str(e)}")
            
        # JavaScript back kullan
        try:
            self.update_status("JavaScript history.back() kullanılıyor...")
            self.driver.execute_script("window.history.back();")
            self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
            return True
        except Exception as e:
            self.update_status(f"JavaScript geri hatası: {str(e)}")
            
        # Driver back kullan
        try:
            self.update_status("Driver.back() kullanılıyor...")
            self.driver.back()
            self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
            return True
        except Exception as e:
            self.update_status(f"Driver geri hatası: {str(e)}")
            
        # Son çare olarak orijinal URL'ye git
        if original_url:
            try:
                self.update_status(f"Orijinal URL'ye geri dönülüyor: {original_url}")
                self.driver.get(original_url)
                self.random_sleep()
                return True
            except Exception as e:
                self.update_status(f"URL yeniden yükleme hatası: {str(e)}")
        
        return False
        
    def get_safe_text(self, element, default=""):
        """
        Güvenli bir şekilde element metnini almak için yardımcı fonksiyon
        
        Args:
            element: Metin alınacak web elementi
            default: Başarısızlık durumunda dönecek değer
            
        Returns:
            str: Element metni veya varsayılan değer
        """
        try:
            if element:
                return element.text
            return default
        except:
            return default

    def safe_find_element(self, by, value, timeout=5, default=None):
        """
        Güvenli bir şekilde element bulmak için yardımcı fonksiyon
        
        Args:
            by: Seçim yöntemi (By.ID, By.CSS_SELECTOR vb.)
            value: Seçim değeri
            timeout: Maksimum bekleme süresi
            default: Başarısızlık durumunda dönecek değer
            
        Returns:
            WebElement: Bulunan element veya varsayılan değer
        """
        if not self.driver:
            return default
            
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except:
            return default
    
    def safe_click(self, element, retry_count=3):
        """
        Güvenli bir şekilde elemente tıklama yapar
        
        Args:
            element: Tıklanacak web elementi
            retry_count: Başarısız durumda deneme sayısı
            
        Returns:
            bool: İşlemin başarılı olup olmadığı
        """
        if not element or not self.driver:
            return False
            
        for attempt in range(retry_count):
            try:
                # Scroll element into view
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", 
                    element
                )
                self.random_sleep(0.5, 1)
                
                # Try action chains first
                ActionChains(self.driver).move_to_element(element).click().perform()
                self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
                return True
            except:
                try:
                    # Try JavaScript click
                    self.driver.execute_script("arguments[0].click();", element)
                    self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
                    return True
                except:
                    try:
                        # Try direct click
                        element.click()
                        self.random_sleep(BROWSER_CONFIG['sleep_click_min'], BROWSER_CONFIG['sleep_click_max'])
                        return True
                    except:
                        if attempt < retry_count - 1:
                            self.random_sleep(0.5, 1)  # Kısa bekle ve tekrar dene
        
        return False