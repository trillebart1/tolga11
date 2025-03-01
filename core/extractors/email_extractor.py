"""
E-posta çıkarma modülü - İyileştirilmiş kontrol mekanizmaları eklendi
"""
import re
import time
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin
from utils.validators import is_valid_email

class EmailExtractor:
    """
    E-posta çıkarma sınıfı
    """
    def __init__(self, browser, update_status_callback=None):
        """
        Args:
            browser: BrowserManager nesnesi
            update_status_callback: Durum güncellemesi yapacak callback fonksiyonu
        """
        self.browser = browser
        self.update_status = update_status_callback or (lambda msg: None)
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    def extract_emails_from_website(self, website_url):
        """
        Websiteyi yeni sekmede ziyaret et ve e-posta adreslerini topla
        
        Args:
            website_url: Ziyaret edilecek website adresi
            
        Returns:
            list: Bulunan e-posta adresleri listesi
        """
        emails = []
        new_tab = None
        
        # İlk olarak URL'yi doğrula
        if not website_url or not isinstance(website_url, str) or not website_url.startswith('http'):
            self.update_status("Geçersiz website URL'si. E-posta araması yapılmayacak.")
            return emails
            
        # Genel websiteleri filtrele
        excluded_domains = [
            'google.com', 'goo.gl', 'youtube.com', 'facebook.com', 'instagram.com',
            'twitter.com', 'linkedin.com', 'maps.app.goo.gl', 'yelp.com', 'tripadvisor.com'
        ]
        
        # URL'yi kontrol et, yasaklı domainlerden biriyse hemen çık
        if any(domain in website_url.lower() for domain in excluded_domains):
            self.update_status(f"Bu URL ({website_url}) geçerli bir işletme websitesi değil, sosyal medya veya platform URL'si. E-posta araması yapılmayacak.")
            return emails
        
        try:
            # Yeni pencere aç
            self.update_status(f"Web sitesi ziyaret ediliyor: {website_url}")
            
            # Mevcut sekmeleri kaydet
            original_handles = self.browser.driver.window_handles
            original_window = self.browser.driver.current_window_handle
            
            # Yeni sekme aç
            self.browser.driver.execute_script("window.open('about:blank', '_blank');")
            self.browser.random_sleep(0.5, 1)
            
            # Yeni sekmeyi bul ve geç
            new_handles = [handle for handle in self.browser.driver.window_handles 
                           if handle not in original_handles]
            
            if not new_handles:
                self.update_status("Yeni sekme açılamadı! E-posta araması yapılmayacak.")
                return emails
                
            new_tab = new_handles[0]
            
            # Yeni sekmeye geç
            self.browser.driver.switch_to.window(new_tab)
            
            # URL'yi yükle
            try:
                self.update_status(f"Website yükleniyor: {website_url}")
                self.browser.driver.get(website_url)
                self.browser.random_sleep(3, 5)  # Sayfanın yüklenmesi için daha uzun bekle
                
                # Yüklenen URL'yi kontrol et - eğer başka bir URL'ye yönlendirildiyse
                actual_url = self.browser.driver.current_url
                if actual_url != website_url:
                    self.update_status(f"URL yönlendirmesi algılandı: {actual_url}")
                    
                    # Yönlendirilen URL'de de yasaklı domainler var mı kontrol et
                    if any(domain in actual_url.lower() for domain in excluded_domains):
                        self.update_status(f"Yönlendirilen URL ({actual_url}) geçerli bir işletme websitesi değil.")
                        
                        # Sekmeyi kapat ve çık
                        self.browser.driver.close()
                        self.browser.driver.switch_to.window(original_window)
                        return emails
            except Exception as load_err:
                self.update_status(f"Website yükleme hatası: {str(load_err)}")
                
                # Sekmeyi kapat ve çık
                try:
                    self.browser.driver.close()
                    self.browser.driver.switch_to.window(original_window)
                except:
                    pass
                    
                return emails
            
            # Ana sayfadan e-posta adresleri topla
            self.update_status("Ana sayfadaki e-postaları taranıyor...")
            page_emails = self._find_emails_on_page()
            emails.extend(page_emails)
            self.update_status(f"Ana sayfada {len(page_emails)} e-posta bulundu")
            
            # İletişim sayfası linkleri için özel arama
            self.update_status("İletişim sayfaları aranıyor...")
            contact_links = self._find_contact_links(website_url)
            self.update_status(f"{len(contact_links)} potansiyel iletişim sayfası bulundu")
            
            # İletişim sayfalarını ziyaret et (maksimum 2 sayfa)
            visited_pages = set([website_url.lower()])
            
            # İletişim sayfalarını kontrol et
            for i, link in enumerate(contact_links[:2]):  # Maksimum 2 iletişim sayfası
                link_lower = link.lower()
                if link_lower in visited_pages:
                    self.update_status(f"Sayfa zaten ziyaret edildi: {link}")
                    continue
                    
                try:
                    self.update_status(f"İletişim sayfası ziyaret ediliyor ({i+1}/2): {link}")
                    self.browser.driver.get(link)
                    self.browser.random_sleep(2, 4)  # Sayfanın yüklenmesi için daha uzun bekle
                    
                    # Sayfadan e-posta topla
                    contact_emails = self._find_emails_on_page()
                    if contact_emails:
                        emails.extend(contact_emails)
                        self.update_status(f"İletişim sayfasında {len(contact_emails)} e-posta bulundu")
                    else:
                        self.update_status("Bu iletişim sayfasında e-posta bulunamadı")
                    
                    # Ziyaret edilen sayfaları işaretle
                    visited_pages.add(link_lower)
                    
                except Exception as e:
                    self.update_status(f"İletişim sayfası ziyaret hatası: {str(e)}")
                    continue
            
            # Eğer hala e-posta bulunamadıysa, diğer bağlantılara göz at
            if not emails:
                self.update_status("Henüz e-posta bulunamadı, diğer sayfalar kontrol ediliyor...")
                other_links = self._find_other_internal_links(website_url)
                
                for i, link in enumerate(other_links[:3]):  # Maksimum 3 ek sayfa
                    if link.lower() in visited_pages:
                        continue
                        
                    try:
                        self.update_status(f"Ek sayfa ziyaret ediliyor ({i+1}/3): {link}")
                        self.browser.driver.get(link)
                        self.browser.random_sleep(1, 3)
                        
                        # Sayfadan e-posta topla
                        page_emails = self._find_emails_on_page()
                        if page_emails:
                            emails.extend(page_emails)
                            self.update_status(f"Bu sayfada {len(page_emails)} e-posta bulundu")
                        else:
                            self.update_status("Bu sayfada e-posta bulunamadı")
                            
                        # Ziyaret edilen sayfaları işaretle
                        visited_pages.add(link.lower())
                        
                    except Exception as e:
                        self.update_status(f"Sayfa ziyaret hatası: {str(e)}")
                        continue
            
            # Tekrar eden e-postaları kaldır
            emails = list(set(emails))
            
            # E-postaları filtrele ve önceliklendir
            emails = self._prioritize_emails(emails)
            
            # Sonuç
            if emails:
                self.update_status(f"Toplam {len(emails)} benzersiz e-posta bulundu")
            else:
                self.update_status("Hiçbir e-posta bulunamadı")
                
        except Exception as e:
            self.update_status(f"E-posta toplama hatası: {str(e)}")
        finally:
            # Yeni sekmeyi kapat ve ana sekmeye geri dön
            try:
                if new_tab:
                    self.browser.driver.close()
                
                # Ana sekmeye dön
                self.browser.driver.switch_to.window(original_window)
                self.browser.random_sleep(0.5, 1)
            except Exception as close_err:
                self.update_status(f"Sekme kapatma hatası: {str(close_err)}")
                # Kritik durum - pencere değiştirmeyi zorla
                try:
                    self.browser.driver.switch_to.window(original_window)
                except:
                    pass
        
        return emails
    
    def _find_emails_on_page(self):
        """
        Mevcut sayfada e-posta adreslerini bulur
        
        Returns:
            list: Bulunan e-posta adresleri
        """
        emails = set()
        
        try:
            # HTML kaynak kodunda e-posta adresleri ara
            page_source = self.browser.driver.page_source
            found_emails = self.email_pattern.findall(page_source)
            
            for email in found_emails:
                if is_valid_email(email):
                    emails.add(email)
                    self.update_status(f"E-posta bulundu: {email}")
            
            # Metin içeriklerinde e-posta ara
            try:
                body = self.browser.driver.find_element(By.TAG_NAME, "body")
                text = body.text
                
                if text:
                    text_emails = self.email_pattern.findall(text)
                    for email in text_emails:
                        if is_valid_email(email):
                            emails.add(email)
            except:
                pass
            
            # Bağlantılarda e-posta ara (özellikle mailto: linkleri)
            try:
                links = self.browser.driver.find_elements(By.TAG_NAME, "a")
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
    
    def _find_contact_links(self, base_url):
        """
        İletişim sayfası bağlantılarını bulur
        
        Args:
            base_url: Temel URL
            
        Returns:
            list: İletişim sayfalarının URL listesi
        """
        contact_links = []
        contact_keywords = [
            'iletişim', 'iletisim', 'contact', 'kontakt', 'связаться', 'contacto', 
            'contatto', 'kontakt', 'contato', '連絡先', '联系', 'bize ulaşın',
            'contact-us', 'contact_us', 'get-in-touch', 'reach-us', 'bize-yazın',
            'bize_ulasin', 'hakkimizda', 'about-us', 'about_us', 'kurumsal'
        ]
        
        try:
            # Tüm <a> etiketlerini bul
            links = self.browser.driver.find_elements(By.TAG_NAME, "a")
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href or not href.startswith('http'):
                        continue
                    
                    # URL'yi kontrol et
                    parsed_url = urlparse(href)
                    
                    # Aynı domain'de olduğunu kontrol et
                    if parsed_url.netloc != base_domain:
                        continue
                    
                    # Link metnini veya href değerini kontrol et
                    link_text = link.text.lower()
                    href_lower = href.lower()
                    
                    # İletişim sayfası olma ihtimali
                    for keyword in contact_keywords:
                        if (keyword in link_text) or (keyword in href_lower):
                            contact_links.append(href)
                            self.update_status(f"Muhtemel iletişim sayfası: {href}")
                            break
                except:
                    continue
                    
            # Menu classlarını da kontrol et
            try:
                menu_items = self.browser.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "nav a, .menu a, .nav a, .navbar a, header a, .header a, footer a, .footer a"
                )
                
                for item in menu_items:
                    try:
                        href = item.get_attribute('href')
                        if not href or not href.startswith('http'):
                            continue
                            
                        parsed_url = urlparse(href)
                        if parsed_url.netloc != base_domain:
                            continue
                            
                        item_text = item.text.lower()
                        href_lower = href.lower()
                        
                        for keyword in contact_keywords:
                            if (keyword in item_text) or (keyword in href_lower):
                                if href not in contact_links:
                                    contact_links.append(href)
                                    self.update_status(f"Menüden iletişim sayfası: {href}")
                                break
                    except:
                        continue
            except:
                pass
                
        except Exception as e:
            self.update_status(f"İletişim sayfası arama hatası: {str(e)}")
        
        return contact_links
        
    def _find_other_internal_links(self, base_url):
        """
        Diğer dahili bağlantıları bulur (aynı domainde)
        
        Args:
            base_url: Temel URL
            
        Returns:
            list: Dahili bağlantı listesi
        """
        internal_links = []
        skip_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.xls', '.zip', '.rar']
        
        try:
            links = self.browser.driver.find_elements(By.TAG_NAME, "a")
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc
            
            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href or not href.startswith('http'):
                        continue
                        
                    # Dosya uzantılarını kontrol et
                    if any(href.lower().endswith(ext) for ext in skip_extensions):
                        continue
                        
                    parsed_url = urlparse(href)
                    
                    # Aynı domain'de olduğunu kontrol et
                    if parsed_url.netloc != base_domain:
                        continue
                        
                    # Daha önce dahil edilmediyse ekle
                    if href not in internal_links:
                        internal_links.append(href)
                except:
                    continue
                    
        except Exception as e:
            self.update_status(f"Dahili bağlantıları bulma hatası: {str(e)}")
            
        # Sayfa sayısını sınırlandır
        return internal_links[:10]  # En fazla 10 dahili bağlantı döndür
    
    def _prioritize_emails(self, emails):
        """
        E-postaları önceliklendirir ve filtreleyerek döndürür
        - noreply gibi e-postaları filtreler
        - info@ gibi genel e-postaları listenin sonuna taşır
        - Diğer e-postaları önce getirir
        
        Args:
            emails: E-posta listesi 
            
        Returns:
            list: Önceliklendirilmiş e-posta listesi
        """
        if not emails:
            return []
            
        filtered_emails = []
        general_emails = []
        excluded_emails = []
        
        exclude_patterns = ['noreply', 'no-reply', 'donotreply', 'mailer-daemon', 'mailerdaemon', 'postmaster']
        general_patterns = ['info@', 'contact@', 'mail@', 'iletisim@', 'bilgi@', 'hello@', 'destek@', 'support@']
        
        for email in emails:
            email_lower = email.lower()
            
            # Dışlanacak e-postalar
            if any(pattern in email_lower for pattern in exclude_patterns):
                excluded_emails.append(email)
            # Genel e-postalar
            elif any(pattern in email_lower for pattern in general_patterns):
                if email not in general_emails:
                    general_emails.append(email)
            # Normal e-postalar
            else:
                if email not in filtered_emails:
                    filtered_emails.append(email)
        
        # Önce kişisel, sonra genel e-postaları döndür
        result = filtered_emails + general_emails
        
        if not result and excluded_emails:
            # Eğer başka e-posta yoksa, en azından dışlananları göster
            return excluded_emails
            
        return result