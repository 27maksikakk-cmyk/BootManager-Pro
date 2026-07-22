# bootmanager_python.py — диспетчер автозагрузки на Python

import os
import sys
import platform
import argparse
import json
from datetime import datetime

if platform.system() == 'Windows':
    try:
        import winreg
    except ImportError:
        print("Для Windows требуется pywin32 или модуль winreg (встроен)")
        sys.exit(1)
else:
    import subprocess
    import glob

class BootManager:
    def __init__(self):
        self.os_name = platform.system()
        self.entries = []

    def get_entries(self):
        """Получает список программ автозагрузки"""
        self.entries = []
        if self.os_name == 'Windows':
            self._get_windows_entries()
        elif self.os_name == 'Linux':
            self._get_linux_entries()
        elif self.os_name == 'Darwin':
            self._get_macos_entries()
        else:
            print("ОС не поддерживается")
        return self.entries

    def _get_windows_entries(self):
        # Реестр: текущий пользователь и локальная машина
        hives = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce")
        ]
        for hive, path in hives:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        self.entries.append({
                            'name': name,
                            'command': value,
                            'enabled': True,
                            'source': f"{'HKCU' if hive == winreg.HKEY_CURRENT_USER else 'HKLM'}\\{path}",
                            'os': 'Windows'
                        })
                        i += 1
                    except WindowsError:
                        break
                winreg.CloseKey(key)
            except WindowsError:
                pass

        # Папка Startup
        startup = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
        if os.path.exists(startup):
            for f in os.listdir(startup):
                if f.endswith('.lnk') or f.endswith('.exe'):
                    self.entries.append({
                        'name': f,
                        'command': os.path.join(startup, f),
                        'enabled': True,
                        'source': 'Startup folder',
                        'os': 'Windows'
                    })

    def _get_linux_entries(self):
        # Файлы .desktop в ~/.config/autostart и /etc/xdg/autostart
        dirs = [
            os.path.expanduser('~/.config/autostart'),
            '/etc/xdg/autostart'
        ]
        for d in dirs:
            if os.path.exists(d):
                for f in glob.glob(os.path.join(d, '*.desktop')):
                    with open(f, 'r') as file:
                        content = file.read()
                        # парсим Name и Exec
                        name = ''
                        exec_cmd = ''
                        enabled = not content.startswith('Hidden=true')
                        for line in content.splitlines():
                            if line.startswith('Name='):
                                name = line[5:].strip()
                            elif line.startswith('Exec='):
                                exec_cmd = line[5:].strip()
                        if name or exec_cmd:
                            self.entries.append({
                                'name': name or os.path.basename(f),
                                'command': exec_cmd,
                                'enabled': enabled,
                                'source': f,
                                'os': 'Linux'
                            })

    def _get_macos_entries(self):
        # Используем команду launchctl list и файлы в ~/Library/LaunchAgents
        # упрощённо
        try:
            output = subprocess.check_output(['launchctl', 'list']).decode('utf-8')
            for line in output.splitlines():
                parts = line.split()
                if len(parts) >= 3 and parts[0] != '-':
                    self.entries.append({
                        'name': parts[2],
                        'command': parts[2],
                        'enabled': True,
                        'source': 'launchctl',
                        'os': 'macOS'
                    })
        except:
            pass

    def enable_entry(self, index):
        """Включить запись по индексу"""
        if index < 0 or index >= len(self.entries):
            return False
        entry = self.entries[index]
        if self.os_name == 'Windows':
            # В реестре просто пересоздаём запись
            # в этом примере мы не изменяем, т.к. не храним состояние отключения
            print("Для включения используйте --add или удалите комментарий")
        # Для Linux: переименовать .desktop файл (убрать префикс)
        # Для macOS: launchctl load
        return True

    def disable_entry(self, index):
        """Отключить запись по индексу"""
        if index < 0 or index >= len(self.entries):
            return False
        entry = self.entries[index]
        if self.os_name == 'Windows':
            # Удаляем из реестра (или переименовываем)
            print("Отключение через --remove, затем добавление")
        # Для Linux: переименовать .desktop в .desktop.disabled
        # Для macOS: launchctl unload
        return True

    def add_entry(self, command, name):
        """Добавить новую запись"""
        # Пример для Windows
        if self.os_name == 'Windows':
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                     r"Software\Microsoft\Windows\CurrentVersion\Run",
                                     0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
                winreg.CloseKey(key)
                print(f"✅ Добавлено: {name}")
                return True
            except Exception as e:
                print(f"Ошибка добавления: {e}")
                return False
        else:
            print("Добавление для этой ОС не реализовано")
            return False

    def remove_entry(self, index):
        """Удалить запись"""
        if index < 0 or index >= len(self.entries):
            return False
        entry = self.entries[index]
        if self.os_name == 'Windows':
            # Удаляем из реестра
            try:
                if 'Run' in entry['source']:
                    hive, path = entry['source'].split('\\', 1)
                    hive = winreg.HKEY_CURRENT_USER if 'HKCU' in hive else winreg.HKEY_LOCAL_MACHINE
                    path = path.replace('HKLM\\', '').replace('HKCU\\', '')
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, entry['name'])
                    winreg.CloseKey(key)
                    print(f"✅ Удалено: {entry['name']}")
                    return True
            except Exception as e:
                print(f"Ошибка удаления: {e}")
        else:
            # Для Linux удалить файл .desktop
            pass
        return False

    def list_entries(self):
        print("📋 Программы в автозагрузке:")
        print(f"{'№':<3} {'Имя':<25} {'Статус':<8} {'Команда'}")
        print("-" * 80)
        for i, e in enumerate(self.entries):
            status = '✅' if e.get('enabled', True) else '❌'
            name = e['name'][:24]
            cmd = e['command'][:40]
            print(f"{i+1:<3} {name:<25} {status:<8} {cmd}")

    def export_json(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.entries, f, indent=2)
        print(f"Экспортировано в {filename}")

def main():
    parser = argparse.ArgumentParser(description="Диспетчер автозагрузки")
    parser.add_argument('--list', action='store_true', help='Показать список автозагрузки')
    parser.add_argument('--add', help='Добавить программу (путь к исполняемому файлу)')
    parser.add_argument('--name', default='', help='Имя для добавляемой программы')
    parser.add_argument('--enable', type=int, help='Включить запись по номеру')
    parser.add_argument('--disable', type=int, help='Отключить запись по номеру')
    parser.add_argument('--remove', type=int, help='Удалить запись по номеру')
    parser.add_argument('--export', help='Экспорт в JSON')
    args = parser.parse_args()

    bm = BootManager()
    bm.get_entries()

    if args.list:
        bm.list_entries()
    elif args.add:
        name = args.name if args.name else os.path.basename(args.add)
        bm.add_entry(args.add, name)
    elif args.enable is not None:
        bm.enable_entry(args.enable - 1)
    elif args.disable is not None:
        bm.disable_entry(args.disable - 1)
    elif args.remove is not None:
        bm.remove_entry(args.remove - 1)
    elif args.export:
        bm.export_json(args.export)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
