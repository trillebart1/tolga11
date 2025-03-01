"""
Loglama yardımcıları
"""
import logging
import time
import os
import sys

class Logger:
    """Logger yardımcı sınıfı"""
    
    def __init__(self, log_to_file=False, log_level=logging.INFO):
        """
        Logger'ı başlat
        
        Args:
            log_to_file: Dosyaya da log yazılsın mı
            log_level: Log seviyesi
        """
        self.logger = logging.getLogger('email_scraper')
        self.logger.setLevel(log_level)
        
        # Eğer daha önce handler eklenmiş ise temizle
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Konsol handler'ı
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # Dosya handler'ı (istenirse)
        if log_to_file:
            # Log klasörü kontrol et
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # Log dosyası
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            log_file = os.path.join(log_dir, f"scraper_{timestamp}.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_format)
            self.logger.addHandler(file_handler)
    
    def info(self, message):
        """Info seviyesinde log"""
        self.logger.info(message)
    
    def error(self, message):
        """Error seviyesinde log"""
        self.logger.error(message)
    
    def warning(self, message):
        """Warning seviyesinde log"""
        self.logger.warning(message)
    
    def debug(self, message):
        """Debug seviyesinde log"""
        self.logger.debug(message)