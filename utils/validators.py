"""
Doğrulama fonksiyonları
"""
import re
from urllib.parse import urlparse

def is_valid_email(email):
    """
    E-posta adresinin geçerli olup olmadığını kontrol eder
    
    Args:
        email (str): Kontrol edilecek e-posta adresi
        
    Returns:
        bool: E-posta geçerli ise True, değilse False
    """
    if not email or not isinstance(email, str):
        return False
        
    pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(pattern.match(email))

def is_valid_url(url):
    """
    URL'nin geçerli olup olmadığını kontrol eder
    
    Args:
        url (str): Kontrol edilecek URL
        
    Returns:
        bool: URL geçerli ise True, değilse False
    """
    if not url or not isinstance(url, str):
        return False
        
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_phone(phone):
    """
    Telefon numarasının geçerli olup olmadığını kontrol eder
    
    Args:
        phone (str): Kontrol edilecek telefon numarası
        
    Returns:
        bool: Telefon numarası geçerli ise True, değilse False
    """
    if not phone or not isinstance(phone, str):
        return False
        
    # Sadece sayı, boşluk, parantez ve + karakterleri içerebilir
    pattern = re.compile(r'^[0-9\s\(\)\+\-]+$')
    return bool(pattern.match(phone))

def has_minimum_length(text, min_length=3):
    """
    Metnin minimum uzunlukta olup olmadığını kontrol eder
    
    Args:
        text (str): Kontrol edilecek metin
        min_length (int): Minimum uzunluk
        
    Returns:
        bool: Metin minimum uzunlukta ise True, değilse False
    """
    if not text or not isinstance(text, str):
        return False
        
    return len(text.strip()) >= min_length