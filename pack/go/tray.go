// Package main provides system tray functionality
package main

import (
	"embed"
	"fmt"
	"runtime"

	"github.com/getlantern/systray"
	"github.com/sirupsen/logrus"
)

// Embed icon files for all platforms
//
//go:embed icons/*.png icons/*.ico icon.png
var iconFS embed.FS

// startTray starts the system tray
func startTray() {
	logrus.Info("Starting system tray...")

	systray.Run(onReady, onExit)
}

// onReady is called when the systray is ready
func onReady() {
	// Set tray icon based on platform
	iconData := getPlatformIcon()
	systray.SetIcon(iconData)
	systray.SetTitle("RagHubMCP")
	systray.SetTooltip(fmt.Sprintf("RagHubMCP v%s", appConfig.Version))

	// Add menu items
	mOpen := systray.AddMenuItem("Open Browser", "Open web interface")
	mStatus := systray.AddMenuItem("Status: Running", "Service status")
	mStatus.Disable()
	systray.AddSeparator()

	mAbout := systray.AddMenuItem("About", "About RagHubMCP")
	systray.AddSeparator()

	mQuit := systray.AddMenuItem("Quit", "Exit application")

	// Handle menu clicks
	go func() {
		for {
			select {
			case <-mOpen.ClickedCh:
				openBrowser(fmt.Sprintf("http://localhost:%d", appConfig.Port))
			case <-mAbout.ClickedCh:
				showAboutDialog()
			case <-mQuit.ClickedCh:
				systray.Quit()
			}
		}
	}()

	logrus.Info("System tray started")
}

// onExit is called when the systray exits
func onExit() {
	logrus.Info("System tray exiting...")

	// Stop all Python processes before exiting
	stopPythonProcesses()

	// Clean up temporary resources
	cleanupTempResources()

	logrus.Info("All services stopped, goodbye!")
}

// getPlatformIcon returns the appropriate icon for the current platform
// Windows: ICO format preferred
// macOS: PNG 64x64 (retina-friendly)
// Linux: PNG 32x32 (standard tray size)
func getPlatformIcon() []byte {
	var iconPath string

	switch runtime.GOOS {
	case "windows":
		// Windows prefers ICO format with multiple resolutions
		iconPath = "icons/icon.ico"
	case "darwin":
		// macOS uses larger icons for Retina displays
		iconPath = "icons/icon_64.png"
	default:
		// Linux and others use standard tray size
		iconPath = "icons/icon_32.png"
	}

	// Try to load platform-specific icon
	data, err := iconFS.ReadFile(iconPath)
	if err == nil {
		logrus.Debugf("Loaded platform icon: %s (%d bytes)", iconPath, len(data))
		return data
	}

	// Fallback: try the default icon.png in root
	data, err = iconFS.ReadFile("icon.png")
	if err == nil {
		logrus.Debug("Loaded fallback icon.png")
		return data
	}

	logrus.WithError(err).Warn("Failed to load any icon, using embedded default")
	return getDefaultIcon()
}

// getDefaultIcon returns a minimal default icon (16x16 blue square)
// This is only used if all icon loading fails
func getDefaultIcon() []byte {
	// Minimal 16x16 PNG icon (blue square)
	return []byte{
		0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
		0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x10,
		0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x91, 0x68, 0x36, 0x00, 0x00, 0x00,
		0x19, 0x49, 0x44, 0x41, 0x54, 0x08, 0xD7, 0x63, 0x60, 0x60, 0xF8, 0x0F,
		0x3B, 0x82, 0xF6, 0xFF, 0xFF, 0x3B, 0x82, 0xF6, 0x0F, 0x0F, 0x0F, 0x0F,
		0x00, 0x05, 0xFE, 0x02, 0xFE, 0xEC, 0x33, 0x37, 0x00, 0x00, 0x00, 0x00,
		0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
	}
}

// showAboutDialog shows the about dialog
func showAboutDialog() {
	// On GUI platforms, we could show a dialog
	// For now, we log the information
	logrus.Info("=== About RagHubMCP ===")
	logrus.Infof("Version: %s", appConfig.Version)
	logrus.Infof("Build Time: %s", appConfig.BuildTime)
	logrus.Info("Universal Code RAG Hub")
	logrus.Info("REST API: localhost:", appConfig.RESTPort)
	logrus.Info("MCP HTTP: localhost:", appConfig.MCPPort)
	logrus.Info("Web UI: localhost:", appConfig.Port)
}

// updateTrayStatus updates the tray status (for future use)
func updateTrayStatus(status string) {
	// This function could be used to update the tray icon or menu
	// based on service status
	logrus.Debugf("Tray status: %s", status)
}
