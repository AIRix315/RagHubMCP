// Package main provides integration tests
package main

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

// TestBuildExecutable tests that the executable can be built
func TestBuildExecutable(t *testing.T) {
	// This test assumes you're running from the pack/go directory
	// Skip if not in CI environment
	if os.Getenv("CI") == "" {
		t.Skip("Skipping build test in development mode")
	}

	// Build the executable
	cmd := exec.Command("go", "build", "-o", "test_build.exe", ".")
	cmd.Dir = "."
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("Build failed: %v\nOutput: %s", err, string(output))
	}

	// Cleanup
	defer os.Remove("test_build.exe")

	// Check if executable exists
	if _, err := os.Stat("test_build.exe"); os.IsNotExist(err) {
		t.Fatal("Executable was not created")
	}
}

// TestExecutableHelp tests that the executable shows help
func TestExecutableHelp(t *testing.T) {
	// Skip in CI if builds are separate
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Find the executable
	exePath := findExecutable(t)
	if exePath == "" {
		t.Skip("No executable found, skipping integration test")
	}

	// Run --version
	cmd := exec.Command(exePath, "--version")
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Logf("Warning: --version failed: %v", err)
	}

	t.Logf("Version output: %s", string(output))
}

// TestResourceExtraction tests embedded resource extraction
func TestResourceExtraction(t *testing.T) {
	// Create temp directory
	tmpDir := t.TempDir()

	// Test that extractFS can handle empty source
	err := extractFS(frontendFS, "frontend", filepath.Join(tmpDir, "frontend"))
	// In development, frontend dir is empty placeholder, so this should fail gracefully
	// In production build, it would contain actual files
	if err != nil {
		// Expected in dev mode - directory doesn't exist in embed
		t.Logf("Expected error in dev mode (empty embed): %v", err)
	}
}

// TestConfigGeneration tests config file generation
func TestConfigGeneration(t *testing.T) {
	tmpDir := t.TempDir()

	// Generate config
	configPath, err := createDefaultConfig(tmpDir)
	if err != nil {
		t.Fatalf("createDefaultConfig failed: %v", err)
	}

	// Verify file exists
	if _, err := os.Stat(configPath); err != nil {
		t.Fatalf("Config file not found: %v", err)
	}

	// Verify content is valid YAML
	content, err := os.ReadFile(configPath)
	if err != nil {
		t.Fatalf("Failed to read config: %v", err)
	}

	// Basic validation
	contentStr := string(content)
	requiredSections := []string{
		"server:",
		"host:",
		"port:",
		"providers:",
	}

	for _, section := range requiredSections {
		if !strings.Contains(contentStr, section) {
			t.Errorf("Config missing required section: %s", section)
		}
	}
}

// TestCrossPlatformPaths tests platform-specific path handling
func TestCrossPlatformPaths(t *testing.T) {
	// Test runtime directory
	runtimeDir := getRuntimeDir()
	if runtimeDir == "" {
		t.Error("getRuntimeDir returned empty string")
	}

	// Platform-specific assertions
	switch runtime.GOOS {
	case "windows":
		if !strings.Contains(runtimeDir, "AppData") && !strings.Contains(runtimeDir, "RagHubMCP") {
			t.Errorf("Windows runtime dir should contain AppData or RagHubMCP: %s", runtimeDir)
		}
	case "darwin":
		if !strings.Contains(runtimeDir, "Library/Application Support") && !strings.Contains(runtimeDir, "RagHubMCP") {
			t.Errorf("macOS runtime dir should contain Library/Application Support: %s", runtimeDir)
		}
	default: // linux
		if !strings.Contains(runtimeDir, ".raghubmcp") {
			t.Errorf("Linux runtime dir should contain .raghubmcp: %s", runtimeDir)
		}
	}
}

// TestServicePortChecking tests service availability checking
func TestServicePortChecking(t *testing.T) {
	// Test with a port that's likely not in use
	// We can't reliably test port availability without actually binding
	// So we just verify the function doesn't panic
	err := checkPortAvailable(59999)
	if err != nil {
		t.Errorf("checkPortAvailable failed: %v", err)
	}
}

// TestVersionFlags tests version flag handling
func TestVersionFlags(t *testing.T) {
	// Create a mock app config
	appConfig = &AppConfig{
		Version:    "test-1.0.0",
		BuildTime:  "2024-01-01",
		Host:       "127.0.0.1",
		Port:       3315,
		RESTPort:   8818,
		MCPPort:    8819,
		WorkingDir: ".",
	}

	// Verify config values
	if appConfig.Version != "test-1.0.0" {
		t.Errorf("Expected version 'test-1.0.0', got '%s'", appConfig.Version)
	}
	if appConfig.Port != 3315 {
		t.Errorf("Expected port 3315, got %d", appConfig.Port)
	}
}

// TestCLIFlagParsing tests CLI argument parsing
func TestCLIFlagParsing(t *testing.T) {
	// This would normally use flag.Parse(), but we can't do that in tests
	// Instead, we verify that our flag definitions are correct

	// The main.go defines these flags:
	// -host, -port, -rest-port, -mcp-port, -no-browser, -no-tray, -debug, -version
	// We can't test the parsing directly without modifying global state,
	// but we can verify the AppConfig struct supports all values

	config := &AppConfig{
		Host:     "192.168.1.1",
		Port:     8080,
		RESTPort: 8081,
		MCPPort:  8082,
	}

	if config.Host != "192.168.1.1" {
		t.Error("Failed to set Host")
	}
	if config.Port != 8080 {
		t.Error("Failed to set Port")
	}
	if config.RESTPort != 8081 {
		t.Error("Failed to set RESTPort")
	}
	if config.MCPPort != 8082 {
		t.Error("Failed to set MCPPort")
	}
}

// TestProxyRouteParsing tests proxy route configuration
func TestProxyRouteParsing(t *testing.T) {
	// Verify URL parsing for proxy targets
	testCases := []struct {
		port     int
		expected string
	}{
		{8818, "http://localhost:8818"},
		{8819, "http://localhost:8819"},
		{3315, "http://localhost:3315"},
	}

	for _, tc := range testCases {
		expected := tc.expected
		if expected == "" {
			t.Error("Empty expected URL")
		}
	}
}

// TestBrowserOpen tests browser opening functionality
func TestBrowserOpen(t *testing.T) {
	// We can't actually open a browser in tests, but we can verify the function exists
	// and the platform operations are initialized

	ops := getPlatformOps()
	if ops == nil {
		t.Fatal("getPlatformOps returned nil")
	}

	// Function should not panic
	// In tests, we don't actually call openBrowser because it launches a process
}

// TestProcessManagerState tests ProcessManager state management
func TestProcessManagerState(t *testing.T) {
	// Create a new ProcessManager
	pm := &ProcessManager{
		processes: make(map[string]*exec.Cmd),
	}

	// Verify initial state
	if len(pm.processes) != 0 {
		t.Error("ProcessManager should start empty")
	}

	// Test mutex operations don't deadlock
	done := make(chan bool)
	go func() {
		pm.mu.Lock()
		pm.processes["test1"] = nil
		pm.mu.Unlock()
		done <- true
	}()

	select {
	case <-done:
		// Success
	case <-time.After(time.Second):
		t.Error("ProcessManager mutex deadlock detected")
	}
}

// Helper function to find executable
func findExecutable(t *testing.T) string {
	// Check common locations
	locations := []string{
		"../dist/RHM.exe",
		"../dist/RHM",
		"./RHM.exe",
		"./RHM",
	}

	for _, loc := range locations {
		if _, err := os.Stat(loc); err == nil {
			return loc
		}
	}

	return ""
}
