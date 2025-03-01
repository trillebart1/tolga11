"""
İşletme bilgilerini çıkarma modülü - Veri seçenekleri destekli
"""
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from ..config import CSS_SELECTORS
from .phone_extractor import PhoneExtractor
from .address_extractor import AddressExtractor
from .email_extractor import EmailExtractor

class BusinessInfoExtractor:
    """
    İşletme detay sayfasından bilgileri çıkaran sınıf
    """
    def __init__(self, browser, update_status_callback=None):
        """
        Args:
            browser: BrowserManager nesnesi
            update_status_callback: Durum güncellemesi yapacak callback fonksiyonu
        """
        self.browser = browser
        self.update_status = update_status_callback or (lambda msg: None)
        
        # Alt çıkarıcılar
        self.phone_extractor = PhoneExtractor(browser, update_status_callback)
        self.address_extractor = AddressExtractor(browser, update_status_callback)
        self.email_extractor = EmailExtractor(browser, update_status_callback)
        
        # Veri toplama seçenekleri
        self.data_options = {
            'collect_address': True,
            'collect_phone': True,
            'collect_website': True,
            'collect_email': True
        }
        
    def set_data_options(self, options):
        """
        Veri toplama seçeneklerini ayarla
        
        Args:
            options: Veri toplama seçenek sözlüğü
        """
        if options:
            self.data_options = options
            
    def extract_business_info(self):
        """
        İşletme detay sayfasından bilgileri çıkartır
        
        Returns:
            dict: İşletme bilgileri
        """
        business_info = {}
        
        # Current URL (detay sayfası)
        try:
            business_info['Detay_URL'] = self.browser.driver.current_url
        except:
            business_info['Detay_URL'] = "Alınamadı"
        
        # İşletme adı - Geliştirilmiş yöntem
        try:
            business_name = self._extract_business_name()
            if business_name and not business_name.strip().startswith("http") and business_name != "Sonuçlar":
                business_info['İsim'] = business_name
            else:
                # URL'den işletme adı çıkarma yöntemi
                try:
                    url = business_info['Detay_URL']
                    if '/place/' in url:
                        # URL'den işletme adını çıkar
                        place_match = re.search(r'/place/([^/]+)', url)
                        if place_match:
                            url_name = place_match.group(1)
                            # URL formatını düzeltme
                            url_name = url_name.replace('+', ' ')
                            url_name = re.sub(r'%[\dA-F]{2}', ' ', url_name)
                            url_name = url_name.strip()
                            
                            if url_name and len(url_name) > 3:
                                business_info['İsim'] = url_name
                                self.update_status(f"İşletme adı URL'den alındı: {url_name}")
                            else:
                                business_info['İsim'] = "İsimsiz İşletme"
                        else:
                            business_info['İsim'] = "İsimsiz İşletme"
                    else:
                        business_info['İsim'] = "İsimsiz İşletme"
                except:
                    business_info['İsim'] = "İsimsiz İşletme"
        except Exception as e:
            business_info['İsim'] = "İsimsiz İşletme"
            self.update_status(f"İsim alınamadı: {str(e)}")
        
        # Adres için arama (eğer seçildiyse)
        business_info['Adres'] = "Bulunamadı"
        if self.data_options.get('collect_address', True):
            try:
                address = self.address_extractor.extract_address()
                business_info['Adres'] = address if address else "Bulunamadı"
            except Exception as e:
                self.update_status(f"Adres bulma hatası: {str(e)}")
        else:
            self.update_status("Adres toplamak seçilmedi, atlanıyor")
        
        # Telefon numarası için arama (eğer seçildiyse)
        business_info['Telefon'] = "Bulunamadı"
        if self.data_options.get('collect_phone', True):
            try:
                phone = self.phone_extractor.extract_phone_number()
                business_info['Telefon'] = phone if phone else "Bulunamadı"
            except Exception as e:
                self.update_status(f"Telefon bulma hatası: {str(e)}")
        else:
            self.update_status("Telefon toplamak seçilmedi, atlanıyor")
        
        # Website ve e-posta işlemleri
        business_info['Website'] = "Bulunamadı"
        business_info['E-postalar'] = "Bulunamadı"
        
        # Website ara (eğer seçildiyse)
        website = None
        if self.data_options.get('collect_website', True):
            try:
                website = self._extract_website_direct()
                
                # Website bulunamadıysa veya geçersizse
                if not website:
                    self.update_status("İşletmeye ait website bulunamadı")
                    business_info['Website'] = "Bulunamadı"
                else:
                    # URL'nin geçerliliğini kontrol et
                    valid_website = self._validate_website_url(website)
                    
                    if valid_website:
                        business_info['Website'] = website
                        self.update_status(f"Geçerli website bulundu: {website}")
                    else:
                        business_info['Website'] = "Bulunamadı"
                        self.update_status("Bulunan website geçerli değil")
            except Exception as e:
                self.update_status(f"Website arama hatası: {str(e)}")
        else:
            self.update_status("Website toplamak seçilmedi, atlanıyor")
            
        # E-posta ara (eğer seçildiyse ve geçerli bir website bulunduysa)
        if self.data_options.get('collect_email', True) and website and business_info['Website'] != "Bulunamadı":
            try:
                # E-posta toplama
                emails = self.email_extractor.extract_emails_from_website(website)
                business_info['E-postalar'] = '; '.join(emails) if emails else "Bulunamadı"
            except Exception as email_err:
                self.update_status(f"E-posta toplama hatası: {str(email_err)}")
                business_info['E-postalar'] = "Hata: Toplanamadı"
        else:
            if not self.data_options.get('collect_email', True):
                self.update_status("E-posta toplamak seçilmedi, atlanıyor")
            elif not website or business_info['Website'] == "Bulunamadı":
                self.update_status("Website bulunamadığı için e-posta araması yapılmıyor")
        
        # Zaman damgası ekle
        business_info['Tarih'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return business_info
    
    def _validate_website_url(self, url):
        """
        Website URL'sinin geçerli olup olmadığını kontrol eder
        
        Args:
            url: Kontrol edilecek URL
            
        Returns:
            bool: URL geçerliyse True, değilse False
        """
        if not url or not isinstance(url, str) or len(url) < 5:
            self.update_status(f"Çok kısa veya geçersiz URL: {url}")
            return False
            
        # http ile başlamayı kontrol et
        if not url.startswith('http'):
            self.update_status(f"URL http ile başlamıyor: {url}")
            return False
            
        # Yasaklı domainleri kontrol et
        excluded_domains = [
            'google.com', 'goo.gl', 'youtube.com', 'facebook.com', 'instagram.com',
            'twitter.com', 'linkedin.com', 'maps.app.goo.gl', 'yelp.com', 'tripadvisor.com',
            'maps.google'
        ]
        
        if any(domain in url.lower() for domain in excluded_domains):
            self.update_status(f"URL yasaklı domain içeriyor: {url}")
            return False
            
        return True
        
    def _extract_business_name(self):
        """
        İşletme adını birden fazla yöntemle çıkarır
        
        Returns:
            str: İşletme adı veya None
        """
        # Doğrudan bilgi panelinden başlık almaya çalış
        try:
            # En sık kullanılan başlık seçicileri
            main_selectors = [
                "h1.DUwDvf", 
                "h1.fontHeadlineLarge", 
                "h1.tAiQdd",
                "h1",
                "[role='main'] h1",
                "[role='dialog'] h1",
                ".fontHeadlineLarge",
                ".DUwDvf",
                ".x3AX1-LfntMc-header-title-title span"
            ]
            
            for selector in main_selectors:
                try:
                    elements = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and text != "Sonuçlar" and len(text) > 2:
                            self.update_status(f"İşletme adı bulundu (ana seçici): {text}")
                            return text
                except:
                    continue
            
            # Google Maps panelindeki bilgilerden başlık elementini ara
            panel_selectors = [
                ".fontHeadlineLarge", 
                ".w4GYrb span",
                ".UlEimf span", 
                ".qBF1Pd",
                ".qBF1Pd fontHeadlineLarge",
                ".lMbq3e h2"
            ]
            
            for selector in panel_selectors:
                try:
                    elements = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and text != "Sonuçlar" and len(text) > 2:
                            self.update_status(f"İşletme adı bulundu (panel): {text}")
                            return text
                except:
                    continue
            
            # Son çare: sayfa başlığı
            page_title = self.browser.driver.title
            if page_title:
                # "XXX - Google Haritalar" formatını temizle
                if " - Google" in page_title:
                    name = page_title.split(" - Google")[0].strip()
                    if name and len(name) > 2:
                        self.update_status(f"İşletme adı sayfa başlığından alındı: {name}")
                        return name
        
        except Exception as e:
            self.update_status(f"İşletme adı çıkarma hatası: {str(e)}")
            
        return None
    
    def _extract_website_direct(self):
        """
        Doğrudan websiteyi çıkarmaya çalışır, hızlı ve güvenli bir yöntem
        
        Returns:
            str: Website URL'si veya None
        """
        website = None
        
        # Yöntem 1: Standart seçicilerle arama
        try:
            for selector in CSS_SELECTORS["website"]:
                try:
                    website_elements = self.browser.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in website_elements:
                        try:
                            href = elem.get_attribute('href')
                            if href and href.startswith('http'):
                                website = href
                                self.update_status(f"Website bulundu (seçici): {website}")
                                return website
                        except:
                            continue
                except:
                    continue
        except:
            pass
        
        # Yöntem 2: Web sitesi açıkça belirtilen tüm elementleri ara
        try:
            # Website içeren elementleri farklı yöntemlerle ara
            site_elements = []
            
            # CSS seçicileri ile ara
            try:
                site_elements.extend(self.browser.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "button[data-item-id='authority'], a[data-item-id='authority'], a[aria-label*='web'], button[aria-label*='web']"
                ))
            except:
                pass
                
            # XPath ile alternatif arama
            try:
                site_elements.extend(self.browser.driver.find_elements(
                    By.XPATH, 
                    "//button[contains(text(), 'Web') or contains(., 'Site') or contains(@aria-label, 'web')]"
                ))
            except:
                pass
                
            # Her bulunan eleman için tıklama/içerik çıkarma dene
            for elem in site_elements:
                try:
                    # Elemanda href varsa doğrudan al
                    href = elem.get_attribute('href')
                    if href and href.startswith('http'):
                        website = href
                        self.update_status(f"Website doğrudan bulundu: {website}")
                        return website
                    
                    # Yok ve tıklanabilirse tıkla
                    elem.click()
                    self.browser.random_sleep(1, 2)
                    
                    # Yeni pencere açıldı mı kontrol et
                    current_handles = self.browser.driver.window_handles
                    if len(current_handles) > 1:
                        # Yeni pencereye geç
                        main_window = self.browser.driver.current_window_handle
                        
                        # Yeni açılan her pencereyi kontrol et
                        for handle in current_handles:
                            if handle != main_window:
                                try:
                                    self.browser.driver.switch_to.window(handle)
                                    new_url = self.browser.driver.current_url
                                    
                                    # URL'yi kontrol et
                                    if new_url and new_url.startswith('http'):
                                        website = new_url
                                    
                                    # Her koşulda yeni pencereyi kapat
                                    self.browser.driver.close()
                                except:
                                    pass
                        
                        # Ana pencereye geri dön
                        self.browser.driver.switch_to.window(main_window)
                        
                        if website:
                            self.update_status(f"Website yeni pencerede bulundu: {website}")
                            return website
                except:
                    continue
        except:
            pass
        
        # Website bulunamadı
        self.update_status("Website bulunamadı")
        return None