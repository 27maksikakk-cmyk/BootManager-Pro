// bootmanager_java.java — диспетчер автозагрузки на Java

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public class BootManager {
    private static class Entry {
        String name;
        String command;
        boolean enabled;
        String source;
    }

    private List<Entry> entries = new ArrayList<>();

    public void scan() {
        String os = System.getProperty("os.name").toLowerCase();
        if (os.contains("win")) {
            scanWindows();
        } else if (os.contains("linux")) {
            scanLinux();
        } else if (os.contains("mac")) {
            scanMac();
        } else {
            System.out.println("ОС не поддерживается");
        }
    }

    private void scanWindows() {
        // Используем команду reg query для получения данных (простой способ)
        try {
            String[] cmds = {
                "reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
            };
            for (String cmd : cmds) {
                Process p = Runtime.getRuntime().exec(cmd);
                BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.contains("REG_SZ") || line.contains("REG_EXPAND_SZ")) {
                        String[] parts = line.trim().split("\\s+", 3);
                        if (parts.length >= 3) {
                            Entry e = new Entry();
                            e.name = parts[0].trim();
                            e.command = parts[2].trim();
                            e.enabled = true;
                            e.source = cmd;
                            entries.add(e);
                        }
                    }
                }
                p.waitFor();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    private void scanLinux() {
        // Чтение ~/.config/autostart/*.desktop
        String home = System.getProperty("user.home");
        Path autostart = Paths.get(home, ".config", "autostart");
        if (Files.exists(autostart)) {
            try {
                Files.list(autostart).filter(p -> p.toString().endsWith(".desktop")).forEach(p -> {
                    try {
                        List<String> lines = Files.readAllLines(p);
                        Entry e = new Entry();
                        e.enabled = true;
                        e.source = p.toString();
                        for (String line : lines) {
                            if (line.startsWith("Name=")) e.name = line.substring(5);
                            if (line.startsWith("Exec=")) e.command = line.substring(5);
                            if (line.startsWith("Hidden=true")) e.enabled = false;
                        }
                        if (e.name != null && e.command != null) entries.add(e);
                    } catch (IOException ex) {}
                });
            } catch (IOException e) {}
        }
    }

    private void scanMac() {
        // Упрощённо: используем launchctl list
        try {
            Process p = Runtime.getRuntime().exec("launchctl list");
            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String line;
            while ((line = reader.readLine()) != null) {
                if (!line.startsWith("-")) {
                    String[] parts = line.trim().split("\\s+");
                    if (parts.length >= 3) {
                        Entry e = new Entry();
                        e.name = parts[2];
                        e.command = parts[2];
                        e.enabled = true;
                        e.source = "launchctl";
                        entries.add(e);
                    }
                }
            }
            p.waitFor();
        } catch (Exception e) {}
    }

    public void list() {
        System.out.println("📋 Программы в автозагрузке:");
        System.out.printf("%-3s %-25s %-8s %s\n", "№", "Имя", "Статус", "Команда");
        System.out.println("------------------------------------------------------------");
        int i = 1;
        for (Entry e : entries) {
            String status = e.enabled ? "✅" : "❌";
            String name = e.name.length() > 24 ? e.name.substring(0, 24) : e.name;
            String cmd = e.command.length() > 40 ? e.command.substring(0, 40) : e.command;
            System.out.printf("%-3d %-25s %-8s %s\n", i++, name, status, cmd);
        }
    }

    public static void main(String[] args) {
        BootManager bm = new BootManager();
        bm.scan();
        if (args.length == 0 || args[0].equals("--list")) {
            bm.list();
        } else {
            System.out.println("Использование: java BootManager [--list]");
        }
    }
}
