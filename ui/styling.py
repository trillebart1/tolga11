"""
UI stil tanımlamaları
"""
import tkinter as tk
from tkinter import ttk

# Renk Teması
COLORS = {
    "primary": "#4285F4",      # Google Mavi
    "secondary": "#e0e0e0",    # Açık Gri
    "background": "#f0f2f5",   # Arkaplan
    "text": "#333333",         # Koyu Metin
    "white": "#FFFFFF",        # Beyaz
    "success": "#34A853",      # Yeşil
    "warning": "#FBBC05",      # Sarı
    "error": "#EA4335",        # Kırmızı
}

# Font ayarları
FONTS = {
    "header": ("Segoe UI", 16, "bold"),
    "title": ("Segoe UI", 12, "bold"),
    "normal": ("Segoe UI", 10),
    "button": ("Segoe UI", 10, "bold"),
    "mono": ("Consolas", 10),
}

def apply_styles(root):
    """
    Uygulama genelinde stil ayarlarını uygular
    """
    style = ttk.Style()
    
    # LabelFrame (Gruplar) stili
    style.configure("TLabelframe", background=COLORS["white"])
    style.configure("TLabelframe.Label", font=FONTS["title"])
    
    # Entry (Giriş kutuları) stili
    style.configure("TEntry", padding=5)
    
    # Progressbar (İlerleme çubuğu) stili
    style.configure("TProgressbar", 
                   thickness=20, 
                   troughcolor=COLORS["secondary"],
                   background=COLORS["primary"])
    
    # Normal Checkbutton stili
    style.configure("TCheckbutton", background=COLORS["white"])
    
    return style