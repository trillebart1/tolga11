"""
Ana pencere arayüzü - Sekmeli arayüz tasarımı
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import queue
import threading
import time

# Dahili modülleri içe aktar
from .styling import COLORS, FONTS, apply_styles
from .components import StyledFrame, StyledButton, LogConsole
from core.scraper import MapsScraper
from core.data_manager import DataManager

class MainWindow:
    def __init__(self, missing_dependencies=None):
        # Ana pencere oluştur
        self.window = tk.Tk()
        self.window.title("Detaylı E-posta ve İletişim Bilgisi Toplayıcı")
        self.window.geometry("700x600")  # Boyutu azalttım
        self.window.minsize(600, 500)    # Minimum boyutu da azalttım
        self.window.configure(bg=COLORS["background"])
        
        # Stil uygula
        self.style = apply_styles(self.window)
        
        # Eksik modül uyarısını göster
        if missing_dependencies:
            self.show_module_warning(missing_dependencies)
            
        # İleti kuyruğu
        self.message_queue = queue.Queue()
        
        # İşlem durumu
        self.is_running = False
        
        # Veri yöneticisi
        self.data_manager = DataManager()
        
        # Veri toplama seçenekleri - başlangıç değerleri
        self.collect_address_var = tk.BooleanVar(value=True)
        self.collect_phone_var = tk.BooleanVar(value=True)
        self.collect_website_var = tk.BooleanVar(value=True)
        self.collect_email_var = tk.BooleanVar(value=True)
        
        # UI oluştur
        self.setup_ui()
        
        # Kuyruk işlemini başlat
        self.window.after(100, self.process_queue)
    
    def show_module_warning(self, missing_modules):
        """Eksik modül uyarısı göster"""
        if not missing_modules:
            return
            
        warning_msg = "Dikkat: Aşağıdaki modüller bulunamadı:\n\n"
        warning_msg += "\n".join(missing_modules)
        
        install_instructions = "\n\nKurulum için komut satırına şunu yazın:\n"
        install_instructions += "pip install " + " ".join([m.split()[0] for m in missing_modules])
                
        warning_msg += install_instructions
        warning_msg += "\n\nEksik modüller nedeniyle bazı özellikler çalışmayabilir."
        
        messagebox.showwarning("Modül Eksikliği", warning_msg)
    
    def setup_ui(self):
        """Kullanıcı arayüzünü oluştur"""
        # Ana başlık
        header_frame = tk.Frame(self.window, bg=COLORS["background"], pady=10)
        header_frame.pack(fill="x")
        
        title_label = tk.Label(header_frame, 
                             text="Google Maps E-posta ve İletişim Toplama Aracı", 
                             font=FONTS["header"], 
                             bg=COLORS["background"], 
                             fg=COLORS["primary"])
        title_label.pack()
        
        # Sekme kontrol paneli
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Sekme 1: Ayarlar
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Arama Ayarları")
        
        # Sekme 2: Sonuçlar ve İlerleme
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="Sonuçlar ve İlerleme")
        
        # Ayarlar sekmesini oluştur
        self.setup_settings_tab()
        
        # Sonuçlar sekmesini oluştur
        self.setup_results_tab()
        
        # Durum çubuğu
        status_bar = tk.Frame(self.window, bg=COLORS["secondary"], height=25)
        status_bar.pack(side="bottom", fill="x")
        
        self.status_label = tk.Label(
            status_bar, text="Hazır", bd=1, relief=tk.SUNKEN, 
            anchor=tk.W, bg=COLORS["secondary"], fg=COLORS["text"])
        self.status_label.pack(fill="x")
        
    def setup_settings_tab(self):
        """Ayarlar sekmesini oluştur"""
        # Ana container
        main_container = tk.Frame(self.settings_tab, bg=COLORS["background"], padx=10, pady=10)
        main_container.pack(fill="both", expand=True)
        
        # Arama ayarları frame
        settings_frame = StyledFrame(main_container, "Arama Ayarları")
        settings_frame.pack(fill="x", pady=10)
        
        # Grid düzeni içinde ayarlar
        settings_grid = tk.Frame(settings_frame, bg=COLORS["white"])
        settings_grid.pack(fill="x", expand=True, pady=10, padx=10)
        
        # Aranacak kelime
        tk.Label(settings_grid, text="Aranacak Kelime:", 
                font=FONTS["normal"], bg=COLORS["white"]).grid(
                row=0, column=0, sticky="w", padx=5, pady=5)
        self.search_entry = tk.Entry(
            settings_grid, font=FONTS["normal"], 
            width=40, relief="solid", bd=1)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Şehir
        tk.Label(settings_grid, text="Şehir:", 
                font=FONTS["normal"], bg=COLORS["white"]).grid(
                row=1, column=0, sticky="w", padx=5, pady=5)
        self.city_entry = tk.Entry(
            settings_grid, font=FONTS["normal"], 
            width=40, relief="solid", bd=1)
        self.city_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Maksimum işletme sayısı
        tk.Label(settings_grid, text="Maksimum İşletme Sayısı:", 
                font=FONTS["normal"], bg=COLORS["white"]).grid(
                row=2, column=0, sticky="w", padx=5, pady=5)
        self.max_business_var = tk.StringVar(value="20")
        self.max_business_entry = tk.Entry(
            settings_grid, font=FONTS["normal"], 
            width=10, relief="solid", bd=1, 
            textvariable=self.max_business_var)
        self.max_business_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        # Grid sütunlarını otomatik genişlet
        settings_grid.columnconfigure(1, weight=1)
        
        # Veri toplama seçenekleri
        options_frame = StyledFrame(main_container, "Veri Toplama Seçenekleri")
        options_frame.pack(fill="x", pady=10)
        
        options_grid = tk.Frame(options_frame, bg=COLORS["white"])
        options_grid.pack(fill="x", expand=True, pady=10, padx=10)
        
        # Checkbox'ları yan yana düzenle
        check_frame = tk.Frame(options_grid, bg=COLORS["white"])
        check_frame.pack(fill="x", padx=5, pady=5)
        
        address_check = tk.Checkbutton(
            check_frame, text="Adres", 
            variable=self.collect_address_var, bg=COLORS["white"], 
            font=FONTS["normal"])
        address_check.pack(side="left", padx=15)
        
        phone_check = tk.Checkbutton(
            check_frame, text="Telefon", 
            variable=self.collect_phone_var, bg=COLORS["white"], 
            font=FONTS["normal"])
        phone_check.pack(side="left", padx=15)
        
        website_check = tk.Checkbutton(
            check_frame, text="Website", 
            variable=self.collect_website_var, bg=COLORS["white"], 
            font=FONTS["normal"])
        website_check.pack(side="left", padx=15)
        
        email_check = tk.Checkbutton(
            check_frame, text="E-posta", 
            variable=self.collect_email_var, bg=COLORS["white"], 
            font=FONTS["normal"], command=self._toggle_email_option)
        email_check.pack(side="left", padx=15)
        
        # E-posta seçiliyse websitesi de seçilmeli bilgisi
        self.email_info_label = tk.Label(
            options_grid, 
            text="Not: E-posta toplanması için website toplamayı da seçmelisiniz.", 
            font=("Segoe UI", 8, "italic"), fg="gray", bg=COLORS["white"])
        self.email_info_label.pack(anchor="w", padx=10, pady=(0, 5))
        
        # Başlangıçta e-posta kontrolleri
        self._toggle_email_option()
        
        # Butonlar
        buttons_frame = tk.Frame(main_container, bg=COLORS["background"], pady=10)
        buttons_frame.pack(fill="x")
        
        # Start button
        self.start_button = StyledButton(
            buttons_frame, "Taramayı Başlat", self.start_thread)
        self.start_button.pack(side="left", padx=5)
        
        # Bu sekmeden sonuçlar sekmesine geçiş butonu
        go_to_results_button = StyledButton(
            buttons_frame, "Sonuçlar Sekmesine Geç", self._show_results_tab, 
            is_primary=False)
        go_to_results_button.pack(side="right", padx=5)

    def setup_results_tab(self):
        """Sonuçlar sekmesini oluştur"""
        # Ana container
        main_container = tk.Frame(self.results_tab, bg=COLORS["background"], padx=10, pady=10)
        main_container.pack(fill="both", expand=True)
        
        # Butonlar frame
        buttons_frame = tk.Frame(main_container, bg=COLORS["background"])
        buttons_frame.pack(fill="x", pady=10)
        
        # Stop button
        self.stop_button = StyledButton(
            buttons_frame, "Taramayı Durdur", self.stop_scraping, 
            is_primary=False)
        self.stop_button.pack(side="left", padx=5)
        self.stop_button.config(state='disabled')
        
        # Export button
        export_text = "Verileri Dışa Aktar"
        self.export_button = StyledButton(
            buttons_frame, export_text, self.export_results, 
            is_primary=False)
        self.export_button.pack(side="right", padx=5)
        self.export_button.config(state='disabled')
        
        # Clear button
        self.clear_button = StyledButton(
            buttons_frame, "Listeyi Temizle", self.clear_logs, 
            is_primary=False)
        self.clear_button.pack(side="right", padx=5)
        
        # Bu sekmeden ayarlar sekmesine geçiş butonu
        go_to_settings_button = StyledButton(
            buttons_frame, "Ayarlar Sekmesine Dön", self._show_settings_tab, 
            is_primary=False)
        go_to_settings_button.pack(side="left", padx=5)
        
        # İlerleme frame
        progress_frame = StyledFrame(main_container, "İlerleme Durumu")
        progress_frame.pack(fill="x", pady=10)
        
        progress_container = tk.Frame(progress_frame, bg=COLORS["white"])
        progress_container.pack(fill="x", expand=True, pady=10, padx=10)
        
        self.progress_text = tk.StringVar(value="Bekliyor...")
        progress_label = tk.Label(
            progress_container, textvariable=self.progress_text, 
            font=FONTS["normal"], bg=COLORS["white"])
        progress_label.pack(anchor="w", pady=2)
        
        self.progress = ttk.Progressbar(
            progress_container, mode='determinate', 
            style="TProgressbar")
        self.progress.pack(fill="x", pady=5)
        
        # Log frame
        log_frame = StyledFrame(main_container, "İşlem Detayları")
        log_frame.pack(fill="both", expand=True, pady=10)
        
        self.status_text = LogConsole(log_frame)
        self.status_text.pack(fill="both", expand=True, pady=10, padx=10)
    
    def _show_settings_tab(self):
        """Ayarlar sekmesini göster"""
        self.notebook.select(0)  # İlk sekme (0) ayarlar sekmesi
    
    def _show_results_tab(self):
        """Sonuçlar sekmesini göster"""
        self.notebook.select(1)  # İkinci sekme (1) sonuçlar sekmesi
    
    def _toggle_email_option(self):
        """E-posta seçimi değiştiğinde website seçimini kontrol et"""
        if self.collect_email_var.get():
            # E-posta toplanacaksa websiteyi de seçili hale getir
            self.collect_website_var.set(True)
            self.email_info_label.configure(fg="black")
        else:
            # E-posta toplanmayacaksa bilgiyi gri yap
            self.email_info_label.configure(fg="gray")
    
    def process_queue(self):
        """Mesaj kuyruğundan ileti işleme"""
        try:
            while True:
                msg_type, msg = self.message_queue.get_nowait()
                if msg_type == "status":
                    self.status_text.log(msg)
                    self.status_label.config(text=msg)
                elif msg_type == "progress":
                    self.progress['value'] = msg
                    self.progress_text.set(f"İşlem: {msg}/{self.progress['maximum']}")
                elif msg_type == "max_progress":
                    self.progress['maximum'] = msg
                elif msg_type == "enable_start":
                    self.start_button.config(state='normal')
                    self.stop_button.config(state='disabled')
                    self.export_button.config(state='normal' if self.data_manager.has_data() else 'disabled')
                elif msg_type == "disable_start":
                    self.start_button.config(state='disabled')
                    self.stop_button.config(state='normal')
                    self.export_button.config(state='disabled')
                    # Sonuçlar sekmesine otomatik geçiş
                    self._show_results_tab()
        except queue.Empty:
            pass
        self.window.after(100, self.process_queue)

    def update_status(self, message):
        """Durum güncellemesi"""
        self.message_queue.put(("status", message))

    def clear_logs(self):
        """Log alanını temizle"""
        self.status_text.clear()
        self.update_status("Loglar temizlendi.")
    
    def start_thread(self):
        """Tarama işlemini başlat"""
        # Giriş kontrolü
        search_term = self.search_entry.get().strip()
        city = self.city_entry.get().strip()
        
        if not search_term:
            messagebox.showwarning("Uyarı", "Lütfen aranacak kelimeyi girin.")
            return
            
        if not city:
            messagebox.showwarning("Uyarı", "Lütfen şehir bilgisini girin.")
            return
            
        try:
            max_business = int(self.max_business_var.get())
            if max_business <= 0:
                raise ValueError("Pozitif sayı girilmeli")
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir maksimum işletme sayısı girin.")
            return
        
        # UI durumunu güncelle
        self.message_queue.put(("disable_start", None))
        self.message_queue.put(("progress", 0))
        self.is_running = True
        
        # Veri toplama seçenekleri
        data_options = {
            'collect_address': self.collect_address_var.get(),
            'collect_phone': self.collect_phone_var.get(),
            'collect_website': self.collect_website_var.get(),
            'collect_email': self.collect_email_var.get()
        }
        
        # E-posta seçiliyse websiteyi de zorla seç
        if data_options['collect_email']:
            data_options['collect_website'] = True
            self.collect_website_var.set(True)
        
        # Tarama işlemini başlat
        thread = threading.Thread(
            target=self.start_scraping,
            args=(search_term, city, max_business, data_options)
        )
        thread.daemon = True
        thread.start()
        
    def start_scraping(self, search_term, city, max_business, data_options):
        """Tarama işlemini gerçekleştir"""
        try:
            # Tarayıcıyı başlat
            self.update_status(f"Tarama başlatılıyor: {search_term}, {city}")
            self.message_queue.put(("max_progress", max_business))
            
            # Scraper'ı oluştur
            scraper = MapsScraper(
                queue_handler=self.message_queue
            )
            
            # Veri yöneticisini temizle
            self.data_manager.clear_data()
            
            # Tarama işlemini başlat
            results = scraper.scrape(
                search_term=search_term,
                city=city,
                max_items=max_business,
                is_running_check=lambda: self.is_running,
                data_options=data_options
            )
            
            # Sonuçları kaydet
            if results:
                self.data_manager.set_data(results)
                self.update_status(f"Toplam {len(results)} işletme verisi toplandı.")
                self.message_queue.put(("enable_start", None))
            else:
                self.update_status("Hiç veri bulunamadı!")
                messagebox.showwarning("Uyarı", "Hiç veri bulunamadı!")
                self.message_queue.put(("enable_start", None))
                
        except Exception as e:
            self.update_status(f"Genel hata: {str(e)}")
            messagebox.showerror("Hata", f"Bir hata oluştu: {str(e)}")
            self.message_queue.put(("enable_start", None))
        finally:
            self.is_running = False
            self.update_status("İşlem tamamlandı.")
            self.message_queue.put(("enable_start", None))
    
    def stop_scraping(self):
        """Tarama işlemini durdur"""
        self.is_running = False
        self.update_status("Kullanıcı tarafından durduruldu. İşlemler sonlanıyor...")
    
    def export_results(self):
        """Sonuçları dışa aktar"""
        if not self.data_manager.has_data():
            messagebox.showwarning("Uyarı", "Dışa aktarılacak veri bulunamadı!")
            return
        
        try:
            file_path = self.data_manager.export_data()
            self.update_status(f"Veriler {file_path} dosyasına kaydedildi!")
            messagebox.showinfo("Başarılı", f"Veriler {file_path} dosyasına kaydedildi!")
        except Exception as e:
            self.update_status(f"Dışa aktarma hatası: {str(e)}")
            messagebox.showerror("Hata", f"Dışa aktarma sırasında hata oluştu: {str(e)}")
    
    def run(self):
        """Uygulamayı başlat"""
        self.window.mainloop()