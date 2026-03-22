// Package main provides CLI command handling
package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"time"

	"github.com/sirupsen/logrus"
)

// isServiceRunning checks if a service is running by checking its health endpoint
func isServiceRunning(url string) bool {
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		return false
	}
	defer resp.Body.Close()
	return resp.StatusCode == http.StatusOK
}

// runIndexCLI runs the index CLI command
func runIndexCLI(args []string) {
	logrus.Info("Running index CLI command...")

	// Get paths
	pythonExe := getPythonExecutable()
	backendDir := getBackendDir()

	// Build command
	cmdArgs := []string{"-m", "src.cli.main", "index"}
	cmdArgs = append(cmdArgs, args...)

	cmd := exec.Command(pythonExe, cmdArgs...)
	cmd.Dir = backendDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	// Run command
	if err := cmd.Run(); err != nil {
		logrus.WithError(err).Error("Index command failed")
		os.Exit(1)
	}

	logrus.Info("Index command completed successfully")
}

// runSearchCLI runs the search CLI command
func runSearchCLI(args []string) {
	logrus.Info("Running search CLI command...")

	// Get paths
	pythonExe := getPythonExecutable()
	backendDir := getBackendDir()

	// Build command
	cmdArgs := []string{"-m", "src.cli.main", "query"}
	cmdArgs = append(cmdArgs, args...)

	cmd := exec.Command(pythonExe, cmdArgs...)
	cmd.Dir = backendDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	// Run command
	if err := cmd.Run(); err != nil {
		logrus.WithError(err).Error("Search command failed")
		os.Exit(1)
	}
}

// runProviderCLI runs provider CLI commands
func runProviderCLI(args []string) {
	logrus.Info("Running provider CLI command...")

	if len(args) == 0 {
		fmt.Println("Usage: RHM.exe provider <command> [args]")
		fmt.Println("Commands: list, test, switch")
		os.Exit(1)
	}

	command := args[0]
	cmdArgs := args[1:]

	// Get paths
	pythonExe := getPythonExecutable()
	backendDir := getBackendDir()

	// Build command
	cmdArgs = append([]string{"-m", "src.cli.main", "provider", command}, cmdArgs...)

	cmd := exec.Command(pythonExe, cmdArgs...)
	cmd.Dir = backendDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	// Run command
	if err := cmd.Run(); err != nil {
		logrus.WithError(err).Errorf("Provider %s command failed", command)
		os.Exit(1)
	}
}

// runConfigCLI runs config CLI commands
func runConfigCLI(args []string) {
	logrus.Info("Running config CLI command...")

	if len(args) == 0 {
		fmt.Println("Usage: RHM.exe config <command> [args]")
		fmt.Println("Commands: list, profiles, apply")
		os.Exit(1)
	}

	command := args[0]
	cmdArgs := args[1:]

	// Get paths
	pythonExe := getPythonExecutable()
	backendDir := getBackendDir()

	// Build command
	cmdArgs = append([]string{"-m", "src.cli.main", "config", command}, cmdArgs...)

	cmd := exec.Command(pythonExe, cmdArgs...)
	cmd.Dir = backendDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Stdin = os.Stdin

	// Run command
	if err := cmd.Run(); err != nil {
		logrus.WithError(err).Errorf("Config %s command failed", command)
		os.Exit(1)
	}
}

// runStatusCLI shows service status
func runStatusCLI(args []string) {
	logrus.Info("Checking service status...")

	// Check REST API
	restURL := fmt.Sprintf("http://localhost:%d/health", appConfig.RESTPort)
	if isServiceRunning(restURL) {
		fmt.Printf("✓ REST API running on port %d\n", appConfig.RESTPort)
	} else {
		fmt.Printf("✗ REST API not running on port %d\n", appConfig.RESTPort)
	}

	// Check MCP HTTP
	mcpURL := fmt.Sprintf("http://localhost:%d/health", appConfig.MCPPort)
	if isServiceRunning(mcpURL) {
		fmt.Printf("✓ MCP HTTP running on port %d\n", appConfig.MCPPort)
	} else {
		fmt.Printf("✗ MCP HTTP not running on port %d\n", appConfig.MCPPort)
	}

	// Check frontend
	frontendURL := fmt.Sprintf("http://localhost:%d", appConfig.Port)
	if isServiceRunning(frontendURL) {
		fmt.Printf("✓ Frontend running on port %d\n", appConfig.Port)
	} else {
		fmt.Printf("✗ Frontend not running on port %d\n", appConfig.Port)
	}
}
