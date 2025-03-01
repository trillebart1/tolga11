"""
Özel UI bileşenleri
"""
import tkinter as tk
from tkinter import ttk
from .styling import COLORS, FONTS

class StyledFrame(ttk.LabelFrame):
    """Özel stillendirilmiş frame"""
    def __init__(self, parent, text, **kwargs):
        padding = kwargs.pop('padding', 10)
        super().__init__(parent, text=text, padding=padding, **kwargs)

class StyledButton(tk.Button):
    """Özel stillendirilmiş buton"""
    def __init__(self, parent, text, command, width=20, is_primary=True, **kwargs):
        bg_color = COLORS["primary"] if is_primary else COLORS["secondary"]
        fg_color = COLORS["white"] if is_primary else COLORS["text"]
        font = FONTS["button"] if is_primary else FONTS["normal"]
        
        super().__init__(
            parent, 
            text=text, 
            command=command,
            bg=bg_color,
            fg=fg_color,
            font=font,
            relief="flat", 
            width=width,
            **kwargs
        )

class LogConsole(tk.scrolledtext.ScrolledText):
    """Özel log konsol bileşeni"""
    def __init__(self, parent, **kwargs):
        height = kwargs.pop('height', 15)
        width = kwargs.pop('width', 80)
        super().__init__(
            parent,
            height=height,
            width=width,
            font=FONTS["mono"],
            **kwargs
        )
        self.configure(state='disabled')  # Başlangıçta düzenlemeyi kapat
        
    def log(self, message):
        """Mesaj ekle"""
        import time
        self.configure(state='normal')  # Düzenlemeyi aç
        self.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.see(tk.END)  # Sona kaydır
        self.configure(state='disabled')  # Düzenlemeyi kapat
        
    def clear(self):
        """Tüm içeriği temizle"""
        self.configure(state='normal')
        self.delete(1.0, tk.END)
        self.configure(state='disabled')