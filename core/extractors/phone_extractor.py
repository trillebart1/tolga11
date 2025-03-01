"""
Telefon numarası çıkarma modülü
"""
from selenium.webdriver.common.by import By
from ..config import CSS_SELECTORS, REGEX_PATTERNS

class PhoneExtractor:
    """
    Telefon numarası çıkarma sınıfı
    """
    def __init__(self, browser, update_status_callback=None):
        """
        Args:
            browser: BrowserManager nesnesi
            update_status_callback: Durum güncellemesi yapacak callback fonksiyonu
        """
        self.browser = browser
        self.update_status = update_status_callback or (lambda msg: None)
    
    def extract_phone_number(self):
        """
        Telefon numarasını bulmak için geliştirilmiş yöntem
        
        Returns:
            str: Bulunan telefon numarası veya None
        """
        phone = None
        
        # Yöntem 1: Standart CSS seçicileriyle arama
        phone_selector = ", ".join(CSS_SELECTORS["phone"])
        phone_elements = self.browser.driver.find_elements(By.CSS_SELECTOR, phone_selector)
        
        for phone_elem in phone_elements:
            try:
                # Seçenek 1: aria-label özniteliği
                aria_label = phone_elem.get_attribute('aria-label')
                if aria_label and ('telefon' in aria_label.lower() or 'ara' in aria_label.lower()):
                    # Telefon: +90 555 123 4567 formatını temizle
                    phone = aria_label.replace('Telefon: ', '').strip()
                    self.update_status(f"Telefon bulundu (aria-label): {phone}")
                    break
                    
                # Seçenek 2: Element metni
                text = phone_elem.text
                if text and REGEX_PATTERNS["phone"].search(text) and len(text) < 30:
                    phone = text
                    self.update_status(f"Telefon bulundu (metin): {phone}")
                    break
            except:
                continue
        
        # Yöntem 2: Telefon ikonuyla ilişkili buttonlar
        if not phone:
            try:
                # Telefon simgesi içeren butonları bul
                phone_buttons = self.browser.driver.find_elements(
                    By.CSS_SELECTOR, "button[data-item-id^='phone'], [data-tooltip='Telefon numarasını kopyala']"
                )
                
                for btn in phone_buttons:
                    try:
                        text = btn.text.strip()
                        if text and REGEX_PATTERNS["phone"].search(text):
                            phone = text
                            self.update_status(f"Telefon bulundu (telefon butonu): {phone}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Yöntem 3: Tüm buttonları kontrol et
        if not phone:
            try:
                buttons = self.browser.driver.find_elements(By.CSS_SELECTOR, "button")
                for btn in buttons:
                    try:
                        text = btn.text.strip()
                        if text and REGEX_PATTERNS["phone"].search(text) and len(text) < 30:
                            # Bazen butonlar diğer metin içerebilir, bu yüzden regex ile sadece telefon kısmını çıkart
                            phone_match = REGEX_PATTERNS["phone"].search(text)
                            if phone_match:
                                phone = phone_match.group(0)
                                self.update_status(f"Telefon bulundu (genel buton): {phone}")
                                break
                    except:
                        continue
            except:
                pass
        
        # Yöntem 4: Tüm sayfada regex ile telefon numarası ara
        if not phone:
            try:
                page_source = self.browser.driver.page_source
                phone_matches = REGEX_PATTERNS["phone"].findall(page_source)
                
                if phone_matches:
                    # En uzun eşleşmeyi al (daha muhtemel telefon numarası)
                    phone = max(phone_matches, key=len)
                    self.update_status(f"Telefon bulundu (sayfa kaynağı): {phone}")
            except:
                pass
        
        return phone