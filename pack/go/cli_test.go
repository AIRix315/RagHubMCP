// Package main provides CLI command tests
package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestIsServiceRunning_WhenRunning(t *testing.T) {
	// Create a test server
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/health" {
			w.WriteHeader(http.StatusOK)
			return
		}
		w.WriteHeader(http.StatusNotFound)
	}))
	defer server.Close()

	// Test the function
	result := isServiceRunning(server.URL + "/health")
	if !result {
		t.Error("Expected isServiceRunning to return true for running service")
	}
}

func TestIsServiceRunning_WhenNotRunning(t *testing.T) {
	// Test with a non-existent URL
	result := isServiceRunning("http://localhost:59999/health")
	if result {
		t.Error("Expected isServiceRunning to return false for non-existent service")
	}
}

func TestIsServiceRunning_Timeout(t *testing.T) {
	// Create a server that delays response
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		time.Sleep(3 * time.Second) // Longer than client timeout
		w.WriteHeader(http.StatusOK)
	}))
	defer server.Close()

	// Should timeout and return false
	result := isServiceRunning(server.URL + "/health")
	if result {
		t.Error("Expected isServiceRunning to return false on timeout")
	}
}

func TestIsServiceRunning_ReturnsNonOK(t *testing.T) {
	// Create a server that returns 500
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusInternalServerError)
	}))
	defer server.Close()

	// Current implementation returns false for non-200
	result := isServiceRunning(server.URL + "/health")
	if result {
		t.Error("Expected isServiceRunning to return false for non-200 status")
	}
}

func TestRunStatusCLI(t *testing.T) {
	// Create test config
	appConfig = &AppConfig{
		Version:    "test",
		BuildTime:  "2024-01-01",
		Host:       "127.0.0.1",
		Port:       3315,
		RESTPort:   8818,
		MCPPort:    8819,
		WorkingDir: ".",
	}

	// This function outputs to stdout, so we just verify it doesn't panic
	// In a real test, we'd capture stdout
	runStatusCLI([]string{})
}

func TestPrintCLIHelp(t *testing.T) {
	// Verify function doesn't panic
	printCLIHelp()
}
