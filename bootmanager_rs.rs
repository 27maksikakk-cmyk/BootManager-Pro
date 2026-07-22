// bootmanager_rs.rs — диспетчер автозагрузки на Rust

use std::env;
use std::process;
use std::fs;
use std::path::PathBuf;

#[cfg(target_os = "windows")]
use winreg::RegKey;
#[cfg(target_os = "windows")]
use winreg::enums::*;

struct Entry {
    name: String,
    command: String,
    enabled: bool,
    source: String,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() > 1 && args[1] == "--list" {
        list_entries();
    } else {
        println!("Использование: bootmanager_rs --list");
    }
}

#[cfg(target_os = "windows")]
fn list_entries() {
    println!("📋 Программы в автозагрузке (Windows):");
    let hives = [
        (HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
        (HKEY_LOCAL_MACHINE, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
    ];
    let mut entries: Vec<Entry> = Vec::new();
    for (hive, path) in hives.iter() {
        let hkey = RegKey::predef(*hive);
        if let Ok(key) = hkey.open_subkey_with_flags(path, KEY_READ) {
            for (name, value) in key.enum_values().filter_map(Result::ok) {
                if let Ok(val_str) = value.to_string() {
                    entries.push(Entry {
                        name: name.to_string_lossy().to_string(),
                        command: val_str,
                        enabled: true,
                        source: format!("{:?}\\{}", hive, path),
                    });
                }
            }
        }
    }
    // Вывод
    println!("{:<3} {:<25} {:<8} {}", "№", "Имя", "Статус", "Команда");
    println!("{}", "-".repeat(80));
    for (i, e) in entries.iter().enumerate() {
        let status = if e.enabled { "✅" } else { "❌" };
        let name = if e.name.len() > 24 { &e.name[..24] } else { &e.name };
        let cmd = if e.command.len() > 40 { &e.command[..40] } else { &e.command };
        println!("{:<3} {:<25} {:<8} {}", i+1, name, status, cmd);
    }
}

#[cfg(not(target_os = "windows"))]
fn list_entries() {
    println!("📋 Программы в автозагрузке (не Windows):");
    // Реализация для Linux/macOS
    let home = std::env::var("HOME").unwrap();
    let autostart = PathBuf::from(home).join(".config/autostart");
    if autostart.exists() {
        // чтение .desktop файлов
    }
}
