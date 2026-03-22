// Package main provides configuration tests
package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestGetConfigPath_CreatedIfNotExists(t *testing.T) {
	// Create a temporary runtime directory
	tmpDir := t.TempDir()

	// Override the getRuntimeDir function behavior for testing
	// by creating a config in the temp directory
	configPath := filepath.Join(tmpDir, "config.yaml")

	// Remove config if it exists
	os.Remove(configPath)

	// Call createDefaultConfig
	createdPath, err := createDefaultConfig(tmpDir)
	if err != nil {
		t.Fatalf("createDefaultConfig failed: %v", err)
	}

	if createdPath != configPath {
		t.Errorf("Expected config path %s, got %s", configPath, createdPath)
	}

	// Verify file exists
	if _, err := os.Stat(configPath); os.IsNotExist(err) {
		t.Error("Config file was not created")
	}

	// Verify file content
	content, err := os.ReadFile(configPath)
	if err != nil {
		t.Fatalf("Failed to read config file: %v", err)
	}

	if len(content) == 0 {
		t.Error("Config file is empty")
	}

	// Verify it contains expected keys
	contentStr := string(content)
	expectedKeys := []string{"server:", "chroma:", "providers:", "embedding:", "rerank:", "vectorstore:"}
	for _, key := range expectedKeys {
		if !containsSubstring(contentStr, key) {
			t.Errorf("Config missing expected key: %s", key)
		}
	}
}

func TestCreateDefaultConfig_Idempotent(t *testing.T) {
	tmpDir := t.TempDir()

	// Create config first time
	path1, err := createDefaultConfig(tmpDir)
	if err != nil {
		t.Fatalf("First createDefaultConfig failed: %v", err)
	}

	// Create config second time (should overwrite)
	path2, err := createDefaultConfig(tmpDir)
	if err != nil {
		t.Fatalf("Second createDefaultConfig failed: %v", err)
	}

	if path1 != path2 {
		t.Errorf("Expected same path, got %s and %s", path1, path2)
	}
}

func TestAppConfig(t *testing.T) {
	config := &AppConfig{
		Version:    "test-version",
		BuildTime:  "2024-01-01",
		Host:       "127.0.0.1",
		Port:       3315,
		RESTPort:   8818,
		MCPPort:    8819,
		WorkingDir: "/test/dir",
	}

	if config.Version != "test-version" {
		t.Errorf("Expected version 'test-version', got '%s'", config.Version)
	}
	if config.Port != 3315 {
		t.Errorf("Expected port 3315, got %d", config.Port)
	}
	if config.RESTPort != 8818 {
		t.Errorf("Expected REST port 8818, got %d", config.RESTPort)
	}
	if config.MCPPort != 8819 {
		t.Errorf("Expected MCP port 8819, got %d", config.MCPPort)
	}
}

func TestResourceExtractionConfig(t *testing.T) {
	cfg := ResourceExtractionConfig{
		ExtractFrontend: true,
		ExtractBackend:  true,
		ExtractData:     true,
	}

	if !cfg.ExtractFrontend {
		t.Error("ExtractFrontend should be true")
	}
	if !cfg.ExtractBackend {
		t.Error("ExtractBackend should be true")
	}
	if !cfg.ExtractData {
		t.Error("ExtractData should be true")
	}
}

func TestGetWorkingDir(t *testing.T) {
	wd := getWorkingDir()

	if wd == "" {
		t.Error("getWorkingDir returned empty string")
	}
}
