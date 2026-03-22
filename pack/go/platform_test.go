// Package main provides platform-specific operations tests
package main

import (
	"path/filepath"
	"runtime"
	"testing"
)

func TestGetPlatformOps(t *testing.T) {
	ops := getPlatformOps()

	if ops == nil {
		t.Fatal("getPlatformOps returned nil")
	}

	// Check that required functions are set
	if ops.OpenBrowser == nil {
		t.Error("OpenBrowser function is nil")
	}
	if ops.GetRuntimeDir == nil {
		t.Error("GetRuntimeDir function is nil")
	}
	if ops.PathSep == "" {
		t.Error("PathSep is empty")
	}
	if ops.Shell == "" {
		t.Error("Shell is empty")
	}
	if ops.ShellFlag == "" {
		t.Error("ShellFlag is empty")
	}
}

func TestPlatformSpecificPathSep(t *testing.T) {
	ops := getPlatformOps()

	switch runtime.GOOS {
	case "windows":
		if ops.PathSep != "\\" {
			t.Errorf("Expected PathSep='\\' on Windows, got '%s'", ops.PathSep)
		}
	default:
		if ops.PathSep != "/" {
			t.Errorf("Expected PathSep='/' on Unix, got '%s'", ops.PathSep)
		}
	}
}

func TestPlatformSpecificShell(t *testing.T) {
	ops := getPlatformOps()

	switch runtime.GOOS {
	case "windows":
		if ops.Shell != "cmd" {
			t.Errorf("Expected Shell='cmd' on Windows, got '%s'", ops.Shell)
		}
		if ops.ShellFlag != "/c" {
			t.Errorf("Expected ShellFlag='/c' on Windows, got '%s'", ops.ShellFlag)
		}
	case "darwin":
		if ops.Shell != "/bin/sh" {
			t.Errorf("Expected Shell='/bin/sh' on macOS, got '%s'", ops.Shell)
		}
	default: // linux
		if ops.Shell != "/bin/sh" {
			t.Errorf("Expected Shell='/bin/sh' on Linux, got '%s'", ops.Shell)
		}
	}
}

func TestGetRuntimeDir(t *testing.T) {
	ops := getPlatformOps()
	runtimeDir := ops.GetRuntimeDir()

	if runtimeDir == "" {
		t.Error("GetRuntimeDir returned empty string")
	}

	// Should contain RagHubMCP or .raghubmcp
	switch runtime.GOOS {
	case "windows":
		if !filepath.IsAbs(runtimeDir) {
			t.Errorf("Runtime dir should be absolute on Windows: %s", runtimeDir)
		}
	case "darwin":
		if !filepath.IsAbs(runtimeDir) {
			t.Errorf("Runtime dir should be absolute on macOS: %s", runtimeDir)
		}
	default:
		if !filepath.IsAbs(runtimeDir) {
			t.Errorf("Runtime dir should be absolute on Linux: %s", runtimeDir)
		}
	}
}

func TestGetExeSuffix(t *testing.T) {
	suffix := getExeSuffix()

	switch runtime.GOOS {
	case "windows":
		if suffix != ".exe" {
			t.Errorf("Expected '.exe' on Windows, got '%s'", suffix)
		}
	default:
		if suffix != "" {
			t.Errorf("Expected empty suffix on Unix, got '%s'", suffix)
		}
	}
}

func TestIsWindows(t *testing.T) {
	result := isWindows()
	expected := runtime.GOOS == "windows"
	if result != expected {
		t.Errorf("isWindows() = %v, expected %v", result, expected)
	}
}

func TestIsDarwin(t *testing.T) {
	result := isDarwin()
	expected := runtime.GOOS == "darwin"
	if result != expected {
		t.Errorf("isDarwin() = %v, expected %v", result, expected)
	}
}

func TestIsLinux(t *testing.T) {
	result := isLinux()
	expected := runtime.GOOS == "linux"
	if result != expected {
		t.Errorf("isLinux() = %v, expected %v", result, expected)
	}
}

func TestGetPythonExe(t *testing.T) {
	exe := getPythonExe()

	switch runtime.GOOS {
	case "windows":
		if exe != "python.exe" {
			t.Errorf("Expected 'python.exe' on Windows, got '%s'", exe)
		}
	default:
		if exe != "python" {
			t.Errorf("Expected 'python' on Unix, got '%s'", exe)
		}
	}
}

func TestGetPipExe(t *testing.T) {
	exe := getPipExe()

	switch runtime.GOOS {
	case "windows":
		if exe != "pip.exe" {
			t.Errorf("Expected 'pip.exe' on Windows, got '%s'", exe)
		}
	default:
		if exe != "pip" {
			t.Errorf("Expected 'pip' on Unix, got '%s'", exe)
		}
	}
}

func TestGetIconPath(t *testing.T) {
	iconPath := getIconPath()

	switch runtime.GOOS {
	case "windows":
		if iconPath != "icons/app.ico" {
			t.Errorf("Expected 'icons/app.ico' on Windows, got '%s'", iconPath)
		}
	default:
		if iconPath != "icons/app.png" {
			t.Errorf("Expected 'icons/app.png' on Unix, got '%s'", iconPath)
		}
	}
}

func TestInitPlatform(t *testing.T) {
	// Should not panic
	initPlatform()

	if cachedPlatformOps == nil {
		t.Error("initPlatform did not set cachedPlatformOps")
	}
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
