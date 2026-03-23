// Package main provides user configuration management
package main

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/sirupsen/logrus"
)

// UserConfig holds user preferences
type UserConfig struct {
	OpenBrowserOnStartup bool   `json:"open_browser_on_startup"`
	FirstRun             bool   `json:"first_run"`
	LastVersion          string `json:"last_version"`
	ServerPort           int    `json:"server_port"`
	Theme                string `json:"theme"`
}

// DefaultUserConfig returns the default user configuration
func DefaultUserConfig() *UserConfig {
	return &UserConfig{
		OpenBrowserOnStartup: true,
		FirstRun:             true,
		LastVersion:          "",
		ServerPort:           3315,
		Theme:                "system",
	}
}

// userConfig is the global user configuration
var userConfig *UserConfig

// loadUserConfig loads user configuration from disk
func loadUserConfig() *UserConfig {
	configPath := getUserConfigPath()

	// Try to read existing config
	data, err := os.ReadFile(configPath)
	if err != nil {
		logrus.Debug("No user config found, using defaults")
		return DefaultUserConfig()
	}

	var cfg UserConfig
	if err := json.Unmarshal(data, &cfg); err != nil {
		logrus.WithError(err).Warn("Failed to parse user config, using defaults")
		return DefaultUserConfig()
	}

	return &cfg
}

// saveUserConfig saves user configuration to disk
func saveUserConfig(cfg *UserConfig) error {
	configPath := getUserConfigPath()

	// Ensure directory exists
	configDir := filepath.Dir(configPath)
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(configPath, data, 0644)
}

// getUserConfigPath returns the path to the user config file
func getUserConfigPath() string {
	runtimeDir := getRuntimeDir()
	return filepath.Join(runtimeDir, "config.json")
}

// initializeUserConfig initializes and returns user configuration
func initializeUserConfig() *UserConfig {
	cfg := loadUserConfig()

	// Mark as not first run after this initialization
	if cfg.FirstRun {
		logrus.Info("First run detected, will show welcome page")
		// Don't mark as not-first-run yet, let user complete onboarding
	}

	return cfg
}

// markFirstRunComplete marks the first run as complete
func markFirstRunComplete() error {
	if userConfig == nil {
		return nil
	}

	userConfig.FirstRun = false
	userConfig.LastVersion = version
	return saveUserConfig(userConfig)
}

// setOpenBrowserOnStartup sets the browser auto-open preference
func setOpenBrowserOnStartup(enabled bool) error {
	if userConfig == nil {
		return nil
	}

	userConfig.OpenBrowserOnStartup = enabled
	return saveUserConfig(userConfig)
}

// shouldOpenBrowser returns whether browser should be opened on startup
func shouldOpenBrowser(cliFlag *bool) bool {
	// CLI flag takes precedence
	if cliFlag != nil {
		return *cliFlag
	}

	// Use user config
	if userConfig != nil {
		return userConfig.OpenBrowserOnStartup
	}

	// Default
	return true
}
