// bootmanager_js.js — диспетчер автозагрузки на JavaScript (Node.js)

const { exec } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');

function listWindows() {
    console.log('📋 Программы в автозагрузке (Windows):');
    const cmds = [
        'reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
        'reg query HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'
    ];
    cmds.forEach(cmd => {
        exec(cmd, (err, stdout) => {
            if (err) return;
            const lines = stdout.split('\n');
            lines.forEach(line => {
                if (line.includes('REG_SZ') || line.includes('REG_EXPAND_SZ')) {
                    const parts = line.trim().split(/\s{2,}/);
                    if (parts.length >= 3) {
                        console.log(`${parts[0]} -> ${parts[2]}`);
                    }
                }
            });
        });
    });
}

function listLinux() {
    console.log('📋 Программы в автозагрузке (Linux):');
    const home = os.homedir();
    const autostart = path.join(home, '.config', 'autostart');
    if (fs.existsSync(autostart)) {
        const files = fs.readdirSync(autostart).filter(f => f.endsWith('.desktop'));
        files.forEach(f => {
            const content = fs.readFileSync(path.join(autostart, f), 'utf8');
            const lines = content.split('\n');
            let name = '', execCmd = '', enabled = true;
            lines.forEach(line => {
                if (line.startsWith('Name=')) name = line.substring(5);
                if (line.startsWith('Exec=')) execCmd = line.substring(5);
                if (line.startsWith('Hidden=true')) enabled = false;
            });
            console.log(`${name} (${execCmd}) - ${enabled ? 'Вкл' : 'Откл'}`);
        });
    }
}

if (process.argv.includes('--list')) {
    if (os.platform() === 'win32') listWindows();
    else if (os.platform() === 'linux') listLinux();
    else console.log('ОС не поддерживается');
} else {
    console.log('Использование: node bootmanager_js.js --list');
}
