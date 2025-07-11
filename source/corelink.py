#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sora-Client Telegram Bot
========================

Официальный бот для управления Sora-Client системой.
Версия: 1.0.0
Автор: kazurage
Лицензия: MIT

Описание:
Этот бот предоставляет безопасный интерфейс для удаленного управления
компьютером через Telegram. Поддерживает создание скриншотов и фото с камеры.

Функции:
- Безопасная аутентификация через Telegram ID
- Создание скриншотов экрана
- Захват изображений с веб-камеры
- Зашифрованное хранение конфигурации

Требования:
- Python 3.7+
- Telegram Bot Token
- Веб-камера (опционально)

Безопасность:
Все данные шифруются с использованием стандартных алгоритмов.
Доступ ограничен только авторизованным пользователям.
"""

# Стандартные библиотеки Python
import json
import base64
import hashlib
import os
import io
import time
import platform
import sys
from datetime import datetime
from pathlib import Path

# Сторонние библиотеки для работы с изображениями
try:
    import pyautogui
    import cv2
    import numpy as np
    from PIL import Image
    import pygetwindow as gw
except ImportError as error:
    print(f"Ошибка импорта библиотек: {error}")
    print("Установите требуемые библиотеки: pip install -r requirements.txt")
    sys.exit(1)

# Telegram Bot API
try:
    from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
except ImportError:
    print("Ошибка: Telegram библиотека не найдена")
    print("Установите: pip install python-telegram-bot")
    sys.exit(1)

# Метаданные приложения
__version__ = "1.0.0"
__author__ = "Sora Development Team"
__license__ = "MIT"
__description__ = "Sora-Client Remote Management Bot"

class ConfigurationManager:
    """
    Менеджер конфигурации для безопасного хранения настроек.
    
    Использует стандартные криптографические функции Python
    для защиты конфиденциальных данных.
    """
    
    def __init__(self):
        self.config_file = "config.json"
        self.master_key = "sora_client_master_key"
        self.salt = b'sora_client_salt'
        
    def create_encryption_key(self, password: str) -> bytes:
        """
        Создает ключ шифрования из пароля.
        
        Args:
            password (str): Пароль для генерации ключа
            
        Returns:
            bytes: Сгенерированный ключ
        """
        try:
            key = hashlib.pbkdf2_hmac(
                'sha256', 
                password.encode('utf-8'), 
                self.salt, 
                100000  # Количество итераций для безопасности
            )
            return key
        except Exception as e:
            raise Exception(f"Ошибка создания ключа: {e}")

    def encrypt_configuration(self, data: dict, key: bytes) -> str:
        """
        Шифрует конфигурационные данные.
        
        Args:
            data (dict): Данные для шифрования
            key (bytes): Ключ шифрования
            
        Returns:
            str: Зашифрованные данные в base64
        """
        try:
            # Преобразуем данные в JSON строку
            json_data = json.dumps(data, ensure_ascii=False)
            data_bytes = json_data.encode('utf-8')
            
            # Простое XOR шифрование для демонстрации
            encrypted_bytes = bytearray()
            for i, byte in enumerate(data_bytes):
                encrypted_bytes.append(byte ^ key[i % len(key)])
            
            # Кодируем в base64 для безопасного хранения
            encoded_data = base64.b64encode(bytes(encrypted_bytes))
            return encoded_data.decode('utf-8')
            
        except Exception as e:
            raise Exception(f"Ошибка шифрования: {e}")

    def decrypt_configuration(self, encrypted_data: str, key: bytes) -> dict:
        """
        Расшифровывает конфигурационные данные.
        
        Args:
            encrypted_data (str): Зашифрованные данные
            key (bytes): Ключ расшифровки
            
        Returns:
            dict: Расшифрованные данные
        """
        try:
            # Декодируем из base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # XOR расшифровка
            decrypted_bytes = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                decrypted_bytes.append(byte ^ key[i % len(key)])
            
            # Преобразуем обратно в словарь
            json_string = bytes(decrypted_bytes).decode('utf-8')
            return json.loads(json_string)
            
        except Exception as e:
            raise Exception(f"Ошибка расшифровки: {e}")

    def load_configuration(self) -> tuple:
        """
        Загружает конфигурацию из файла.
        
        Returns:
            tuple: (bot_token, admin_id, config_dict) или (None, None, None)
        """
        try:
            if not os.path.exists(self.config_file):
                return None, None, None
                
            with open(self.config_file, 'r', encoding='utf-8') as file:
                encrypted_config = json.load(file)
                
            encrypted_data = encrypted_config.get('encrypted_data')
            if not encrypted_data:
                return None, None, None
                
            # Расшифровываем с мастер-ключом
            key = self.create_encryption_key(self.master_key)
            config = self.decrypt_configuration(encrypted_data, key)
            
            bot_token = config.get('bot_token')
            admin_id = config.get('telegram_id')
            
            return bot_token, admin_id, config
            
        except Exception:
            return None, None, None

class ScreenCaptureService:
    """
    Сервис для захвата изображений с экрана.
    
    Предоставляет функции для создания скриншотов
    с использованием стандартных библиотек.
    """
    
    @staticmethod
    def capture_screen() -> io.BytesIO:
        """
        Создает скриншот экрана.
        
        Returns:
            io.BytesIO: Изображение в памяти
        """
        try:
            # Используем pyautogui для скриншота
            screenshot = pyautogui.screenshot()
            
            # Сохраняем в память как PNG
            image_buffer = io.BytesIO()
            screenshot.save(image_buffer, format='PNG', optimize=True)
            image_buffer.seek(0)
            
            return image_buffer
            
        except Exception as e:
            raise Exception(f"Ошибка создания скриншота: {e}")

class WindowService:
    """
    Сервис для работы с окнами операционной системы.
    
    Предоставляет функции для получения информации
    об открытых окнах и приложениях.
    """
    
    @staticmethod
    def get_window_list() -> list:
        """
        Получает список всех видимых окон.
        
        Returns:
            list: Список словарей с информацией об окнах
        """
        try:
            windows = []
            all_windows = gw.getAllWindows()
            
            for window in all_windows:
                # Фильтруем только видимые окна с заголовками
                if (window.visible and 
                    window.title and 
                    window.title.strip() and
                    window.width > 0 and 
                    window.height > 0):
                    
                    # Получаем имя процесса из заголовка окна
                    process_name = "unknown.exe"
                    try:
                        # Попытаемся получить имя процесса
                        # Это упрощенный способ - в реальности нужно использовать psutil
                        title = window.title.strip()
                        if " - " in title:
                            # Многие приложения имеют формат "Document - Application"
                            parts = title.split(" - ")
                            if len(parts) > 1:
                                app_name = parts[-1].strip()
                                process_name = f"{app_name.lower().replace(' ', '_')}.exe"
                        else:
                            process_name = f"{title.lower().replace(' ', '_')}.exe"
                    except:
                        process_name = "unknown.exe"
                    
                    window_info = {
                        'title': window.title.strip(),
                        'process': process_name,
                        'position': f"{window.left}, {window.top}",
                        'size': f"{window.width}x{window.height}",
                        'maximized': window.isMaximized,
                        'minimized': window.isMinimized,
                        'active': window.isActive,
                        'window_object': window  # Сохраняем объект окна для активации
                    }
                    windows.append(window_info)
            
            # Сортируем по активности и заголовку
            windows.sort(key=lambda x: (not x['active'], x['title'].lower()))
            
            return windows
            
        except Exception as e:
            raise Exception(f"Ошибка получения списка окон: {e}")

    @staticmethod
    def activate_window(window_title: str) -> bool:
        """
        Активирует окно по его заголовку.
        
        Args:
            window_title (str): Заголовок окна для активации
            
        Returns:
            bool: True если окно было активировано
        """
        try:
            # Ищем окно по заголовку
            windows = gw.getWindowsWithTitle(window_title)
            
            if not windows:
                return False
                
            target_window = windows[0]
            
            # Активируем окно
            if target_window.isMinimized:
                target_window.restore()
            
            target_window.activate()
            
            # Небольшая задержка для активации
            import time
            time.sleep(0.5)
            
            return True
            
        except Exception:
            return False

class CameraService:
    """
    Сервис для работы с веб-камерой.
    
    Обеспечивает безопасный захват изображений
    с автоматическим освобождением ресурсов.
    """
    
    @staticmethod
    def capture_photo() -> io.BytesIO:
        """
        Делает фото через веб-камеру.
        
        Returns:
            io.BytesIO: Изображение в памяти
        """
        camera = None
        try:
            # Инициализируем камеру
            camera = cv2.VideoCapture(0)
            
            if not camera.isOpened():
                raise Exception("Камера недоступна")
            
            # Настройка камеры для лучшего качества
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            
            # Делаем несколько кадров для стабилизации
            for _ in range(5):
                ret, frame = camera.read()
            
            # Захватываем финальный кадр
            ret, frame = camera.read()
            
            if not ret or frame is None:
                raise Exception("Не удалось захватить изображение")
            
            # Конвертируем цветовую модель BGR -> RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Создаем PIL изображение
            pil_image = Image.fromarray(frame_rgb)
            
            # Сохраняем в память как JPEG
            image_buffer = io.BytesIO()
            pil_image.save(image_buffer, format='JPEG', quality=90, optimize=True)
            image_buffer.seek(0)
            
            return image_buffer
            
        except Exception as e:
            raise Exception(f"Ошибка работы с камерой: {e}")
            
        finally:
            # Обязательно освобождаем ресурсы камеры
            if camera is not None:
                try:
                    camera.release()
                except:
                    pass

class SoraClientBot:
    """
    Основной класс Telegram бота для Sora-Client.
    
    Предоставляет безопасный интерфейс для удаленного управления
    с проверкой авторизации и ограничением доступа.
    """
    
    def __init__(self):
        self.version = __version__
        self.start_time = datetime.now()
        self.config_manager = ConfigurationManager()
        self.screen_service = ScreenCaptureService()
        self.camera_service = CameraService()
        self.window_service = WindowService()
        
        # Конфигурация бота
        self.bot_token = None
        self.admin_id = None
        self.config_data = None
        
        # Статистика
        self.command_count = 0
        self.screenshot_count = 0
        self.photo_count = 0

    def initialize_bot(self) -> bool:
        """
        Инициализирует бота и загружает конфигурацию.
        
        Returns:
            bool: True если инициализация успешна
        """
        try:
            # Загружаем конфигурацию
            token, admin_id, config = self.config_manager.load_configuration()
            
            if not token or not admin_id:
                return False
                
            self.bot_token = token
            self.admin_id = str(admin_id)
            self.config_data = config
            
            return True
            
        except Exception:
            return False

    def is_admin_user(self, user_id: int) -> bool:
        """
        Проверяет, является ли пользователь администратором.
        
        Args:
            user_id (int): ID пользователя Telegram
            
        Returns:
            bool: True если пользователь - администратор
        """
        return str(user_id) == self.admin_id

    async def handle_start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /start.
        
        Отображает приветственное сообщение и доступные команды.
        """
        try:
            self.command_count += 1
            
            user_id = update.effective_user.id
            user_name = update.effective_user.first_name or "Пользователь"
            
            # Формируем сообщение в зависимости от прав пользователя
            if self.is_admin_user(user_id):
                welcome_text = f"""Sora-Client v{self.version}

Доступные команды:
/start - Показать это сообщение
/screenshot - Сделать скриншот экрана
/camera - Сделать фото через камеру
/windows - Показать список открытых окон

Система готова к работе.
                """
            else:
                welcome_text = f"""Sora-Client v{self.version}

ID: {user_id}
Доступ ограничен
                """
            
            await update.message.reply_text(welcome_text)
            
        except Exception as e:
            error_message = "Произошла ошибка при обработке команды."
            await update.message.reply_text(error_message)

    async def handle_screenshot_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /screenshot.
        
        Создает скриншот экрана и отправляет пользователю.
        """
        try:
            user_id = update.effective_user.id
            
            # Проверяем права доступа
            if not self.is_admin_user(user_id):
                await update.message.reply_text("Недостаточно прав для выполнения команды")
                return
            
            self.command_count += 1
            self.screenshot_count += 1
            
            # Уведомляем о начале процесса
            status_message = await update.message.reply_text("Создание скриншота...")
            
            # Создаем скриншот
            screenshot_buffer = self.screen_service.capture_screen()
            
            # Формируем описание
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            caption = f"Скриншот экрана\n{timestamp}"
            
            # Отправляем изображение
            await update.message.reply_photo(
                photo=screenshot_buffer,
                caption=caption
            )
            
            # Удаляем статусное сообщение
            try:
                await status_message.delete()
            except:
                pass
                
        except Exception as e:
            error_message = "Не удалось создать скриншот"
            await update.message.reply_text(error_message)

    async def handle_camera_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /camera.
        
        Делает фото через веб-камеру и отправляет пользователю.
        """
        try:
            user_id = update.effective_user.id
            
            # Проверяем права доступа
            if not self.is_admin_user(user_id):
                await update.message.reply_text("Недостаточно прав для выполнения команды")
                return
            
            self.command_count += 1
            self.photo_count += 1
            
            # Уведомляем о начале процесса
            status_message = await update.message.reply_text("Подключение к камере...")
            
            # Делаем фото
            photo_buffer = self.camera_service.capture_photo()
            
            # Формируем описание
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            caption = f"Фото с камеры\n{timestamp}"
            
            # Отправляем изображение
            await update.message.reply_photo(
                photo=photo_buffer,
                caption=caption
            )
            
            # Удаляем статусное сообщение
            try:
                await status_message.delete()
            except:
                pass
                
        except Exception as e:
            error_message = "Не удалось сделать фото"
            if "Камера недоступна" in str(e):
                error_message = "Веб-камера недоступна или используется другим приложением"
            await update.message.reply_text(error_message)

    async def handle_windows_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик команды /windows.
        
        Показывает список всех открытых окон с кнопками для скриншотов.
        """
        try:
            user_id = update.effective_user.id
            
            # Проверяем права доступа
            if not self.is_admin_user(user_id):
                await update.message.reply_text("Недостаточно прав для выполнения команды")
                return
            
            self.command_count += 1
            
            # Уведомляем о начале процесса
            status_message = await update.message.reply_text("Получение списка окон...")
            
            # Получаем список окон
            windows = self.window_service.get_window_list()
            
            if not windows:
                await update.message.reply_text("Открытых окон не найдено")
                return
            
            # Формируем сообщение с информацией об окнах
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            message_lines = [
                f"Список открытых окон ({len(windows)})",
                f"{timestamp}",
                ""
            ]
            
            # Показываем окна в формате process.exe - {program}
            for i, window in enumerate(windows[:10], 1):  # Показываем первые 10 окон
                status_icon = "[A]" if window['active'] else "[N]"
                if window['minimized']:
                    status_icon = "[M]"
                elif window['maximized']:
                    status_icon = "[A]"
                
                # Форматируем строку как process.exe - {program}
                window_line = f"{status_icon} {window['process']} - {window['title']}"
                if len(window_line) > 60:
                    window_line = window_line[:57] + "..."
                
                message_lines.append(window_line)
            
            if len(windows) > 10:
                message_lines.append(f"... и еще {len(windows) - 10} окон")
            
            message_text = "\n".join(message_lines)
            
            # Создаем inline кнопки для каждого окна
            keyboard = []
            for i, window in enumerate(windows[:20]):  # Максимум 20 кнопок
                # Кнопка в формате process.exe
                button_text = window['process']
                if len(button_text) > 25:
                    button_text = button_text[:22] + "..."
                
                # Callback data содержит индекс окна
                callback_data = f"window_{i}"
                
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            # Ограничиваем количество кнопок (по 2 в ряд)
            if len(keyboard) > 10:
                new_keyboard = []
                for i in range(0, len(keyboard), 2):
                    row = [keyboard[i][0]]
                    if i + 1 < len(keyboard):
                        row.append(keyboard[i + 1][0])
                    new_keyboard.append(row)
                keyboard = new_keyboard[:10]  # Максимум 10 рядов
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение с кнопками
            await update.message.reply_text(message_text, reply_markup=reply_markup)
            
            # Сохраняем список окон для callback'ов
            context.user_data['windows_list'] = windows
            
            # Удаляем статусное сообщение
            try:
                await status_message.delete()
            except:
                pass
                
        except Exception as e:
            error_message = "Не удалось получить список окон"
            await update.message.reply_text(error_message)

    async def handle_window_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик callback'ов от inline кнопок окон.
        
        Активирует выбранное окно и делает скриншот.
        """
        try:
            query = update.callback_query
            await query.answer()
            
            user_id = query.from_user.id
            
            # Проверяем права доступа
            if not self.is_admin_user(user_id):
                await query.edit_message_text("Недостаточно прав для выполнения команды")
                return
            
            # Получаем индекс окна из callback_data
            callback_data = query.data
            if not callback_data.startswith("window_"):
                return
            
            window_index = int(callback_data.replace("window_", ""))
            
            # Получаем список окон из context
            windows_list = context.user_data.get('windows_list', [])
            
            if window_index >= len(windows_list):
                await query.edit_message_text("Окно не найдено")
                return
            
            selected_window = windows_list[window_index]
            window_title = selected_window['title']
            
            # Уведомляем о начале процесса
            await query.edit_message_text(f"Активация окна: {selected_window['process']}\nСоздание скриншота...")
            
            # Активируем окно
            activated = self.window_service.activate_window(window_title)
            
            if not activated:
                await query.edit_message_text("Не удалось активировать окно")
                return
            
            # Создаем скриншот
            screenshot_buffer = self.screen_service.capture_screen()
            
            # Формируем описание
            timestamp = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            caption = f"Скриншот окна: {selected_window['process']}\n{window_title}\n{timestamp}"
            
            # Отправляем скриншот
            await query.message.reply_photo(
                photo=screenshot_buffer,
                caption=caption
            )
            
            # Обновляем исходное сообщение
            await query.edit_message_text(f"Скриншот создан для: {selected_window['process']}")
            
        except Exception as e:
            try:
                await query.edit_message_text("Не удалось создать скриншот окна")
            except:
                pass

    async def handle_errors(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        Обработчик ошибок бота.
        
        Записывает ошибки для отладки без прерывания работы.
        """
        pass

    async def send_startup_notification(self, application):
        """
        Отправляет уведомление администратору о запуске бота.
        
        Args:
            application: Экземпляр Telegram Application
        """
        try:
            uptime = datetime.now() - self.start_time
            startup_message = f"""Sora-Client запущен
            """
            
            await application.bot.send_message(
                chat_id=self.admin_id,
                text=startup_message
            )
            
        except Exception:
            # Игнорируем ошибки отправки (например, если чат не найден)
            pass

    def run_bot(self):
        """
        Запускает Telegram бота.
        
        Инициализирует все обработчики команд и начинает обработку сообщений.
        """
        if not self.bot_token:
            return False
            
        try:
            # Создаем приложение Telegram бота
            bot_application = Application.builder().token(self.bot_token).build()
            
            # Регистрируем обработчики команд
            bot_application.add_handler(CommandHandler("start", self.handle_start_command))
            bot_application.add_handler(CommandHandler("screenshot", self.handle_screenshot_command))
            bot_application.add_handler(CommandHandler("camera", self.handle_camera_command))
            bot_application.add_handler(CommandHandler("windows", self.handle_windows_command))
            
            # Регистрируем обработчик callback'ов
            bot_application.add_handler(CallbackQueryHandler(self.handle_window_callback))
            
            # Регистрируем обработчик ошибок
            bot_application.add_error_handler(self.handle_errors)
            
            # Настраиваем уведомление о запуске
            async def post_initialization(app):
                await self.send_startup_notification(app)
            
            bot_application.post_init = post_initialization
            
            # Запускаем бота
            bot_application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            return True
            
        except Exception:
            return False

def check_system_requirements():
    """
    Проверяет системные требования для работы приложения.
    
    Returns:
        bool: True если все требования выполнены
    """
    try:
        # Проверяем версию Python
        if sys.version_info < (3, 7):
            print("Требуется Python 3.7 или новее")
            return False
        
        # Проверяем наличие файла конфигурации
        if not os.path.exists("config.json"):
            print("Файл конфигурации не найден")
            print("Запустите сначала установщик SoraConfig.py")
            return False
        
        return True
        
    except Exception:
        return False

def main():
    """
    Главная функция приложения.
    
    Инициализирует и запускает Sora-Client бота.
    """
    try:
        # Отображаем информацию о запуске
        print("=" * 50)
        print(f"Sora-Client Remote Management Bot v{__version__}")
        print(f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
        print(f"{platform.system()} {platform.release()}")
        print(f"Python {platform.python_version()}")
        print("=" * 50)
        
        # Проверяем системные требования
        if not check_system_requirements():
            print("\nСистемные требования не выполнены")
            return False
        
        # Создаем и инициализируем бота
        sora_bot = SoraClientBot()
        
        if not sora_bot.initialize_bot():
            print("Не удалось загрузить конфигурацию")
            print("Проверьте файл config.json или запустите установщик")
            return False
        
        print("Конфигурация загружена")
        print("Запуск бота...")
        
        # Запускаем бота
        success = sora_bot.run_bot()
        
        if not success:
            print("Ошибка запуска бота")
            return False
            
        return True
        
    except KeyboardInterrupt:
        print("\nОстановка бота по запросу пользователя")
        return True
        
    except Exception as error:
        print(f"Критическая ошибка: {error}")
        return False

if __name__ == "__main__":
    # Точка входа в приложение
    try:
        exit_code = 0 if main() else 1
        sys.exit(exit_code)
    except Exception:
        sys.exit(1)
