// Package main provides resource embedding and extraction
package main

import (
	"embed"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"

	"github.com/sirupsen/logrus"
)

// Embed frontend and backend resources
// These will be populated at build time
// Note: During development, these directories may not exist.
// Build scripts should create them before building.

//go:embed all:frontend
var frontendFS embed.FS

//go:embed all:backend
var backendFS embed.FS

//go:embed all:data
var dataFS embed.FS

// Resource paths for extraction
var (
	extractedBackendDir  string
	extractedFrontendDir string
	extractedDataDir     string
)

// ResourceExtractionConfig defines what resources to extract
type ResourceExtractionConfig struct {
	ExtractFrontend bool
	ExtractBackend  bool
	ExtractData     bool
}

// extractResources extracts embedded resources to disk
func extractResources() error {
	logrus.Info("Extracting embedded resources...")

	runtimeDir := getRuntimeDir()
	cfg := ResourceExtractionConfig{
		ExtractFrontend: true,
		ExtractBackend:  true,
		ExtractData:     true,
	}

	// Extract backend (Python source code)
	if cfg.ExtractBackend {
		backendDir := filepath.Join(runtimeDir, "backend")
		if err := extractFS(backendFS, "backend", backendDir); err != nil {
			return fmt.Errorf("failed to extract backend: %w", err)
		}
		extractedBackendDir = backendDir
		logrus.Infof("Backend extracted to: %s", backendDir)
	}

	// Extract frontend (Vue dist)
	if cfg.ExtractFrontend {
		frontendDir := filepath.Join(runtimeDir, "frontend", "dist")
		// Try to find frontend in embed FS - check both "frontend/dist" and "frontend" paths
		var srcPath string
		if _, err := fs.ReadDir(frontendFS, "frontend/dist"); err == nil {
			srcPath = "frontend/dist"
		} else if _, err := fs.ReadDir(frontendFS, "frontend"); err == nil {
			srcPath = "frontend"
		} else {
			logrus.Warn("Frontend resources not found in embed, skipping")
		}

		if srcPath != "" {
			if err := extractFS(frontendFS, srcPath, frontendDir); err != nil {
				logrus.WithError(err).Warn("Failed to extract frontend, may use local files")
			} else {
				logrus.Infof("Frontend extracted to: %s", frontendDir)
			}
		}
		extractedFrontendDir = frontendDir
	}

	// Extract data (models, cache, etc.)
	if cfg.ExtractData {
		dataDir := filepath.Join(runtimeDir, "data")
		if err := extractFS(dataFS, "data", dataDir); err != nil {
			logrus.WithError(err).Warn("Failed to extract data, may use local files")
		}
		extractedDataDir = dataDir
		logrus.Infof("Data extracted to: %s", dataDir)
	}

	return nil
}

// extractFS extracts an embedded filesystem to a directory
func extractFS(efs embed.FS, srcPath, destPath string) error {
	// Create destination directory
	if err := os.MkdirAll(destPath, 0755); err != nil {
		return fmt.Errorf("failed to create directory %s: %w", destPath, err)
	}

	// Walk the embedded filesystem
	return fs.WalkDir(efs, srcPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}

		// Skip the root directory
		if path == srcPath {
			return nil
		}

		// Calculate relative path
		relPath, err := filepath.Rel(srcPath, path)
		if err != nil {
			return err
		}
		dest := filepath.Join(destPath, relPath)

		if d.IsDir() {
			// Create directory
			return os.MkdirAll(dest, 0755)
		}

		// Read file from embedded FS
		data, err := fs.ReadFile(efs, path)
		if err != nil {
			return fmt.Errorf("failed to read %s: %w", path, err)
		}

		// Write file to disk
		return os.WriteFile(dest, data, 0644)
	})
}

// getEmbeddedFile returns a file from the embedded frontend
func getEmbeddedFile(path string) ([]byte, error) {
	// Try embedded FS first
	data, err := frontendFS.ReadFile(path)
	if err == nil {
		return data, nil
	}

	// Fall back to local filesystem
	if extractedFrontendDir != "" {
		localPath := filepath.Join(extractedFrontendDir, path)
		return os.ReadFile(localPath)
	}

	// Try local frontend directory (development mode)
	localPath := filepath.Join("frontend", "dist", path)
	return os.ReadFile(localPath)
}

// cleanupTempResources cleans up temporary resources
func cleanupTempResources() {
	logrus.Info("Cleaning up temporary resources...")

	// Clean up extracted resources if needed
	if extractedBackendDir != "" {
		logrus.Debug("Backend resources kept for reuse")
	}

	if extractedFrontendDir != "" {
		logrus.Debug("Frontend resources kept for reuse")
	}
}

// getConfigPath returns the path to the config file
func getConfigPath() (string, error) {
	// Check for config in extracted backend first
	if extractedBackendDir != "" {
		configPath := filepath.Join(extractedBackendDir, "config.yaml")
		if _, err := os.Stat(configPath); err == nil {
			return configPath, nil
		}
	}

	// Check for config in backend directory (development)
	wd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	configPath := filepath.Join(wd, "backend", "config.yaml")
	if _, err := os.Stat(configPath); err == nil {
		return configPath, nil
	}

	// Check for config in runtime directory
	runtimeDir := getRuntimeDir()
	configPath = filepath.Join(runtimeDir, "config.yaml")
	if _, err := os.Stat(configPath); err == nil {
		return configPath, nil
	}

	// Create default config
	return createDefaultConfig(runtimeDir)
}

// createDefaultConfig creates a default config file
func createDefaultConfig(runtimeDir string) (string, error) {
	configPath := filepath.Join(runtimeDir, "config.yaml")
	defaultConfig := `# Default RagHubMCP configuration
server:
  host: 127.0.0.1
  port: 8818

chroma:
  persist_dir: ./data/chroma

cors:
  origins:
    - http://localhost:3315
    - http://127.0.0.1:3315
  allow_credentials: true
  allow_methods:
    - GET
    - POST
    - PUT
    - DELETE
    - OPTIONS
  allow_headers:
    - Content-Type
    - Authorization

providers:
  embedding:
    default: ollama-bge
    instances:
      - name: ollama-bge
        type: ollama
        model: bge-m3
        base_url: http://localhost:11434
        dimension: 1024

  rerank:
    default: flashrank-tiny
    instances:
      - name: flashrank-tiny
        type: flashrank
        model: ms-marco-TinyBERT-L-2-v2

  vectorstore:
    default: chroma-local
    instances:
      - name: chroma-local
        type: chroma
        persist_dir: ./data/chroma
`
	if err := os.WriteFile(configPath, []byte(defaultConfig), 0644); err != nil {
		return "", fmt.Errorf("failed to create default config: %w", err)
	}

	logrus.Infof("Created default config: %s", configPath)
	return configPath, nil
}
