"""
Konfigürasyon sabitleri
"""
import re

# Tarayıcı ayarları
BROWSER_CONFIG = {
    "headless": False,             # Başsız mod (görünmez tarayıcı)
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "window_size": (1366, 768),    # Pencere boyutu
    "timeout": 30,                 # Sayfa yükleme zaman aşımı (saniye)
    "sleep_min": 2,                # Minimum bekleme süresi (saniye)
    "sleep_max": 5,                # Maksimum bekleme süresi (saniye) 
    "sleep_click_min": 1,          # Tıklama sonrası minimum bekleme
    "sleep_click_max": 2,          # Tıklama sonrası maksimum bekleme
}

# Google Maps ayarları
MAPS_CONFIG = {
    "base_url": "https://www.google.com/maps/search/",
    "max_retry": 3,                # Maksimum yeniden deneme sayısı
    "max_scroll": 20,              # Maksimum kaydırma sayısı
}

# CSS Seçiciler (Google Maps'teki elementleri bulmak için)
CSS_SELECTORS = {
    # İşletme listesi seçicileri
    "business_list": [
        "div.ecceSd", 
        "div[role='feed']", 
        "div.m6QErb", 
        "div.section-scrollbox"
    ],
    
    # İşletme öğeleri seçicileri
    "business_items": [
        "div.Nv2PK", 
        "a.hfpxzc", 
        "div[jsaction*='mouseover']", 
        "div.bfdHYd"
    ],
    
    # İşletme adı seçicileri
    "business_name": [
        "h1.DUwDvf", 
        "h1.fontHeadlineLarge", 
        "span.fontHeadlineLarge", 
        "div.fontHeadlineLarge", 
        "h1"
    ],
    
    # Website seçicileri
    "website": [
        "a[data-item-id='authority']", 
        "button[data-item-id='authority']", 
        "a[data-tooltip='Web sitesi']", 
        "a[aria-label*='site']", 
        "a[href*='http']:not([href*='google.com']):not([href*='goo.gl'])"
    ],
    
    # Telefon seçicileri
    "phone": [
        "button[data-tooltip='Telefon numarasını kopyala']", 
        "button[data-item-id*='phone']", 
        "[aria-label*='telefon']"
    ],
    
    # Adres seçicileri
    "address": [
        "button[data-item-id*='address']", 
        "button[data-tooltip='Adresi kopyala']", 
        "[aria-label*='adres']"
    ],
    
    # Geri butonları
    "back_buttons": [
        "button.g88MCb", 
        "button.VfPpkd-icon-LgbsSe", 
        "button[jsaction*='back']", 
        "button[aria-label*='geri']"
    ],
    
    # Bilgi paneli
    "info_panel": [
        "div.m6QErb", 
        "div.TIHn2", 
        "div[role='main']", 
        "div[role='dialog']", 
        "div.rogA2c"
    ]
}

# RegEx Paternleri
REGEX_PATTERNS = {
    "email": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'),
    "phone": re.compile(r'(\+\d{1,3}\s?)?(\(\d{1,4}\)\s?)?[\d\s]{7,}')
}

# Dışa aktarma ayarları
EXPORT_CONFIG = {
    "excel_filename_pattern": "isletmeler_detayli_{timestamp}.xlsx",
    "csv_filename_pattern": "isletmeler_detayli_{timestamp}.csv",
    "backup_filename_pattern": "isletmeler_yedek_{timestamp}.txt"
}