"""
Adres bilgisi çıkarma modülü
"""
import re
from selenium.webdriver.common.by import By
from ..config import CSS_SELECTORS

class AddressExtractor:
    """
    Adres bilgisi çıkarma sınıfı
    """
    def __init__(self, browser, update_status_callback=None):
        """
        Args:
            browser: BrowserManager nesnesi
            update_status_callback: Durum güncellemesi yapacak callback fonksiyonu
        """
        self.browser = browser
        self.update_status = update_status_callback or (lambda msg: None)
    
    def extract_address(self):
        """
        Adresi bulmak için geliştirilmiş yöntem
        
        Returns:
            str: Bulunan adres veya None
        """
        address = None
        
        # Yöntem 1: Standart CSS seçicileriyle arama
        address_selector = ", ".join(CSS_SELECTORS["address"])
        address_elements = self.browser.driver.find_elements(By.CSS_SELECTOR, address_selector)
        
        for addr_elem in address_elements:
            try:
                # Seçenek 1: aria-label özniteliği
                aria_label = addr_elem.get_attribute('aria-label')
                if aria_label and ('adres' in aria_label.lower() or 'konum' in aria_label.lower()):
                    address = aria_label.replace('Adres: ', '').strip()
                    self.update_status(f"Adres bulundu (aria-label): {address}")
                    break
                    
                # Seçenek 2: Element metni
                text = addr_elem.text
                if text and len(text) > 10:  # Basit adres kontrolü
                    address = text
                    self.update_status(f"Adres bulundu (metin): {address}")
                    break
            except:
                continue
        
        # Yöntem 2: Adres ikonuyla ilişkili buttonlar
        if not address:
            try:
                # Adres simgesi içeren butonları bul
                address_buttons = self.browser.driver.find_elements(
                    By.CSS_SELECTOR, "button[data-item-id^='address'], [data-tooltip='Adres kopyala']"
                )
                
                for btn in address_buttons:
                    try:
                        text = btn.text.strip()
                        if text and len(text) > 10:  # Basit adres kontrolü
                            address = text
                            self.update_status(f"Adres bulundu (adres butonu): {address}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Yöntem 3: data-item-id özniteliği içeren elementler
        if not address:
            try:
                # data-item-id içinde address geçen elementleri bul
                address_items = self.browser.driver.find_elements(
                    By.CSS_SELECTOR, "[data-item-id*='address']"
                )
                
                for item in address_items:
                    try:
                        text = item.text.strip()
                        if text and len(text) > 10:  # Basit adres kontrolü
                            address = text
                            self.update_status(f"Adres bulundu (data-item-id): {address}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Yöntem 4: Konum ikonları ve benzer içerikli butonlar
        if not address:
            try:
                location_xpath = "//img[contains(@src, 'location') or contains(@src, 'address')]/ancestor::button"
                location_buttons = self.browser.driver.find_elements(By.XPATH, location_xpath)
                
                for btn in location_buttons:
                    try:
                        text = btn.text.strip()
                        if text and len(text) > 10:  # Basit adres kontrolü
                            address = text
                            self.update_status(f"Adres bulundu (konum ikonu): {address}")
                            break
                    except:
                        continue
            except:
                pass
        
        # Yöntem 5: Google Maps URL'inden konum bilgisini çıkarma
        if not address:
            try:
                url = self.browser.driver.current_url
                place_id_match = re.search(r'place/([^/]+)', url)
                
                if place_id_match:
                    place_name = place_id_match.group(1).replace('+', ' ')
                    # Basit bir temizleme (URL kodlamasını temizle)
                    place_name = re.sub(r'%\d\w', ' ', place_name)
                    if len(place_name) > 5:
                        address = place_name
                        self.update_status(f"Adres bulundu (URL'den): {address}")
            except:
                pass
        
        return address