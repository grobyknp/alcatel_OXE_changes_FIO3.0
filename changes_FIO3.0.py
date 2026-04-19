#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для изменения данных абонента на АТС Alcatel OXE.
Все IP-адреса и пароли хранятся во внешнем JSON-файле.
IP определяется по коду региона из номера (9xxyyyy, где xx – код).
"""

import tkinter as tk
from tkinter import messagebox
import logging
import os
import re
import time
import telnetlib
import json
from typing import Optional, Tuple, List, Dict

# =============================================================================
# 1. КОНФИГУРАЦИЯ
# =============================================================================

class Config:
    """Хранит настройки и константы."""
    TELNET_PORT = 23
    TELNET_TIMEOUT = 10
    ENTER = b'\r\n'
    SHELL_PROMPT = [b'u1>', b'u2>', b'u12main>']
    ENCODING = 'utf-8'
    LOG_FILE = os.path.expanduser('C:\\alcatel_script\\changes.log')
    SERVERS_JSON_PATH = os.path.expanduser(r'C:\alcatel_script\servers\servers.json')
    DEFAULT_LOGIN = 'mtcl'

# =============================================================================
# 2. ТРАНСЛИТЕРАЦИЯ
# =============================================================================

class Transliterator:
    """Преобразование кириллицы в латиницу."""
    TABLE = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'Kh', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }

    @classmethod
    def convert(cls, text: str) -> str:
        """Преобразует строку из кириллицы в латиницу."""
        return ''.join(cls.TABLE.get(ch, ch) for ch in text)

# =============================================================================
# 3. УПРАВЛЕНИЕ ДАННЫМИ СЕРВЕРОВ
# =============================================================================

class ServerManager:
    """
    Загружает данные из JSON и предоставляет:
    - IP-адрес по коду региона
    - учётные данные по IP
    """
    def __init__(self, json_path: str):
        self.json_path = json_path
        self._servers_cache = None

    def _load_servers(self) -> List[Dict]:
        """Загружает JSON с серверами (кэширует)."""
        if self._servers_cache is None:
            if not os.path.isfile(self.json_path):
                raise FileNotFoundError(f"Файл конфигурации не найден: {self.json_path}")
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._servers_cache = json.load(f)
        return self._servers_cache

    def get_address_by_region(self, region_code: str) -> str:
        """Возвращает IP-адрес сервера по двузначному коду региона."""
        servers = self._load_servers()
        for server in servers:
            if server.get('region_code') == region_code:
                return server['address']
        raise ValueError(f"Регион с кодом {region_code} не найден в {self.json_path}")

    def get_credentials(self, ip: str) -> Tuple[str, str]:
        """Возвращает (логин, пароль) для заданного IP."""
        servers = self._load_servers()
        for server in servers:
            if server.get('address') == ip:
                password = server.get(Config.DEFAULT_LOGIN)
                if password is None:
                    raise ValueError(f"Для IP {ip} отсутствует поле '{Config.DEFAULT_LOGIN}'")
                return Config.DEFAULT_LOGIN, password
        raise ValueError(f"IP {ip} не найден в файле {self.json_path}")

# =============================================================================
# 4. НИЗКОУРОВНЕВАЯ РАБОТА С TELNET
# =============================================================================

class AlcatelSession:
    """Управление Telnet-соединением и отправкой команд."""
    def __init__(self, host: str, login: str, password: str, encoding: str = Config.ENCODING):
        self.host = host
        self.login = login
        self.password = password
        self.encoding = encoding
        self.tn: Optional[telnetlib.Telnet] = None

    def _expect(self, patterns: List[bytes], timeout: int = Config.TELNET_TIMEOUT) -> Tuple[int, bytes]:
        """Ожидает любой из паттернов, возвращает индекс и накопленные данные."""
        end_time = time.time() + timeout
        data = b''
        while time.time() < end_time:
            try:
                chunk = self.tn.read_some()
            except (TimeoutError, EOFError):
                time.sleep(2.1)
                continue
            if chunk:
                data += chunk
                for i, pat in enumerate(patterns):
                    if pat in data:
                        return i, data
        return -1, data

    def _send_command(self, command: str, wait_prompt: bool = True) -> str:
        """Отправляет команду, ожидая приглашения, если wait_prompt=True."""
        logging.info(f"Отправка команды: {command}")
        self.tn.write(command.encode(self.encoding) + Config.ENTER)
        if not wait_prompt:
            return ""

        idx, data = self._expect(Config.SHELL_PROMPT)
        if idx == -1:
            raise Exception("Не дождались приглашения после команды")

        output = data.decode(self.encoding, errors='ignore')
        time.sleep(5.0)
        logging.info(f"Вывод команды:\n{output}")
        return output

    def connect(self):
        """Устанавливает соединение и выполняет вход."""
        try:
            logging.info(f"Подключение к {self.host}:{Config.TELNET_PORT}")
            self.tn = telnetlib.Telnet(self.host, Config.TELNET_PORT, timeout=Config.TELNET_TIMEOUT)

            # Ожидание логина
            idx, _ = self._expect([b'login:', b'Login:'], timeout=10)
            if idx == -1:
                raise Exception("Не получено приглашение логина")
            self.tn.write(self.login.encode('ascii') + Config.ENTER)

            # Ожидание пароля
            idx2, _ = self._expect([b'Password:', b'password:'], timeout=10)
            if idx2 == -1:
                raise Exception("Не получено приглашение пароля")
            self.tn.write(self.password.encode('ascii') + Config.ENTER)

            # Ожидание приглашения shell
            idx3, _ = self._expect(Config.SHELL_PROMPT)
            if idx3 == -1:
                raise Exception("Не удалось войти в shell")

            logging.info(f"Успешное подключение к {self.host}")
        except Exception as e:
            logging.error(f"Ошибка подключения: {e}")
            raise

    def close(self):
        """Закрывает соединение."""
        if self.tn:
            try:
                self.tn.close()
            except:
                pass
            self.tn = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# =============================================================================
# 5. ВЫСОКОУРОВНЕВЫЙ КЛИЕНТ АТС
# =============================================================================

class AlcatelOXEClient:
    """Клиент для выполнения операций на АТС через Telnet."""
    def __init__(self, host: str, login: str, password: str):
        self.host = host
        self.login = login
        self.password = password
        self.session: Optional[AlcatelSession] = None

    def connect(self):
        self.session = AlcatelSession(self.host, self.login, self.password)
        self.session.connect()

    def close(self):
        if self.session:
            self.session.close()
            self.session = None

    def run_mgr_script(self, script_lines: List[str]) -> Tuple[bool, str]:
        """
        Выполняет mgr-скрипт одной командой: создаёт файл, запускает mgr, удаляет созданный файл.
        Возвращает (успех, вывод).
        """
        if not self.session:
            raise RuntimeError("Соединение не установлено. Вызовите connect() сначала.")

        script_content = "\n".join(script_lines)
        safe_content = script_content.replace("'", "'\\''")
        cmd = f"echo '{safe_content}' > scr1.mgr; mgr -nodico -X scr1.mgr; rm scr1.mgr"
        output = self.session._send_command(cmd, wait_prompt=True)
        success = "Error" not in output
        return success, output

# =============================================================================
# 6. ОРКЕСТРАТОР ДЛЯ ОБНОВЛЕНИЯ АБОНЕНТА
# =============================================================================

class SubscriberUpdater:
    """Координирует процесс обновления данных абонента."""
    def __init__(self, server_manager: ServerManager):
        self.server_manager = server_manager

    def update(self, number: str, last_name: str, first_name: str) -> Tuple[bool, str]:
        """Основная логика: проверка номера, транслитерация, подключение, выполнение."""
        # Проверка формата номера
        if not re.match(r'9\d{2}\d{4}$', number):
            return False, f"Неверный формат номера: {number}. Ожидается 9xxyyyy"

        # Транслитерация
        last_name_lat = Transliterator.convert(last_name)
        first_name_lat = Transliterator.convert(first_name)

        # Формируем скрипт
        script_lines = [
            f'SET Subscriber   "1": "{number}"',
            "{",
            f' Annu_Name = "{last_name_lat}",',
            f' Annu_First_Name = "{first_name_lat}",',
            f' UTF8_Phone_Book_Name = "{last_name}",',
            f' UTF8_Phone_Book_First_Name = "{first_name}"',
            "}"
        ]

        # Определяем IP по коду региона из номера
        region_code = number[1:3]  # две цифры после 9
        try:
            host = self.server_manager.get_address_by_region(region_code)
        except ValueError as e:
            return False, f"Не удалось определить IP-адрес: {e}"

        # Получаем учётные данные
        try:
            login, password = self.server_manager.get_credentials(host)
        except Exception as e:
            return False, f"Ошибка получения учётных данных: {e}"

        client = AlcatelOXEClient(host, login, password)
        try:
            client.connect()
            success, output = client.run_mgr_script(script_lines)
            if success:
                return True, "Данные абонента успешно обновлены."
            else:
                return False, f"Ошибка при выполнении скрипта:\n{output}"
        except Exception as e:
            logging.exception("Критическая ошибка")
            return False, str(e)
        finally:
            client.close()

# =============================================================================
# 7. ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# =============================================================================

class GUI:
    """Tkinter приложение."""
    def __init__(self, updater: SubscriberUpdater):
        self.updater = updater
        self.root = tk.Tk()
        self.root.title("Изменение данных абонента Alcatel OXE")
        self.root.geometry("450x400")
        self.root.resizable(False, False)

        self.var_number = tk.StringVar()
        self.var_last_name = tk.StringVar()
        self.var_first_name = tk.StringVar()
        self.ip_display = tk.StringVar()

        self.var_number.trace_add('write', self.update_ip)

        self._create_widgets()
        self.root.mainloop()

    def _create_widgets(self):
        """Создаёт элементы интерфейса."""
        # Номер
        tk.Label(self.root, text="Номер абонента (9xxyyyy):", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Entry(self.root, textvariable=self.var_number, width=30).pack(pady=5)

        # IP
        tk.Label(self.root, text="IP-адрес АТС (авто):", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Label(self.root, textvariable=self.ip_display, bg="lightgray", width=30).pack(pady=5)

        # Фамилия
        tk.Label(self.root, text="Фамилия (кириллицей):", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Entry(self.root, textvariable=self.var_last_name, width=30).pack(pady=5)

        # Имя
        tk.Label(self.root, text="Имя (кириллицей):", font=("Arial", 10)).pack(pady=(10, 0))
        tk.Entry(self.root, textvariable=self.var_first_name, width=30).pack(pady=5)

        # Кнопка
        self.btn_execute = tk.Button(self.root, text="Переименовать", command=self.on_execute,
                                     bg="lightblue", font=("Arial", 10))
        self.btn_execute.pack(pady=20)

    def update_ip(self, *args):
        """Обновляет отображение IP при изменении номера."""
        number = self.var_number.get().strip()
        if re.match(r'9\d{2}\d{4}$', number):
            region_code = number[1:3]
            try:
                host = self.updater.server_manager.get_address_by_region(region_code)
                self.ip_display.set(host)
            except ValueError:
                self.ip_display.set("(регион не найден)")
        else:
            self.ip_display.set("(неверный формат номера)")

    def on_execute(self):
        """Обработчик нажатия кнопки."""
        number = self.var_number.get().strip()
        last_name = self.var_last_name.get().strip()
        first_name = self.var_first_name.get().strip()

        if not number:
            messagebox.showerror("Ошибка", "Введите номер абонента")
            return
        if not re.match(r'9\d{2}\d{4}$', number):
            messagebox.showerror("Ошибка", "Неверный формат номера. Ожидается 9xxyyyy (например, 9011666)")
            return
        if not last_name or not first_name:
            messagebox.showerror("Ошибка", "Введите фамилию и имя")
            return

        self.btn_execute.config(state=tk.DISABLED, text="Выполняется...")
        self.root.update()

        try:
            success, msg = self.updater.update(number, last_name, first_name)
            if success:
                messagebox.showinfo("Успех", msg)
            else:
                messagebox.showerror("Ошибка", msg)
        except Exception as e:
            messagebox.showerror("Исключение", str(e))
        finally:
            self.btn_execute.config(state=tk.NORMAL, text="Переименовать")
            self.root.update()

# =============================================================================
# 8. ЛОГИРОВАНИЕ И ТОЧКА ВХОДА
# =============================================================================

def setup_logging():
    """Настраивает логирование в файл."""
    log_dir = os.path.dirname(Config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
        filename=Config.LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def main():
    setup_logging()
    server_manager = ServerManager(Config.SERVERS_JSON_PATH)
    updater = SubscriberUpdater(server_manager)
    GUI(updater)

if __name__ == "__main__":
    main()