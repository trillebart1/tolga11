"""
E-posta ve İletişim Bilgisi Toplayıcı - Ana Başlatma Dosyası
"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

def check_dependencies():
    """Gerekli bağımlılıkları kontrol eder ve uyarı verir"""
    missing_modules = []
    
    dependencies = {
        'selenium': 'Selenium Web Driver',
        'tkinter': 'Tkinter GUI kütüphanesi',
        'pandas': 'Pandas veri analizi kütüphanesi (Excel desteği için)',
        'openpyxl': 'OpenPyXL Excel işleme kütüphanesi'
    }
    
    for module, description in dependencies.items():
        try:
            if module == 'tkinter':
                import tkinter
            else:
                __import__(module)
        except ImportError:
            missing_modules.append(f"{module} ({description})")
    
    return missing_modules

def main():
    missing = check_dependencies()
    
    app = MainWindow(missing_dependencies=missing)
    app.run()

if __name__ == "__main__":
    main()