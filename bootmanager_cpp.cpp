// bootmanager_cpp.cpp — диспетчер автозагрузки на C++ (WinAPI/Linux)

#include <iostream>
#include <vector>
#include <string>
#include <windows.h>
#include <winreg.h>
#include <shlobj.h>
#include <filesystem>
#include <algorithm>
#include <iomanip>

struct StartupEntry {
    std::wstring name;
    std::wstring command;
    bool enabled;
    std::wstring source;
};

class BootManager {
private:
    std::vector<StartupEntry> entries;

    void add_registry_entry(HKEY hive, const std::wstring& path, const std::wstring& name, const std::wstring& value) {
        StartupEntry e;
        e.name = name;
        e.command = value;
        e.enabled = true;
        e.source = path;
        entries.push_back(e);
    }

    void scan_registry() {
        HKEY hives[] = { HKEY_CURRENT_USER, HKEY_LOCAL_MACHINE };
        std::wstring paths[] = {
            L"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
            L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
            L"Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce",
            L"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce"
        };
        for (auto hive : hives) {
            for (auto& path : paths) {
                HKEY key;
                if (RegOpenKeyExW(hive, path.c_str(), 0, KEY_READ, &key) == ERROR_SUCCESS) {
                    DWORD index = 0;
                    wchar_t name[256];
                    wchar_t value[1024];
                    DWORD nameSize = 256;
                    DWORD valueSize = 1024;
                    DWORD type;
                    while (RegEnumValueW(key, index, name, &nameSize, nullptr, &type, (LPBYTE)value, &valueSize) == ERROR_SUCCESS) {
                        if (type == REG_SZ || type == REG_EXPAND_SZ) {
                            StartupEntry e;
                            e.name = name;
                            e.command = value;
                            e.enabled = true;
                            e.source = std::wstring(hive == HKEY_CURRENT_USER ? L"HKCU\\" : L"HKLM\\") + path;
                            entries.push_back(e);
                        }
                        nameSize = 256;
                        valueSize = 1024;
                        index++;
                    }
                    RegCloseKey(key);
                }
            }
        }
    }

    void scan_startup_folder() {
        wchar_t path[MAX_PATH];
        if (SHGetFolderPathW(nullptr, CSIDL_STARTUP, nullptr, 0, path) == S_OK) {
            std::wstring startup = path;
            for (auto& entry : std::filesystem::directory_iterator(startup)) {
                if (entry.is_regular_file() && (entry.path().extension() == L".lnk" || entry.path().extension() == L".exe")) {
                    StartupEntry e;
                    e.name = entry.path().filename().wstring();
                    e.command = entry.path().wstring();
                    e.enabled = true;
                    e.source = L"Startup folder";
                    entries.push_back(e);
                }
            }
        }
    }

public:
    void scan() {
        entries.clear();
        scan_registry();
        scan_startup_folder();
    }

    void list() {
        std::wcout << L"📋 Программы в автозагрузке:\n";
        std::wcout << L"№   Имя                           Статус  Команда\n";
        std::wcout << L"------------------------------------------------------------\n";
        int i = 1;
        for (auto& e : entries) {
            std::wcout << i++ << L"   " << std::setw(25) << e.name << L"  " << (e.enabled ? L"✅" : L"❌") << L"   " << e.command.substr(0, 40) << L"\n";
        }
    }

    bool add(const std::wstring& command, const std::wstring& name) {
        HKEY key;
        if (RegOpenKeyExW(HKEY_CURRENT_USER, L"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, KEY_SET_VALUE, &key) == ERROR_SUCCESS) {
            if (RegSetValueExW(key, name.c_str(), 0, REG_SZ, (const BYTE*)command.c_str(), (command.size()+1)*sizeof(wchar_t)) == ERROR_SUCCESS) {
                RegCloseKey(key);
                return true;
            }
            RegCloseKey(key);
        }
        return false;
    }

    bool remove(int index) {
        if (index < 0 || index >= entries.size()) return false;
        auto& e = entries[index];
        if (e.source.find(L"Run") != std::wstring::npos) {
            std::wstring path = e.source;
            // Извлекаем hive и ключ
            size_t pos = path.find(L'\\');
            if (pos != std::wstring::npos) {
                std::wstring hiveStr = path.substr(0, pos);
                std::wstring keyPath = path.substr(pos+1);
                HKEY hive = (hiveStr == L"HKCU") ? HKEY_CURRENT_USER : HKEY_LOCAL_MACHINE;
                HKEY key;
                if (RegOpenKeyExW(hive, keyPath.c_str(), 0, KEY_SET_VALUE, &key) == ERROR_SUCCESS) {
                    RegDeleteValueW(key, e.name.c_str());
                    RegCloseKey(key);
                    return true;
                }
            }
        }
        return false;
    }
};

int main(int argc, char* argv[]) {
    BootManager bm;
    bm.scan();
    if (argc == 1 || std::string(argv[1]) == "--list") {
        bm.list();
    } else if (std::string(argv[1]) == "--add" && argc == 4) {
        std::wstring command = std::wstring(argv[2], argv[2]+strlen(argv[2]));
        std::wstring name = std::wstring(argv[3], argv[3]+strlen(argv[3]));
        if (bm.add(command, name))
            std::wcout << L"✅ Добавлено\n";
        else
            std::wcout << L"❌ Ошибка\n";
    } else if (std::string(argv[1]) == "--remove" && argc == 3) {
        int idx = std::stoi(argv[2]) - 1;
        if (bm.remove(idx))
            std::wcout << L"✅ Удалено\n";
        else
            std::wcout << L"❌ Ошибка\n";
    } else {
        std::cout << "Использование: bootmanager_cpp [--list] [--add <command> <name>] [--remove <index>]\n";
    }
    return 0;
}
