// bootmanager_go.go — диспетчер автозагрузки на Go

package main

import (
	"flag"
	"fmt"
	"os"
	"runtime"
	"strings"
)

func main() {
	listPtr := flag.Bool("list", false, "Показать список автозагрузки")
	flag.Parse()

	if runtime.GOOS == "windows" {
		runWindows(*listPtr)
	} else if runtime.GOOS == "linux" {
		runLinux(*listPtr)
	} else {
		fmt.Println("ОС не поддерживается")
	}
}

func runWindows(list bool) {
	// Для Windows используем команду reg query
	// Можно было бы использовать пакет registry, но для простоты используем exec
	// В реальном проекте используем golang.org/x/sys/windows/registry
	// Здесь упрощённо
	fmt.Println("📋 Программы в автозагрузке (Windows):")
	// ...
}

func runLinux(list bool) {
	// Чтение ~/.config/autostart
	fmt.Println("📋 Программы в автозагрузке (Linux):")
	// ...
}
