// Package main provides HTTP proxy functionality
package main

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"path/filepath"
	"strings"
	"time"

	"github.com/sirupsen/logrus"
)

// ProxyServer handles HTTP proxying to upstream services
type ProxyServer struct {
	RESTTarget *url.URL
	MCPTarget  *url.URL
	Server     *http.Server
}

// proxyServer is the global proxy server instance
var proxyServer *ProxyServer

// startHTTPProxy starts the HTTP proxy server
func startHTTPProxy() {
	// Create target URLs
	restTarget, err := url.Parse(fmt.Sprintf("http://localhost:%d", appConfig.RESTPort))
	if err != nil {
		logrus.WithError(err).Fatal("Failed to parse REST target URL")
	}

	mcpTarget, err := url.Parse(fmt.Sprintf("http://localhost:%d", appConfig.MCPPort))
	if err != nil {
		logrus.WithError(err).Fatal("Failed to parse MCP target URL")
	}

	proxyServer = &ProxyServer{
		RESTTarget: restTarget,
		MCPTarget:  mcpTarget,
	}

	// Create reverse proxies
	restProxy := httputil.NewSingleHostReverseProxy(restTarget)
	mcpProxy := httputil.NewSingleHostReverseProxy(mcpTarget)

	// Configure proxy error handler
	restProxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		logrus.WithError(err).Errorf("REST proxy error for %s", r.URL.Path)
		http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
	}

	mcpProxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
		logrus.WithError(err).Errorf("MCP proxy error for %s", r.URL.Path)
		http.Error(w, "Service unavailable", http.StatusServiceUnavailable)
	}

	// Create WebSocket proxy for /ws/*
	wsProxy := createWebSocketProxy(restTarget)

	// Create main handler
	mux := http.NewServeMux()

	// API routes -> REST API (port 8818)
	mux.HandleFunc("/api/", func(w http.ResponseWriter, r *http.Request) {
		logrus.Debugf("Proxying API request: %s %s", r.Method, r.URL.Path)
		restProxy.ServeHTTP(w, r)
	})

	// Docs routes -> REST API (port 8818)
	mux.HandleFunc("/docs/", func(w http.ResponseWriter, r *http.Request) {
		logrus.Debugf("Proxying docs request: %s %s", r.Method, r.URL.Path)
		restProxy.ServeHTTP(w, r)
	})

	// OpenAPI routes -> REST API (port 8818)
	mux.HandleFunc("/openapi.json", func(w http.ResponseWriter, r *http.Request) {
		logrus.Debugf("Proxying OpenAPI request: %s", r.URL.Path)
		restProxy.ServeHTTP(w, r)
	})

	// Health check -> REST API (port 8818)
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		restProxy.ServeHTTP(w, r)
	})

	// MCP routes -> MCP HTTP (port 8819)
	mux.HandleFunc("/mcp/", func(w http.ResponseWriter, r *http.Request) {
		logrus.Debugf("Proxying MCP request: %s %s", r.Method, r.URL.Path)
		mcpProxy.ServeHTTP(w, r)
	})

	// WebSocket routes -> REST API (port 8818)
	mux.HandleFunc("/ws/", func(w http.ResponseWriter, r *http.Request) {
		logrus.Debugf("Proxying WebSocket request: %s", r.URL.Path)
		wsProxy.ServeHTTP(w, r)
	})

	// Static files (frontend)
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		// Serve static files from embedded frontend
		if r.URL.Path == "/" || r.URL.Path == "/index.html" {
			serveIndexHTML(w, r)
			return
		}
		// Try serving from embedded static files
		serveStaticFile(w, r)
	})

	// Create server
	addr := fmt.Sprintf("%s:%d", appConfig.Host, appConfig.Port)
	proxyServer.Server = &http.Server{
		Addr:         addr,
		Handler:      mux,
		ReadTimeout:  30 * time.Second,
		WriteTimeout: 30 * time.Second,
		IdleTimeout:  120 * time.Second,
	}

	logrus.Infof("HTTP proxy server starting on %s", addr)
	logrus.Info("  /api/*    -> REST API (port 8818)")
	logrus.Info("  /mcp/*    -> MCP HTTP (port 8819)")
	logrus.Info("  /docs/*   -> REST API (port 8818)")
	logrus.Info("  /ws/*     -> WebSocket (port 8818)")
	logrus.Info("  /*        -> Frontend static files")

	if err := proxyServer.Server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		logrus.WithError(err).Fatal("HTTP proxy server error")
	}
}

// createWebSocketProxy creates a WebSocket proxy
func createWebSocketProxy(target *url.URL) *httputil.ReverseProxy {
	proxy := httputil.NewSingleHostReverseProxy(target)

	// Configure director for WebSocket
	proxy.Director = func(req *http.Request) {
		req.URL.Scheme = target.Scheme
		req.URL.Host = target.Host
		req.URL.Path = req.URL.Path

		// Set WebSocket headers
		req.Header.Set("X-Forwarded-Host", req.Host)
		req.Header.Set("X-Forwarded-Proto", "http")
	}

	// Configure transport for WebSocket
	proxy.Transport = &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   30 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		MaxIdleConns:          100,
		IdleConnTimeout:       90 * time.Second,
		TLSHandshakeTimeout:   10 * time.Second,
		ExpectContinueTimeout: 1 * time.Second,
	}

	return proxy
}

// serveIndexHTML serves the index.html file
func serveIndexHTML(w http.ResponseWriter, r *http.Request) {
	content, err := getEmbeddedFile("frontend/dist/index.html")
	if err != nil {
		logrus.WithError(err).Error("Failed to serve index.html")
		http.Error(w, "Internal server error", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write(content)
}

// serveStaticFile serves static files from embedded resources
func serveStaticFile(w http.ResponseWriter, r *http.Request) {
	// Remove leading slash
	path := strings.TrimPrefix(r.URL.Path, "/")

	// Try to get the file from embedded resources
	content, err := getEmbeddedFile("frontend/dist/" + path)
	if err != nil {
		// If file not found, serve index.html (for SPA routing)
		if strings.Contains(r.URL.Path, ".") {
			logrus.Debugf("File not found: %s", path)
			http.NotFound(w, r)
			return
		}
		// SPA fallback to index.html
		serveIndexHTML(w, r)
		return
	}

	// Set content type based on file extension
	contentType := getContentType(path)
	w.Header().Set("Content-Type", contentType)
	w.Write(content)
}

// getContentType returns the content type for a file path
func getContentType(path string) string {
	ext := strings.ToLower(filepath.Ext(path))
	switch ext {
	case ".html":
		return "text/html; charset=utf-8"
	case ".css":
		return "text/css; charset=utf-8"
	case ".js":
		return "application/javascript; charset=utf-8"
	case ".json":
		return "application/json; charset=utf-8"
	case ".png":
		return "image/png"
	case ".jpg", ".jpeg":
		return "image/jpeg"
	case ".gif":
		return "image/gif"
	case ".svg":
		return "image/svg+xml"
	case ".ico":
		return "image/x-icon"
	case ".woff":
		return "font/woff"
	case ".woff2":
		return "font/woff2"
	case ".ttf":
		return "font/ttf"
	default:
		return "application/octet-stream"
	}
}

// stopHTTPProxy stops the HTTP proxy server
func stopHTTPProxy() {
	if proxyServer != nil && proxyServer.Server != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		if err := proxyServer.Server.Shutdown(ctx); err != nil {
			logrus.WithError(err).Warn("Error stopping HTTP proxy server")
		}
	}
}
