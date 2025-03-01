"""
Google Maps Scraper ana sınıfı - Veri toplama seçenekleri eklendi
"""
import re
import time
import random
from urllib.parse import urlparse

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from .browser import BrowserManager
from .config import MAPS_CONFIG, CSS_SELECTORS
from .extractors.business_extractor import BusinessInfoExtractor
from .extractors.email_extractor import EmailExtractor
from utils.email_finder import EmailFinder

class MapsScraper:
    """
    Google Maps scraping işlemlerini yöneten sınıf
    """
    def __init__(self, queue_handler=None):
        """
        Args:
            queue_handler: İleti kuyruğu
        """
        self.queue_handler = queue_handler
        self.maps_browser = None
        self.email_finder = None
        self.processed_ids = set()  # İşlenmiş işletme kimliklerini takip etmek için set
        self.business_extractor = None
        self.data_options = {
            'collect_address': True,
            'collect_phone': True,
            'collect_website': True,
            'collect_email': True
        }
    
    def update_status(self, message):
        """İleti kuyruğuna durum mesajı ekle"""
        if self.queue_handler:
            self.queue_handler.put(("status", message))
    
    def update_progress(self, value):
        """İleti kuyruğuna ilerleme durumu ekle"""
        if self.queue_handler:
            self.queue_handler.put(("progress", value))
            
    def set_max_progress(self, value):
        """İleti kuyruğuna maksimum ilerleme değeri ekle"""
        if self.queue_handler:
            self.queue_handler.put(("max_progress", value))
    
    def initialize_browsers(self):
        """Tarayıcıları başlat"""
        # Ana tarayıcı (Maps için)
        self.maps_browser = BrowserManager(self.update_status)
        self.maps_browser.initialize()
        
        # E-posta bulucu
        self.email_finder = EmailFinder(
            browser=self.maps_browser,
            update_status_callback=self.update_status
        )
        
        # İşletme bilgisi çıkarıcı
        self.business_extractor = BusinessInfoExtractor(
            browser=self.maps_browser,
            update_status_callback=self.update_status
        )
    
    def close_browsers(self):
        """Tarayıcıları kapat"""
        if self.maps_browser:
            self.maps_browser.close()
            self.maps_browser = None
    
    def scrape(self, search_term, city, max_items=20, is_running_check=None, data_options=None):
        """
        Google Maps'te arama yap ve işletme bilgilerini topla
        
        Args:
            search_term: Aranacak terim
            city: Şehir
            max_items: Maksimum işletme sayısı
            is_running_check: Çalışma durumunu kontrol eden fonksiyon
            data_options: Hangi verilerin toplanacağını belirten seçenekler
            
        Returns:
            list: İşletme bilgilerini içeren liste
        """
        results = []
        processed = 0
        self.processed_ids = set()  # İşlenmiş işletme kimliklerini takip etme
        
        # Veri toplama seçeneklerini ayarla
        if data_options:
            self.data_options = data_options
            self.update_status(f"Toplanacak veriler: " + 
                             (", ".join([k.replace('collect_', '') for k, v in data_options.items() if v])))
        
        try:
            # Tarayıcıları başlat
            self.initialize_browsers()
            
            # Durum kontrolü
            if is_running_check and not is_running_check():
                self.update_status("İşlem iptal edildi.")
                return results
            
            # Google Maps'e git
            search_query = f"{search_term}+{city}"
            url = f"{MAPS_CONFIG['base_url']}{search_query}"
            self.update_status(f"Google Maps'e gidiliyor: {url}")
            
            try:
                self.maps_browser.driver.get(url)
                self.maps_browser.random_sleep()
            except Exception as e:
                self.update_status(f"Google Maps yükleme hatası: {str(e)}")
                raise Exception("Google Maps yüklenemedi.")
            
            # İlerleme durumunu ayarla
            self.set_max_progress(max_items)
            self.update_progress(processed)
            
            # Arama sonuçları listesini bul 
            business_list = self._find_business_list()
            if not business_list:
                self.update_status("İşletme listesi bulunamadı.")
                return results
                
            # Google 8'erli yükleme yapar, yeterince veri için sürekli kaydırma gerekli
            scroll_count = 0
            max_scroll_attempts = max(max_items * 3, 100)  # Maksimum kaydırma sayısı
            last_height = 0
            consecutive_no_change = 0
            
            while processed < max_items and scroll_count < max_scroll_attempts:
                # Durum kontrolü
                if is_running_check and not is_running_check():
                    self.update_status("İşlem iptal edildi.")
                    break
                
                # Mevcut işletme öğelerini bul
                items = self._find_business_items(business_list)
                if not items:
                    self.update_status("Hiç işletme bulunamadı, sayfayı yeniliyorum...")
                    try:
                        self.maps_browser.driver.refresh()
                        self.maps_browser.random_sleep()
                        business_list = self._find_business_list()
                        if not business_list:
                            break
                        continue
                    except:
                        break
                
                # İşletmeleri işle
                for item in items:
                    # Maksimum sayıya ulaşıldı mı kontrol et
                    if processed >= max_items:
                        break
                        
                    # Durdurma kontrolü
                    if is_running_check and not is_running_check():
                        self.update_status("İşlem iptal edildi.")
                        break
                    
                    # İşletmenin benzersiz kimliğini al
                    item_id = self._get_item_unique_id(item)
                    
                    # Önceden işlenmiş işletmeyi atla
                    if item_id in self.processed_ids:
                        continue
                    
                    # İşletme kimliğini işlenmiş olarak işaretle
                    self.processed_ids.add(item_id)
                    
                    # İşletmeyi işle
                    business_info = self._process_business_item(item, processed, max_items)
                    
                    if business_info and 'İsim' in business_info and business_info['İsim']:
                        # İşlenen işletmeyi kaydet
                        results.append(business_info)
                        processed += 1
                        self.update_progress(processed)
                
                # Daha fazla sonuç için aşağı kaydır
                try:
                    # İşletme listesinin mevcut yüksekliğini al
                    current_height = self.maps_browser.driver.execute_script(
                        "return arguments[0].scrollHeight", business_list
                    )
                    
                    # Eğer yükseklik değişmediyse, daha fazla kaydırma öncesi sayaç artır
                    if current_height == last_height:
                        consecutive_no_change += 1
                        
                        # Üst üste 3 kez yükseklik değişmediyse, daha fazla yükleme için bekleme ve daha güçlü kaydırma yap
                        if consecutive_no_change >= 3:
                            self.update_status("Daha fazla sonuç yüklemek için güçlü kaydırma yapılıyor...")
                            
                            # Güçlü kaydırma: Birkaç hızlı kaydırma yaparak tarayıcıyı tetikle
                            for _ in range(3):
                                self.maps_browser.driver.execute_script(
                                    "arguments[0].scrollTop += 500;", business_list
                                )
                                time.sleep(0.2)
                            
                            # Ardından daha uzun bekleme
                            self.maps_browser.random_sleep(1.5, 3)
                            
                            # Sayfayı yenile ve sıfırla (son çare olarak)
                            if consecutive_no_change >= 5:
                                self.update_status("Yeni sonuçlar yüklenemedi, sayfa yenileniyor...")
                                self.maps_browser.driver.refresh()
                                self.maps_browser.random_sleep()
                                business_list = self._find_business_list()
                                consecutive_no_change = 0
                                if not business_list:
                                    break
                                continue
                    else:
                        # Yükseklik değişti, sayacı sıfırla
                        consecutive_no_change = 0
                    
                    # Kaydırma işlemi
                    self.maps_browser.driver.execute_script(
                        "arguments[0].scrollTop += 300;", business_list
                    )
                    
                    # Yükleme için bekle (1-2 saniye)
                    self.maps_browser.random_sleep(1, 2)
                    
                    # Son yüksekliği güncelle
                    last_height = current_height
                    
                    # Kaydırma sayacını artır
                    scroll_count += 1
                    
                except Exception as scroll_err:
                    self.update_status(f"Kaydırma hatası: {str(scroll_err)}")
                    # Hata durumunda kısa bekleme
                    time.sleep(1)
                    
                    # Kritik hata durumunda sayfa yenile
                    try:
                        self.maps_browser.driver.refresh()
                        self.maps_browser.random_sleep()
                        business_list = self._find_business_list()
                        if not business_list:
                            break
                    except:
                        break
            
            # Bilgilendirme mesajı
            if processed >= max_items:
                self.update_status(f"Toplam {processed} işletme toplandı, hedef sayıya ulaşıldı.")
            else:
                self.update_status(f"Toplam {processed} işletme toplandı, hedef: {max_items}.")
                
            return results
            
        except Exception as e:
            self.update_status(f"Genel hata: {str(e)}")
            raise
        finally:
            # Tarayıcıları kapat
            self.close_browsers()
    
    def _get_item_unique_id(self, item):
        """
        İşletme öğesinin benzersiz kimliğini çıkarır
        Eğer kimlik bulunamazsa, metin içeriği + sıra numarası kullanır
        """
        try:
            # Google Maps bazen data-result-index özniteliğini kullanır
            result_index = item.get_attribute('data-result-index')
            if result_index:
                return f"idx_{result_index}"
                
            # Alternatif olarak data-item-id kullan
            item_id = item.get_attribute('data-item-id')
            if item_id:
                return f"id_{item_id}"
                
            # Veya aria-label özniteliğinden benzersiz bir değer çıkar
            aria_label = item.get_attribute('aria-label')
            if aria_label:
                # Sabit olmayan kısımları (örn. 4.5 yıldız gibi) temizle
                cleaned = re.sub(r'\d+\.\d+', '', aria_label)
                return f"aria_{cleaned[:50]}"  # İlk 50 karakter
                
            # Son çare olarak innerHTML hash'i oluştur
            inner_html = item.get_attribute('innerHTML')
            if inner_html:
                # Basit string hash (Python'un hash'i oturum arası değişir, o yüzden basit bir yöntem)
                simple_hash = sum(ord(c) for c in inner_html[:100])
                return f"html_{simple_hash}"
                
            # Hiçbiri yoksa metin içeriği kullan
            text = item.text.strip()
            if text:
                return f"text_{text[:30]}"
                
            # En son çare: DOM'daki pozisyon
            parent = item.find_element(By.XPATH, "./..")
            siblings = parent.find_elements(By.XPATH, "./*")
            index = siblings.index(item) if item in siblings else -1
            return f"pos_{index}"
            
        except Exception as e:
            # Hata durumunda, rastgele ID oluştur (işe yaramaz olabilir ama çalışmayı engelleme)
            rand_id = random.randint(1000, 9999)
            return f"err_{rand_id}"
    
    def _find_business_list(self):
        """İşletme listesini bul"""
        list_found = False
        attempts = 0
        max_attempts = MAPS_CONFIG['max_retry']
        
        while not list_found and attempts < max_attempts:
            for selector in CSS_SELECTORS["business_list"]:
                try:
                    business_list = WebDriverWait(self.maps_browser.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if business_list:
                        self.update_status(f"İşletme listesi bulundu: {selector}")
                        return business_list
                except:
                    continue
            
            self.update_status(f"İşletme listesi bulunamadı, yeniden deneniyor... ({attempts+1}/{max_attempts})")
            self.maps_browser.driver.refresh()
            self.maps_browser.random_sleep()
            attempts += 1
        
        return None
    
    def _find_business_items(self, business_list):
        """İşletme öğelerini bul"""
        if not business_list:
            return []
            
        items = []
        for selector in CSS_SELECTORS["business_items"]:
            try:
                items = business_list.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    self.update_status(f"{len(items)} işletme öğesi bulundu")
                    break
            except:
                continue
        
        return items
    
    def _process_business_item(self, item, processed, max_items):
        """
        İşletme öğesini işle - Geri gitmeyi engelleyen yeni yöntem
        Kullanıcının seçtiği veri toplama seçeneklerine göre işlem yapar
        
        Args:
            item: İşletme öğesi (WebElement)
            processed: İşlenen öğe sayısı
            max_items: Maksimum öğe sayısı
            
        Returns:
            dict: İşletme bilgileri
        """
        # İşletme adını al
        business_name = self.maps_browser.get_safe_text(item, "İsimsiz İşletme")
        if not business_name or business_name == "İsimsiz İşletme":
            # Alternatif yöntem
            try:
                business_name = item.get_attribute("aria-label") or "İsimsiz İşletme"
            except:
                pass
        
        self.update_status(f"İşletme seçiliyor: {business_name} (#{processed+1}/{max_items})")
        
        # Ana sekmenin durumunu kaydet
        try:
            # İşletmenin konumunu kaydet (sonraki işlemlerde kullanmak için)
            item_location = {}
            try:
                item_location = self.maps_browser.driver.execute_script(
                    "return arguments[0].getBoundingClientRect()", item
                )
            except:
                pass
                
            # Öğeye tıkla
            click_success = self.maps_browser.safe_click(item)
            if not click_success:
                self.update_status(f"Bu işletmeye tıklanamadı, atlıyorum.")
                return None
            
            self.maps_browser.random_sleep()  # Detay panelinin yüklenmesi için bekle
            
            # Panel yüklendiğini kontrol et
            panel_loaded = False
            for selector in CSS_SELECTORS["info_panel"]:
                try:
                    info_panel = WebDriverWait(self.maps_browser.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    panel_loaded = True
                    break
                except:
                    continue
            
            if not panel_loaded:
                self.update_status("Panel yüklenemedi, bir sonraki işletmeye geçiliyor...")
                return None
            
            # Veri seçeneklerini business_extractor'a ilet
            self.business_extractor.set_data_options(self.data_options)
            
            # İşletme bilgilerini topla
            business_info = self.business_extractor.extract_business_info()
            
            # ESC tuşuna basarak paneli kapat
            try:
                actions = ActionChains(self.maps_browser.driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
                self.maps_browser.random_sleep(0.5, 1.5)
            except Exception as e:
                self.update_status(f"Panel kapatma hatası: {str(e)}")
            
            return business_info
            
        except Exception as e:
            self.update_status(f"İşletme işleme hatası: {str(e)}")
            
            # Kritik hata durumunda ESC tuşuna basarak diyalogları kapatmayı dene
            try:
                actions = ActionChains(self.maps_browser.driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
                self.maps_browser.random_sleep(0.5, 1)
            except:
                pass
                
            return None