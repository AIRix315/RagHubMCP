// Package main provides browser opening functionality
package main

import (
	"fmt"

	"github.com/sirupsen/logrus"
)

// openBrowser opens the URL in the default browser
func openBrowser(url string) error {
	logrus.Infof("Opening browser: %s", url)

	platform := getPlatformOps()
	if err := platform.OpenBrowser(url); err != nil {
		logrus.WithError(err).Warn("Failed to open browser automatically")
		return err
	}

	return nil
}

// openBrowserWithFallback opens the browser, with fallback instructions
func openBrowserWithFallback(url string) {
	if err := openBrowser(url); err != nil {
		// Print instructions for manual opening
		fmt.Printf("\n========================================\n")
		fmt.Printf("Please open your browser to:\n")
		fmt.Printf("  %s\n", url)
		fmt.Printf("========================================\n\n")
	}
}
