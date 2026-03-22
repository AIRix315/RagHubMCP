// Package main provides platform-specific operations
package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
)

// PlatformOps contains platform-specific operations
type PlatformOps struct {
	OpenBrowser   func(url string) error
	GetRuntimeDir func() string
	PathSep       string
	Shell         string
	ShellFlag     string
}

// getPlatformOps returns platform-specific operations
func getPlatformOps() *PlatformOps {
	switch runtime.GOOS {
	case "windows":
		return &PlatformOps{
			OpenBrowser: func(url string) error {
				return exec.Command("cmd", "/c", "start", "", url).Start()
			},
			GetRuntimeDir: func() string {
				return filepath.Join(os.Getenv("APPDATA"), "RagHubMCP")
			},
			PathSep:   "\\",
			Shell:     "cmd",
			ShellFlag: "/c",
		}
	case "darwin":
		return &PlatformOps{
			OpenBrowser: func(url string) error {
				return exec.Command("open", url).Start()
			},
			GetRuntimeDir: func() string {
				return filepath.Join(os.Getenv("HOME"), "Library", "Application Support", "RagHubMCP")
			},
			PathSep:   "/",
			Shell:     "/bin/sh",
			ShellFlag: "-c",
		}
	default: // linux
		return &PlatformOps{
			OpenBrowser: func(url string) error {
				return exec.Command("xdg-open", url).Start()
			},
			GetRuntimeDir: func() string {
				return filepath.Join(os.Getenv("HOME"), ".raghubmcp")
			},
			PathSep:   "/",
			Shell:     "/bin/sh",
			ShellFlag: "-c",
		}
	}
}

// cachedPlatformOps holds the platform operations
var cachedPlatformOps *PlatformOps

// initPlatform initializes platform-specific operations
func initPlatform() {
	cachedPlatformOps = getPlatformOps()
}

// getIconPath returns the icon path for the current platform
func getIconPath() string {
	switch runtime.GOOS {
	case "windows":
		return "icons/app.ico"
	case "darwin":
		return "icons/app.png"
	default:
		return "icons/app.png"
	}
}

// getExeSuffix returns the executable suffix for the current platform
func getExeSuffix() string {
	if runtime.GOOS == "windows" {
		return ".exe"
	}
	return ""
}

// isWindows returns true if running on Windows
func isWindows() bool {
	return runtime.GOOS == "windows"
}

// isDarwin returns true if running on macOS
func isDarwin() bool {
	return runtime.GOOS == "darwin"
}

// isLinux returns true if running on Linux
func isLinux() bool {
	return runtime.GOOS == "linux"
}

// getPythonExe returns the Python executable name
func getPythonExe() string {
	if runtime.GOOS == "windows" {
		return "python.exe"
	}
	return "python"
}

// getPipExe returns the pip executable name
func getPipExe() string {
	if runtime.GOOS == "windows" {
		return "pip.exe"
	}
	return "pip"
}
