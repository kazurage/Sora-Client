import os
import zipfile
import requests
import shutil
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import json
import base64
import hashlib
import tempfile
import winreg
import subprocess

# Путь установки в Program Files (x86)
program_files_path = r"C:\Program Files (x86)"
install_path = os.path.join(program_files_path, "Corelink")

zip_url = "https://github.com/kazurage/Sora-Client/releases/download/python/SoraClient.zip"

class SoraInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Sora-Client Установщик")
        self.root.geometry("500x450")
        self.root.resizable(False, False)
        
        # Темная тема
        self.root.configure(bg='#1a1a1a')
        
        # Центрируем окно
        self.root.eval('tk::PlaceWindow . center')
        
        self.setup_ui()
        
    def setup_ui(self):
        # Главный фрейм с темным фоном
        main_frame = tk.Frame(self.root, bg='#1a1a1a', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title_label = tk.Label(main_frame, text="🚀 Sora-Client", 
                              font=("Arial", 18, "bold"), 
                              fg='white', bg='#1a1a1a')
        title_label.pack(pady=(0, 30))
        
        # Поле для токена
        token_label = tk.Label(main_frame, text="🔑 Token телеграм бота", 
                              font=("Arial", 10), 
                              fg='white', bg='#1a1a1a')
        token_label.pack(anchor='w', pady=(0, 5))
        
        self.token_entry = tk.Entry(main_frame, width=50, show="*", 
                                   font=("Arial", 10), 
                                   bg='#404040', fg='white', 
                                   insertbackground='white',
                                   relief='flat', bd=5)
        self.token_entry.pack(fill=tk.X, pady=(0, 20))
        
        # Добавляем поддержку горячих клавиш для поля токена
        self.token_entry.bind('<Control-v>', self.paste_text)
        self.token_entry.bind('<Control-c>', self.copy_text)
        self.token_entry.bind('<Control-a>', self.select_all)
        self.token_entry.bind('<Control-x>', self.cut_text)
        self.token_entry.bind('<Button-3>', self.show_context_menu)
        
        # Поле для Telegram ID
        telegram_id_label = tk.Label(main_frame, text="👤 Ваш Telegram ID", 
                                     font=("Arial", 10), 
                                     fg='white', bg='#1a1a1a')
        telegram_id_label.pack(anchor='w', pady=(0, 5))
        
        self.telegram_id_entry = tk.Entry(main_frame, width=50, 
                                         font=("Arial", 10), 
                                         bg='#404040', fg='white', 
                                         insertbackground='white',
                                         relief='flat', bd=5)
        self.telegram_id_entry.pack(fill=tk.X, pady=(0, 30))
        
        # Добавляем поддержку горячих клавиш для поля Telegram ID
        self.telegram_id_entry.bind('<Control-v>', self.paste_text)
        self.telegram_id_entry.bind('<Control-c>', self.copy_text)
        self.telegram_id_entry.bind('<Control-a>', self.select_all)
        self.telegram_id_entry.bind('<Control-x>', self.cut_text)
        self.telegram_id_entry.bind('<Button-3>', self.show_context_menu)
        
        # Кнопка установки
        self.install_button = tk.Button(main_frame, text="📦 Начать установку", 
                                       command=self.start_installation,
                                       font=("Arial", 12, "bold"),
                                       bg='#2d2d2d', fg='white',
                                       activebackground='#404040',
                                       activeforeground='white',
                                       relief='flat', bd=0,
                                       padx=20, pady=10)
        self.install_button.pack(pady=(0, 20))
        
        # Область логов
        log_label = tk.Label(main_frame, text="📝 Логи установки", 
                            font=("Arial", 10), 
                            fg='white', bg='#1a1a1a')
        log_label.pack(anchor='w', pady=(0, 5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, width=60, height=12,
                                                 font=("Consolas", 9),
                                                 bg='#000000', fg='white',
                                                 insertbackground='white',
                                                 relief='flat', bd=5)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log_message(self, message):
        """Добавляет сообщение в лог"""
        def update_log():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
    
    def paste_text(self, event):
        """Вставляет текст из буфера обмена"""
        try:
            text = self.root.clipboard_get()
            widget = event.widget
            widget.insert(tk.INSERT, text)
            return "break"
        except:
            pass
    
    def copy_text(self, event):
        """Копирует выделенный текст в буфер обмена"""
        try:
            widget = event.widget
            if widget.selection_present():
                text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
            return "break"
        except:
            pass
    
    def cut_text(self, event):
        """Вырезает выделенный текст в буфер обмена"""
        try:
            widget = event.widget
            if widget.selection_present():
                text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
            return "break"
        except:
            pass
    
    def select_all(self, event):
        """Выделяет весь текст в поле"""
        try:
            widget = event.widget
            widget.select_range(0, tk.END)
            return "break"
        except:
            pass
    
    def show_context_menu(self, event):
        """Показывает контекстное меню при нажатии правой кнопки мыши"""
        try:
            context_menu = tk.Menu(self.root, tearoff=0, 
                                 bg='#2d2d2d', fg='white',
                                 activebackground='#404040',
                                 activeforeground='white',
                                 relief='flat', bd=1)
            
            context_menu.add_command(label="📋 Вставить", 
                                   command=lambda: self.paste_text_from_menu(event.widget))
            context_menu.add_command(label="📄 Копировать", 
                                   command=lambda: self.copy_text_from_menu(event.widget))
            context_menu.add_command(label="✂️ Вырезать", 
                                   command=lambda: self.cut_text_from_menu(event.widget))
            context_menu.add_separator()
            context_menu.add_command(label="🔘 Выделить все", 
                                   command=lambda: self.select_all_from_menu(event.widget))
            
            context_menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            pass
    
    def paste_text_from_menu(self, widget):
        """Вставляет текст из буфера обмена через меню"""
        try:
            text = self.root.clipboard_get()
            widget.insert(tk.INSERT, text)
        except:
            pass
    
    def copy_text_from_menu(self, widget):
        """Копирует выделенный текст в буфер обмена через меню"""
        try:
            if widget.selection_present():
                text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
        except:
            pass
    
    def cut_text_from_menu(self, widget):
        """Вырезает выделенный текст в буфер обмена через меню"""
        try:
            if widget.selection_present():
                text = widget.selection_get()
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
                widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except:
            pass
    
    def select_all_from_menu(self, widget):
        """Выделяет весь текст в поле через меню"""
        try:
            widget.select_range(0, tk.END)
        except:
            pass
        
    def check_admin_rights(self):
        """Проверка прав администратора"""
        try:
            test_file = os.path.join(program_files_path, "test_access.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except (PermissionError, OSError):
            return False
            
    def generate_key(self, password):
        """Генерирует ключ для шифрования на основе пароля"""
        salt = b'sora_client_salt'
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return key

    def encrypt_data(self, data, key):
        """Шифрует данные"""
        try:
            data_bytes = json.dumps(data).encode()
            encrypted = bytearray()
            for i, byte in enumerate(data_bytes):
                encrypted.append(byte ^ key[i % len(key)])
            return base64.b64encode(bytes(encrypted)).decode()
        except Exception as e:
            raise Exception(f"Ошибка шифрования: {e}")

    def save_credentials(self, token, telegram_id):
        """Сохраняет зашифрованные данные в JSON файл"""
        try:
            key = self.generate_key("sora_client_master_key")
            
            data = {
                "bot_token": token,
                "telegram_id": telegram_id,
                "created_at": "2024-01-01",
                "version": "1.0"
            }
            
            encrypted_data = self.encrypt_data(data, key)
            
            config_file = os.path.join(install_path, "config.json")
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({"encrypted_data": encrypted_data}, f, indent=2)
            
            self.log_message("🔑 Данные зашифрованы и сохранены в config.json")
        except Exception as e:
            self.log_message(f"❌ Ошибка сохранения данных: {e}")

    def move_files_from_subfolder(self):
        """Перемещает файлы из папки SoraClient в корень corelink"""
        try:
            sora_client_path = os.path.join(install_path, "SoraClient")
            
            if not os.path.exists(sora_client_path):
                self.log_message("⚠️ Папка SoraClient не найдена")
                return False
                
            self.log_message("🚚 Начинаем перемещение файлов из SoraClient...")
            
            # Перемещаем все файлы и папки из SoraClient в корень corelink
            moved_files = 0
            for item in os.listdir(sora_client_path):
                source_path = os.path.join(sora_client_path, item)
                dest_path = os.path.join(install_path, item)
                
                try:
                    # Если файл уже существует в назначении, удаляем его
                    if os.path.exists(dest_path):
                        if os.path.isfile(dest_path):
                            os.remove(dest_path)
                        else:
                            shutil.rmtree(dest_path)
                    
                    # Перемещаем файл/папку
                    shutil.move(source_path, dest_path)
                    self.log_message(f"📁 Перемещен: {item}")
                    moved_files += 1
                    
                except Exception as e:
                    self.log_message(f"❌ Ошибка перемещения {item}: {e}")
                    continue
            
            # Удаляем пустую папку SoraClient
            try:
                os.rmdir(sora_client_path)
                self.log_message("🗑️ Папка SoraClient удалена")
            except Exception as e:
                self.log_message(f"⚠️ Не удалось удалить папку SoraClient: {e}")
            
            self.log_message(f"✅ Перемещено файлов: {moved_files}")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Ошибка при перемещении файлов: {e}")
            return False

    def add_to_autostart(self):
        """Добавляет программу в автозагрузку Windows"""
        try:
            exe_path = os.path.join(install_path, "wintrix.exe")
            
            if not os.path.exists(exe_path):
                self.log_message("⚠️ Файл wintrix.exe не найден, пропускаем автозагрузку")
                return False
            
            self.log_message("🔧 Добавляем в автозагрузку Windows...")
            
            # Добавляем в реестр Windows для автозагрузки
            key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
            value_name = "WinTrix"
            
            try:
                # Открываем ключ реестра
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, exe_path)
                winreg.CloseKey(key)
                
                self.log_message("✅ Программа добавлена в автозагрузку")
                return True
                
            except Exception as e:
                self.log_message(f"❌ Ошибка добавления в автозагрузку: {e}")
                return False
                
        except Exception as e:
            self.log_message(f"❌ Ошибка при добавлении в автозагрузку: {e}")
            return False

    def launch_program(self):
        """Запускает программу wintrix.exe"""
        try:
            exe_path = os.path.join(install_path, "wintrix.exe")
            
            if not os.path.exists(exe_path):
                self.log_message("⚠️ Файл wintrix.exe не найден, не можем запустить")
                return False
            
            self.log_message("🚀 Запускаем wintrix.exe...")
            
            # Запускаем программу
            subprocess.Popen([exe_path], cwd=install_path)
            self.log_message("✅ Программа запущена")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Ошибка при запуске программы: {e}")
            return False

    def download_file(self, url, filename):
        """Скачивает файл с прогрессом"""
        try:
            self.log_message(f"📦 Начинаем скачивание: {url}")
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            self.log_message(f"📊 Скачано: {progress:.1f}%")
            
            self.log_message(f"✅ Файл скачан: {filename}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log_message(f"❌ Ошибка скачивания: {e}")
            return False
        except Exception as e:
            self.log_message(f"❌ Неожиданная ошибка при скачивании: {e}")
            return False

    def extract_zip(self, zip_path, extract_to):
        """Извлекает все файлы из ZIP архива"""
        try:
            self.log_message(f"🗂 Начинаем распаковку: {zip_path}")
            self.log_message(f"📁 Папка назначения: {extract_to}")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Получаем список всех файлов в архиве
                file_list = zip_ref.namelist()
                total_files = len(file_list)
                
                self.log_message(f"📋 Найдено файлов в архиве: {total_files}")
                
                # Извлекаем все файлы
                for i, file_info in enumerate(zip_ref.infolist()):
                    try:
                        # Извлекаем файл
                        zip_ref.extract(file_info, extract_to)
                        self.log_message(f"📄 Извлечен: {file_info.filename}")
                    except Exception as e:
                        self.log_message(f"⚠️ Ошибка извлечения {file_info.filename}: {e}")
                        continue
                
                self.log_message(f"✅ Распаковка завершена")
                return True
                
        except zipfile.BadZipFile:
            self.log_message("❌ Ошибка: Поврежденный ZIP архив")
            return False
        except Exception as e:
            self.log_message(f"❌ Ошибка распаковки: {e}")
            return False
            
    def install_files(self):
        """Основная функция установки"""
        try:
            # Проверка введенных данных
            token = self.token_entry.get().strip()
            telegram_id = self.telegram_id_entry.get().strip()
            
            if not token:
                self.log_message("❌ Ошибка: Не указан Token телеграм бота!")
                messagebox.showerror("Ошибка", "Введите Token телеграм бота!")
                return
            
            if not telegram_id:
                self.log_message("❌ Ошибка: Не указан Telegram ID!")
                messagebox.showerror("Ошибка", "Введите ваш Telegram ID!")
                return
                
            # Проверка, что telegram_id является числом
            try:
                int(telegram_id)
            except ValueError:
                self.log_message("❌ Ошибка: Telegram ID должен быть числом!")
                messagebox.showerror("Ошибка", "Telegram ID должен быть числом!")
                return
                
            self.log_message("🚀 Начинаем установку Sora-Client...")
            self.log_message(f"🔑 Token: {token[:10]}...")
            self.log_message(f"👤 Telegram ID: {telegram_id}")
            
            # Проверка прав администратора
            if not self.check_admin_rights():
                self.log_message("❌ Нет прав для записи в Program Files (x86)")
                messagebox.showerror("Ошибка", "Нет прав для записи в Program Files (x86)\nЗапустите программу от имени администратора!")
                return
                
            self.log_message("✅ Права администратора подтверждены")
            
            # Создаем папку для установки
            if os.path.exists(install_path):
                self.log_message(f"🗂 Папка уже существует: {install_path}")
                # Очищаем папку
                try:
                    shutil.rmtree(install_path)
                    self.log_message("🧹 Старая папка удалена")
                except Exception as e:
                    self.log_message(f"⚠️ Не удалось удалить старую папку: {e}")
            
            os.makedirs(install_path, exist_ok=True)
            self.log_message(f"📁 Создана папка: {install_path}")
            
            # Создаем временный файл для ZIP архива
            temp_zip = os.path.join(tempfile.gettempdir(), "sora_client_temp.zip")
            
            # Скачиваем архив
            if not self.download_file(zip_url, temp_zip):
                self.log_message("❌ Не удалось скачать архив")
                return
            
            # Проверяем размер скачанного файла
            if os.path.exists(temp_zip):
                file_size = os.path.getsize(temp_zip)
                self.log_message(f"📊 Размер скачанного файла: {file_size} байт")
                
                if file_size < 1000:  # Если файл слишком маленький
                    self.log_message("❌ Скачанный файл слишком маленький, возможно ошибка")
                    return
            
            # Распаковываем архив
            if not self.extract_zip(temp_zip, install_path):
                self.log_message("❌ Не удалось распаковать архив")
                return
            
            # Перемещаем файлы из папки SoraClient в корень corelink
            if not self.move_files_from_subfolder():
                self.log_message("⚠️ Не удалось переместить файлы, продолжаем...")
            
            # Сохраняем конфигурацию
            self.save_credentials(token, telegram_id)
            
            # Добавляем в автозагрузку
            self.add_to_autostart()
            
            # Запускаем программу
            self.launch_program()
            
            # Удаляем временный файл
            try:
                os.remove(temp_zip)
                self.log_message("🧹 Временный файл удален")
            except Exception as e:
                self.log_message(f"⚠️ Не удалось удалить временный файл: {e}")
            
            # Показываем содержимое папки установки
            self.log_message("📋 Содержимое папки установки:")
            try:
                for root, dirs, files in os.walk(install_path):
                    level = root.replace(install_path, '').count(os.sep)
                    indent = ' ' * 2 * level
                    self.log_message(f"{indent}📁 {os.path.basename(root)}/")
                    sub_indent = ' ' * 2 * (level + 1)
                    for file in files:
                        self.log_message(f"{sub_indent}📄 {file}")
            except Exception as e:
                self.log_message(f"⚠️ Не удалось показать содержимое: {e}")
            
            self.log_message("🎉 Установка завершена успешно!")
            self.log_message(f"📂 Файлы установлены в: {install_path}")
            self.log_message("🔄 Программа добавлена в автозагрузку и запущена")
            self.log_message("🔄 Окно закроется через 5 секунд...")
            
            # Закрываем окно через 5 секунд
            self.root.after(5000, self.root.quit)
            
        except Exception as e:
            self.log_message(f"❌ Критическая ошибка: {e}")
            messagebox.showerror("Критическая ошибка", f"Произошла критическая ошибка: {e}")
        finally:
            # Восстанавливаем кнопку
            def restore_button():
                self.install_button.config(state="normal", text="📦 Начать установку", bg='#2d2d2d')
            self.root.after(0, restore_button)
            
    def start_installation(self):
        """Запускает установку в отдельном потоке"""
        def update_button():
            self.install_button.config(state="disabled", text="⏳ Устанавливаю...", bg='#555555')
            self.log_text.delete(1.0, tk.END)
        
        update_button()
        
        # Запускаем установку в отдельном потоке
        thread = threading.Thread(target=self.install_files)
        thread.daemon = True
        thread.start()
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SoraInstaller()
    app.run()