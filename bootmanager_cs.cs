// bootmanager_cs.cs — диспетчер автозагрузки на C# (.NET Core)

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using Microsoft.Win32;

class BootManager
{
    private class Entry
    {
        public string Name { get; set; }
        public string Command { get; set; }
        public bool Enabled { get; set; }
        public string Source { get; set; }
    }

    private List<Entry> entries = new List<Entry>();

    public void Scan()
    {
        if (OperatingSystem.IsWindows())
            ScanWindows();
        else if (OperatingSystem.IsLinux())
            ScanLinux();
        else if (OperatingSystem.IsMacOS())
            ScanMac();
        else
            Console.WriteLine("ОС не поддерживается");
    }

    private void ScanWindows()
    {
        // Реестр
        string[] paths = {
            @"HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
            @"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
        };
        foreach (var path in paths) {
            try {
                using (var key = RegistryKey.OpenBaseKey(RegistryHive.CurrentUser, RegistryView.Default))
                using (var sub = key.OpenSubKey(path.Replace("HKEY_CURRENT_USER\\", ""))) {
                    if (sub != null) {
                        foreach (var name in sub.GetValueNames()) {
                            var val = sub.GetValue(name).ToString();
                            entries.Add(new Entry {
                                Name = name,
                                Command = val,
                                Enabled = true,
                                Source = path
                            });
                        }
                    }
                }
            } catch {}
        }
        // Папка Startup
        var startup = Environment.GetFolderPath(Environment.SpecialFolder.Startup);
        foreach (var f in Directory.GetFiles(startup, "*.lnk")) {
            entries.Add(new Entry {
                Name = Path.GetFileName(f),
                Command = f,
                Enabled = true,
                Source = "Startup folder"
            });
        }
    }

    private void ScanLinux()
    {
        // ~/.config/autostart
        var home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        var path = Path.Combine(home, ".config", "autostart");
        if (Directory.Exists(path)) {
            foreach (var f in Directory.GetFiles(path, "*.desktop")) {
                try {
                    var lines = File.ReadAllLines(f);
                    Entry e = new Entry();
                    e.Enabled = true;
                    e.Source = f;
                    foreach (var line in lines) {
                        if (line.StartsWith("Name=")) e.Name = line.Substring(5);
                        if (line.StartsWith("Exec=")) e.Command = line.Substring(5);
                        if (line.StartsWith("Hidden=true")) e.Enabled = false;
                    }
                    if (!string.IsNullOrEmpty(e.Name) && !string.IsNullOrEmpty(e.Command))
                        entries.Add(e);
                } catch {}
            }
        }
    }

    private void ScanMac() { /* аналогично Linux */ }

    public void List()
    {
        Console.WriteLine("📋 Программы в автозагрузке:");
        Console.WriteLine($"{"№",-3} {"Имя",-25} {"Статус",-8} {"Команда"}");
        Console.WriteLine(new string('-', 80));
        int i = 1;
        foreach (var e in entries) {
            string status = e.Enabled ? "✅" : "❌";
            string name = e.Name.Length > 24 ? e.Name.Substring(0, 24) : e.Name;
            string cmd = e.Command.Length > 40 ? e.Command.Substring(0, 40) : e.Command;
            Console.WriteLine($"{i++,-3} {name,-25} {status,-8} {cmd}");
        }
    }

    public static void Main(string[] args)
    {
        var bm = new BootManager();
        bm.Scan();
        if (args.Length == 0 || args[0] == "--list")
            bm.List();
        else
            Console.WriteLine("Использование: dotnet run -- [--list]");
    }
}
