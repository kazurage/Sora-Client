import time
import subprocess
import socket
import os
import sys
from pathlib import Path

def check_internet_connection():
    """Проверяет подключение к интернету"""
    try:
        # Пытаемся подключиться к Google DNS
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except (socket.error, OSError):
        try:
            # Пытаемся подключиться к Cloudflare DNS как альтернативу
            socket.create_connection(("1.1.1.1", 53), timeout=5)
            return True
        except (socket.error, OSError):
            return False

def launch_program(program_path):
    """Запускает программу по указанному пути"""
    try:
        # Проверяем существует ли файл
        if not os.path.exists(program_path):
            print(f"Ошибка: Файл {program_path} не найден!")
            return False
        
        # Запускаем программу
        print(f"Запускаю программу: {program_path}")
        subprocess.Popen([program_path], shell=True)
        return True
    except Exception as e:
        print(f"Ошибка при запуске программы: {e}")
        return False

def main():
    # Путь к программе
    program_path = r"C:\Program Files (x86)\corelink\corelink.exe"
    
    print("Программа запущена. Ожидание 3 минуты...")
    print("Для принудительного завершения нажмите Ctrl+C")
    
    try:
        # Ждем 3 минуты (180 секунд)
        for i in range(180, 0, -1):
            print(f"\rОсталось секунд: {i}", end="", flush=True)
            time.sleep(1)
        
        print("\n\nВремя ожидания истекло. Проверяю подключение к интернету...")
        
        # Проверяем интернет-соединение
        while True:
            if check_internet_connection():
                print("✓ Интернет-соединение активно!")
                print("Запускаю программу...")
                
                if launch_program(program_path):
                    print("✓ Программа успешно запущена!")
                    break
                else:
                    print("✗ Не удалось запустить программу")
                    break
            else:
                print("✗ Нет подключения к интернету. Повторная проверка через 1 минуту...")
                time.sleep(60)  # Ждем 1 минуту
    
    except KeyboardInterrupt:
        print("\n\nПрограмма была остановлена пользователем.")
        sys.exit(0)
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()