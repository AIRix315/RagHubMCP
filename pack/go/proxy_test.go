// Package main provides HTTP proxy tests
package main

import (
	"net/http"
	"net/url"
	"testing"
)

func TestGetContentType(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"index.html", "text/html; charset=utf-8"},
		{"style.css", "text/css; charset=utf-8"},
		{"script.js", "application/javascript; charset=utf-8"},
		{"data.json", "application/json; charset=utf-8"},
		{"image.png", "image/png"},
		{"image.jpg", "image/jpeg"},
		{"image.jpeg", "image/jpeg"},
		{"image.gif", "image/gif"},
		{"icon.svg", "image/svg+xml"},
		{"favicon.ico", "image/x-icon"},
		{"font.woff", "font/woff"},
		{"font.woff2", "font/woff2"},
		{"font.ttf", "font/ttf"},
		{"unknown.xyz", "application/octet-stream"},
		{"", "application/octet-stream"},
	}

	for _, tt := range tests {
		t.Run(tt.path, func(t *testing.T) {
			result := getContentType(tt.path)
			if result != tt.expected {
				t.Errorf("getContentType(%s) = %s, expected %s", tt.path, result, tt.expected)
			}
		})
	}
}

func TestCreateWebSocketProxy(t *testing.T) {
	target, _ := url.Parse("http://localhost:8818")
	proxy := createWebSocketProxy(target)

	if proxy == nil {
		t.Fatal("createWebSocketProxy returned nil")
	}

	// Verify director is set
	if proxy.Director == nil {
		t.Error("WebSocket proxy director should not be nil")
	}

	// Verify transport is set
	if proxy.Transport == nil {
		t.Error("WebSocket proxy transport should not be nil")
	}
}

func TestProxyServer_CreateTargets(t *testing.T) {
	restTarget, err := url.Parse("http://localhost:8818")
	if err != nil {
		t.Fatalf("Failed to parse REST target: %v", err)
	}

	mcpTarget, err := url.Parse("http://localhost:8819")
	if err != nil {
		t.Fatalf("Failed to parse MCP target: %v", err)
	}

	ps := &ProxyServer{
		RESTTarget: restTarget,
		MCPTarget:  mcpTarget,
	}

	if ps.RESTTarget.Port() != "8818" {
		t.Errorf("Expected REST port 8818, got %s", ps.RESTTarget.Port())
	}

	if ps.MCPTarget.Port() != "8819" {
		t.Errorf("Expected MCP port 8819, got %s", ps.MCPTarget.Port())
	}
}

func TestStopHTTPProxy_NilServer(t *testing.T) {
	// Should not panic when server is nil
	proxyServer = nil
	stopHTTPProxy()
}

func TestStopHTTPProxy_WithServer(t *testing.T) {
	// Create a mock server
	proxyServer = &ProxyServer{
		Server: &http.Server{Addr: ":9999"},
	}

	// Should not panic when calling stop
	// Note: This will try to shut down the server, but since it's not running,
	// it should return quickly
	stopHTTPProxy()
}
