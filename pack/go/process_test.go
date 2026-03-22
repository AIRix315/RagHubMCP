// Package main provides process management tests
package main

import (
	"os/exec"
	"testing"
)

func TestProcessManager_Init(t *testing.T) {
	pm := &ProcessManager{
		processes: make(map[string]*exec.Cmd),
	}

	if pm.processes == nil {
		t.Error("processes map should be initialized")
	}
}

func TestProcessManager_ConcurrentAccess(t *testing.T) {
	pm := &ProcessManager{
		processes: make(map[string]*exec.Cmd),
	}

	// Test concurrent read/write
	done := make(chan bool)

	// Writer goroutine
	go func() {
		for i := 0; i < 100; i++ {
			pm.mu.Lock()
			pm.processes["test"] = nil
			pm.mu.Unlock()
		}
		done <- true
	}()

	// Reader goroutine
	go func() {
		for i := 0; i < 100; i++ {
			pm.mu.RLock()
			_ = pm.processes["test"]
			pm.mu.RUnlock()
		}
		done <- true
	}()

	// Wait for both goroutines
	<-done
	<-done
}

func TestGetPythonExecutable(t *testing.T) {
	exe := getPythonExecutable()

	if exe == "" {
		t.Error("getPythonExecutable returned empty string")
	}

	// On Windows, should contain ".exe"
	// On Unix, should be "python3" or "python"
	// This depends on system Python availability
}

func TestGetBackendDir(t *testing.T) {
	dir := getBackendDir()

	if dir == "" {
		t.Error("getBackendDir returned empty string")
	}
}

func TestGetRuntimeDirProcess(t *testing.T) {
	dir := getRuntimeDir()

	if dir == "" {
		t.Error("getRuntimeDir returned empty string")
	}
}

func TestGetEmbeddedPythonPath(t *testing.T) {
	path := getEmbeddedPythonPath()

	if path == "" {
		t.Error("getEmbeddedPythonPath returned empty string")
	}
}

func TestCheckPortAvailable(t *testing.T) {
	// This function currently just logs and returns nil
	err := checkPortAvailable(8818)
	if err != nil {
		t.Errorf("checkPortAvailable returned error: %v", err)
	}
}

func TestProcessManager_CleanupEmptyMap(t *testing.T) {
	// Should not panic with empty map
	stopPythonProcesses()
}
