"""
E-posta bulma yardımcıları
"""
import re
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin
from .validators import is_valid_email

class EmailFinder:
    """
    Web sayfalarında e-posta adreslerini bulan sınıf
    """
    def __init__(self, browser=None, update_status_callback=None):
        """
        Args:
            browser: Tarayıcı yöneticisi
            update_status_callback: Durum güncellemesi için callback fonksiyonu
        """
        self.browser = browser
        self.update_status = update_status_callback or (lambda msg: None)
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        
    def find_emails_on_website(self, website_url):
        """
        Bir websitesinde e-posta adreslerini bulur
        
        Args:
            website_url: Taranacak websitesinin URL'si
            
        Returns:
            list: Bulunan benzersiz e-posta adresleri listesi
        """
        emails = []
        
        if not self.browser or not self.browser.driver:
            self.update_status("E-posta taraması için tarayıcı bulunamadı!")
            return emails
            
        try:
            # Yeni pencere aç
            self.update_status(f"E-posta taraması için {website_url} ziyaret ediliyor (yeni pencerede)...")
            original_window = self.browser.open_new_window(website_url)
            
            if not original_window:
                self.update_status("Yeni pencere açılamadı, e-posta taraması yapılamıyor!")
                return emails
            
            # Ana sayfada e-posta ara
            page_emails = self.find_emails_on_page(self.browser.driver)
            emails.extend(page_emails)
            
            # İletişim sayfasını bul ve ziyaret et
            contact_links = self._find_contact_page_links(self.browser.driver, website_url)
            
            for link in contact_links[:2]:  # En fazla 2 iletişim sayfasını ziyaret et
                try:
                    self.update_status(f"İletişim sayfası ziyaret ediliyor: {link}")
                    self.browser.driver.get(link)
                    self.browser.random_sleep()
                    
                    contact_emails = self.find_emails_on_page(self.browser.driver)
                    emails.extend(contact_emails)
                except Exception as e:
                    self.update_status(f"İletişim sayfası ziyaret hatası: {str(e)}")
            
            # Taramayı tamamladıktan sonra pencereyi kapat ve geri dön
            self.browser.close_current_and_switch_to(original_window)
            
            # Benzersiz e-postaları döndür
            unique_emails = list(set(emails))
            return unique_emails
            
        except Exception as e:
            self.update_status(f"Website e-posta tarama hatası: {str(e)}")
            # Hata durumunda da pencereyi kapatmaya çalış
            try:
                if 'original_window' in locals() and original_window:
                    self.browser.close_current_and_switch_to(original_window)
            except:
                pass
            return emails
    
    def find_emails_on_page(self, driver):
        """
        Belirli bir sayfada e-posta adreslerini bulur
        
        Args:
            driver: Selenium WebDriver nesnesi
            
        Returns:
            list: Bulunan benzersiz e-posta adresleri listesi
        """
        emails = set()
        
        try:
            # HTML kaynak kodunda e-posta adresleri ara
            page_source = driver.page_source
            found_emails = self.email_pattern.findall(page_source)
            
            for email in found_emails:
                if is_valid_email(email):
                    emails.add(email)
                    self.update_status(f"E-posta bulundu: {email}")
            
            # Metin içeriklerinde e-posta ara
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                text = body.text
                
                if text:
                    text_emails = self.email_pattern.findall(text)
                    for email in text_emails:
                        if is_valid_email(email):
                            emails.add(email)
                            self.update_status(f"Metin içinde e-posta bulundu: {email}")
            except:
                pass
            
            # Bağlantılarda e-posta ara (özellikle mailto: linkleri)
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        if href and href.startswith('mailto:'):
                            email = href[7:].split('?')[0]  # mailto: kısmını ve olası parametreleri kaldır
                            if is_valid_email(email):
                                emails.add(email)
                                self.update_status(f"Mail link'i bulundu: {email}")
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            self.update_status(f"Sayfa e-posta tarama hatası: {str(e)}")
        
        return list(emails)
    
    def _find_contact_page_links(self, driver, base_url):
        """
        İletişim sayfası bağlantılarını bulur
        
        Args:
            driver: Selenium WebDriver nesnesi
            base_url: Temel URL
            
        Returns:
            list: İletişim sayfalarının URL listesi
        """
        contact_links = []
        contact_keywords = [
            'iletişim', 'contact', 'kontakt', 'связаться', 'contacto', 
            'contatto', 'kontakt', 'contato', '連絡先', '联系', 'bize ulaşın',
            'contact us', 'get in touch', 'reach us', 'bize yazın'
        ]
        
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                        
                    # Mutlak URL'ye çevir
                    absolute_url = urljoin(base_url, href)
                    parsed_url = urlparse(absolute_url)
                    
                    # Aynı domain'de olduğunu kontrol et
                    if parsed_url.netloc != base_domain:
                        continue
                    
                    # Link metnini veya href değerini kontrol et
                    link_text = link.text.lower()
                    href_lower = href.lower()
                    
                    for keyword in contact_keywords:
                        if keyword in link_text or keyword in href_lower:
                            contact_links.append(absolute_url)
                            self.update_status(f"İletişim sayfası bulundu: {absolute_url}")
                            break
                except:
                    continue
        except Exception as e:
            self.update_status(f"İletişim sayfası arama hatası: {str(e)}")
        
        return contact_links