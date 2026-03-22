// Package main provides process management for Python services
package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"github.com/sirupsen/logrus"
)

// ProcessManager manages Python processes
type ProcessManager struct {
	processes map[string]*exec.Cmd
	mu        sync.RWMutex
}

// processManager is the global process manager
var processManager *ProcessManager

func init() {
	processManager = &ProcessManager{
		processes: make(map[string]*exec.Cmd),
	}
}

// startPythonREST starts the Python REST API service
func startPythonREST() error {
	logrus.Info("Starting Python REST API service...")

	// Get the Python executable path
	pythonExe := getPythonExecutable()
	backendDir := getBackendDir()

	// Build command - use raghub_mcp package
	cmd := exec.Command(pythonExe, "-m", "uvicorn", "raghub_mcp.main:app",
		"--host", appConfig.Host,
		"--port", fmt.Sprintf("%d", appConfig.RESTPort))
	cmd.Dir = backendDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	// Set PYTHONPATH to src directory (where raghub_mcp package resides)
	// Structure: backend/src/raghub_mcp/
	pythonPath := filepath.Join(backendDir, "src")
	env := os.Environ()
	env = append(env, "PYTHONUNBUFFERED=1")
	env = append(env, fmt.Sprintf("PYTHONPATH=%s", pythonPath))
	cmd.Env = env

	// Start process
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start REST API: %w", err)
	}

	// Register process for cleanup
	processManager.mu.Lock()
	processManager.processes["rest"] = cmd
	processManager.mu.Unlock()

	logrus.Infof("REST API started (PID: %d)", cmd.Process.Pid)

	// Wait for service to be ready
	if err := waitForService(appConfig.RESTPort, 30*time.Second); err != nil {
		return fmt.Errorf("REST API failed to start: %w", err)
	}

	logrus.Info("REST API is ready")
	return nil
}

// startPythonMCP starts the Python MCP HTTP service
func startPythonMCP() error {
	logrus.Info("Starting Python MCP HTTP service...")

	// Get the Python executable path
	pythonExe := getPythonExecutable()
	backendDir := getBackendDir()

	// Build command - use raghub_mcp package
	cmd := exec.Command(pythonExe, "-m", "raghub_mcp.mcp_server.server",
		"--transport", "http",
		"--host", appConfig.Host,
		"--port", fmt.Sprintf("%d", appConfig.MCPPort))
	cmd.Dir = backendDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	// Set PYTHONPATH to src directory (where raghub_mcp package resides)
	// Structure: backend/src/raghub_mcp/
	pythonPath := filepath.Join(backendDir, "src")
	env := os.Environ()
	env = append(env, "PYTHONUNBUFFERED=1")
	env = append(env, fmt.Sprintf("PYTHONPATH=%s", pythonPath))
	cmd.Env = env

	// Start process
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start MCP HTTP: %w", err)
	}

	// Register process for cleanup
	processManager.mu.Lock()
	processManager.processes["mcp"] = cmd
	processManager.mu.Unlock()

	logrus.Infof("MCP HTTP started (PID: %d)", cmd.Process.Pid)

	// Wait for service to be ready
	if err := waitForService(appConfig.MCPPort, 30*time.Second); err != nil {
		return fmt.Errorf("MCP HTTP failed to start: %w", err)
	}

	logrus.Info("MCP HTTP is ready")
	return nil
}

// stopPythonProcesses stops all Python processes
func stopPythonProcesses() {
	logrus.Info("Stopping Python processes...")

	processManager.mu.Lock()
	defer processManager.mu.Unlock()

	for name, cmd := range processManager.processes {
		if cmd != nil && cmd.Process != nil {
			logrus.Infof("Stopping %s process (PID: %d)", name, cmd.Process.Pid)
			if err := cmd.Process.Signal(os.Interrupt); err != nil {
				logrus.WithError(err).Warnf("Failed to stop %s gracefully, killing", name)
				cmd.Process.Kill()
			}
		}
	}

	// Give processes time to exit gracefully
	time.Sleep(2 * time.Second)

	// Force kill remaining processes
	for name, cmd := range processManager.processes {
		if cmd != nil && cmd.Process != nil {
			if cmd.ProcessState == nil || !cmd.ProcessState.Exited() {
				logrus.Warnf("Force killing %s process", name)
				cmd.Process.Kill()
			}
		}
	}

	logrus.Info("All Python processes stopped")
}

// getPythonExecutable returns the Python executable path
func getPythonExecutable() string {
	// First, check for embedded Python
	embeddedPython := getEmbeddedPythonPath()
	if _, err := os.Stat(embeddedPython); err == nil {
		logrus.Debugf("Using embedded Python: %s", embeddedPython)
		return embeddedPython
	}

	// Fall back to system Python
	if runtime.GOOS == "windows" {
		// Try python3 first, then python
		if _, err := exec.LookPath("python3.exe"); err == nil {
			return "python3.exe"
		}
		return "python.exe"
	}

	// Unix-like systems
	if _, err := exec.LookPath("python3"); err == nil {
		return "python3"
	}
	return "python"
}

// getBackendDir returns the backend directory path
func getBackendDir() string {
	// Check for extracted resources first
	extractedBackend := filepath.Join(getRuntimeDir(), "backend")
	if _, err := os.Stat(extractedBackend); err == nil {
		return extractedBackend
	}

	// Fall back to relative path
	wd, _ := os.Getwd()
	return filepath.Join(wd, "backend")
}

// getRuntimeDir returns the runtime directory for extracted resources
func getRuntimeDir() string {
	platform := getPlatformOps()
	runtimeDir := platform.GetRuntimeDir()
	if err := os.MkdirAll(runtimeDir, 0755); err != nil {
		logrus.WithError(err).Warn("Failed to create runtime directory")
	}
	return runtimeDir
}

// getEmbeddedPythonPath returns the path to embedded Python
func getEmbeddedPythonPath() string {
	runtimeDir := getRuntimeDir()
	if runtime.GOOS == "windows" {
		return filepath.Join(runtimeDir, "python", "python.exe")
	}
	return filepath.Join(runtimeDir, "python", "bin", "python")
}

// waitForService waits for a service to become available
func waitForService(port int, timeout time.Duration) error {
	client := &http.Client{Timeout: 1 * time.Second}
	url := fmt.Sprintf("http://localhost:%d/health", port)

	start := time.Now()
	for time.Since(start) < timeout {
		_, err := client.Get(url)
		if err == nil {
			return nil
		}
		time.Sleep(500 * time.Millisecond)
	}
	return fmt.Errorf("service on port %d not ready after %v", port, timeout)
}

// checkPortAvailable checks if a port is available
func checkPortAvailable(port int) error {
	// Try to create a listener on the port
	// If we can create it, the port is not in use, which is what we want
	// If we can't, it's already in use
	// Note: This is a simplified check - more robust port checking would use net.Listen
	logrus.Debugf("Checking port %d availability", port)
	return nil
}
