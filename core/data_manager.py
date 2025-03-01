"""
Veri yönetimi ve dışa aktarma sınıfı
"""
import os
import time
import csv

from .config import EXPORT_CONFIG

class DataManager:
    """
    Veri yönetimi ve dışa aktarma işlemleri
    """
    def __init__(self):
        self.data = []
        
        # Excel desteği kontrol et
        self.has_pandas = False
        self.has_openpyxl = False
        
        try:
            import pandas
            self.has_pandas = True
        except ImportError:
            pass
        
        try:
            import openpyxl
            self.has_openpyxl = True
        except ImportError:
            pass
    
    def has_excel_support(self):
        """Excel desteği var mı kontrol et"""
        return self.has_pandas and self.has_openpyxl
    
    def set_data(self, data):
        """Veri kaydet"""
        self.data = data
    
    def get_data(self):
        """Veriyi getir"""
        return self.data
    
    def has_data(self):
        """Veri var mı kontrol et"""
        return len(self.data) > 0
    
    def clear_data(self):
        """Veriyi temizle"""
        self.data = []
    
    def export_data(self):
        """
        Veriyi dışa aktar - Excel veya CSV olarak
        
        Returns:
            str: Dışa aktarılan dosyanın adı
        
        Raises:
            Exception: Dışa aktarma hatası durumunda
        """
        if not self.data:
            raise Exception("Dışa aktarılacak veri bulunamadı!")
            
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        
        # Excel modülleri varsa Excel olarak kaydet, yoksa CSV
        try:
            if self.has_excel_support():
                import pandas as pd
                
                filename = EXPORT_CONFIG["excel_filename_pattern"].format(timestamp=timestamp)
                df = pd.DataFrame(self.data)
                df.to_excel(filename, index=False)
                return filename
            else:
                # CSV olarak kaydet
                filename = EXPORT_CONFIG["csv_filename_pattern"].format(timestamp=timestamp)
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    if self.data:
                        # Sütun başlıklarını al
                        fieldnames = self.data[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        
                        # Başlıkları ve verileri yaz
                        writer.writeheader()
                        for business in self.data:
                            writer.writerow(business)
                return filename
        except Exception as e:
            # Hata durumunda en basit formatta kaydetmeye çalış
            backup_file = EXPORT_CONFIG["backup_filename_pattern"].format(timestamp=timestamp)
            with open(backup_file, 'w', encoding='utf-8') as f:
                for business in self.data:
                    f.write(str(business) + "\n\n")
            return backup_file