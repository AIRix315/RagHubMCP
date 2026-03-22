// Package main is the entry point for RagHubMCP distributor
// Go + PyInstaller hybrid packaging solution
package main

import (
	"flag"
	"fmt"
	"os"
	"os/signal"
	"runtime"
	"syscall"

	"github.com/sirupsen/logrus"
)

// Build-time variables (injected via -ldflags)
var (
	version   = "dev"
	buildTime = "unknown"
)

// AppConfig holds application configuration
type AppConfig struct {
	Version    string
	BuildTime  string
	Host       string
	Port       int
	RESTPort   int
	MCPPort    int
	WorkingDir string
}

var appConfig *AppConfig

func init() {
	// Initialize logger
	logrus.SetFormatter(&logrus.TextFormatter{
		FullTimestamp: true,
	})
	logrus.SetLevel(logrus.InfoLevel)
}

func main() {
	// Parse command line arguments
	var (
		showVersion = flag.Bool("version", false, "Show version information")
		host        = flag.String("host", "127.0.0.1", "Host to bind to")
		port        = flag.Int("port", 3315, "HTTP server port")
		restPort    = flag.Int("rest-port", 8818, "REST API port")
		mcpPort     = flag.Int("mcp-port", 8819, "MCP HTTP port")
		noBrowser   = flag.Bool("no-browser", false, "Don't open browser automatically")
		noTray      = flag.Bool("no-tray", false, "Don't show system tray (for headless mode)")
		debug       = flag.Bool("debug", false, "Enable debug logging")
	)
	flag.Parse()

	// Show version and exit
	if *showVersion {
		fmt.Printf("RagHubMCP Distributor v%s (built %s)\n", version, buildTime)
		fmt.Printf("Platform: %s/%s\n", runtime.GOOS, runtime.GOARCH)
		os.Exit(0)
	}

	// Set log level
	if *debug {
		logrus.SetLevel(logrus.DebugLevel)
	}

	// Initialize configuration
	appConfig = &AppConfig{
		Version:    version,
		BuildTime:  buildTime,
		Host:       *host,
		Port:       *port,
		RESTPort:   *restPort,
		MCPPort:    *mcpPort,
		WorkingDir: getWorkingDir(),
	}

	// Get remaining arguments for CLI commands
	args := flag.Args()

	// Handle CLI commands
	if len(args) > 0 {
		handleCLICommand(args)
		return
	}

	// Default: Start services
	logrus.Info("================================================")
	logrus.Info("  RagHubMCP - Universal Code RAG Hub")
	logrus.Info("================================================")
	logrus.Infof("Version: %s", version)
	logrus.Infof("Platform: %s/%s", runtime.GOOS, runtime.GOARCH)
	logrus.Infof("Working Directory: %s", appConfig.WorkingDir)

	// Extract embedded resources
	if err := extractResources(); err != nil {
		logrus.WithError(err).Fatal("Failed to extract resources")
	}

	// Start Python backend services
	logrus.Info("Starting Python REST API...")
	if err := startPythonREST(); err != nil {
		logrus.WithError(err).Fatal("Failed to start REST API")
	}

	logrus.Info("Starting Python MCP HTTP...")
	if err := startPythonMCP(); err != nil {
		logrus.WithError(err).Fatal("Failed to start MCP HTTP")
	}

	// Start HTTP proxy server
	logrus.Infof("Starting HTTP proxy on port %d...", *port)
	go startHTTPProxy()

	// Open browser (unless disabled)
	if !*noBrowser {
		go openBrowser(fmt.Sprintf("http://localhost:%d", *port))
	}

	// Start system tray (unless disabled)
	if !*noTray {
		go startTray()
	}

	// Wait for shutdown signal
	waitForShutdown()
}

// getWorkingDir returns the application working directory
func getWorkingDir() string {
	// Use executable directory for packaged app
	if execPath, err := os.Executable(); err == nil {
		return execPath
	}
	// Fall back to current directory
	if cwd, err := os.Getwd(); err == nil {
		return cwd
	}
	return "."
}

// handleCLICommand handles CLI commands
func handleCLICommand(args []string) {
	command := args[0]
	commandArgs := args[1:]

	logrus.Infof("Executing CLI command: %s %v", command, commandArgs)

	switch command {
	case "index":
		runIndexCLI(commandArgs)
	case "search":
		runSearchCLI(commandArgs)
	case "serve":
		// serve is handled as default (no args)
		startServices()
	case "help":
		printCLIHelp()
	default:
		logrus.Errorf("Unknown command: %s", command)
		printCLIHelp()
		os.Exit(1)
	}
}

// startServices starts all services (for CLI serve command)
func startServices() {
	logrus.Info("Starting services...")

	// Extract resources
	if err := extractResources(); err != nil {
		logrus.WithError(err).Fatal("Failed to extract resources")
	}

	// Start Python processes
	if err := startPythonREST(); err != nil {
		logrus.WithError(err).Fatal("Failed to start REST API")
	}

	if err := startPythonMCP(); err != nil {
		logrus.WithError(err).Fatal("Failed to start MCP HTTP")
	}

	// Start HTTP proxy
	go startHTTPProxy()
	go openBrowser(fmt.Sprintf("http://localhost:%d", appConfig.Port))

	waitForShutdown()
}

// printCLIHelp prints CLI help information
func printCLIHelp() {
	fmt.Println("RagHubMCP - Universal Code RAG Hub")
	fmt.Println("")
	fmt.Println("Usage:")
	fmt.Println("  RHM.exe [options]                 Start web service (default)")
	fmt.Println("  RHM.exe serve [options]           Start web service")
	fmt.Println("  RHM.exe index <path> [options]    Index a directory")
	fmt.Println("  RHM.exe search <query> [options]  Search the knowledge base")
	fmt.Println("  RHM.exe --version                 Show version")
	fmt.Println("  RHM.exe --help                    Show this help")
	fmt.Println("")
	fmt.Println("Options:")
	fmt.Println("  --host <host>         Host to bind to (default: 127.0.0.1)")
	fmt.Println("  --port <port>         HTTP port (default: 3315)")
	fmt.Println("  --rest-port <port>    REST API port (default: 8818)")
	fmt.Println("  --mcp-port <port>     MCP HTTP port (default: 8819)")
	fmt.Println("  --no-browser          Don't open browser automatically")
	fmt.Println("  --no-tray             Don't show system tray")
	fmt.Println("  --debug               Enable debug logging")
}

// waitForShutdown waits for shutdown signal
func waitForShutdown() {
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	<-sigChan
	logrus.Info("Shutting down...")

	// Cleanup
	cleanup()
	logrus.Info("Goodbye!")
}

// cleanup performs cleanup on shutdown
func cleanup() {
	stopPythonProcesses()
	cleanupTempResources()
}
