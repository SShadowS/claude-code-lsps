// Launcher finds and executes the AL LSP wrapper from the plugin cache.
// This allows .lsp.json to point to a fixed path without external dependencies.
package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"syscall"
)

func main() {
	wrapper, err := findWrapper()
	if err != nil {
		fmt.Fprintf(os.Stderr, "AL LSP Launcher: %v\n", err)
		os.Exit(1)
	}

	// Execute the wrapper, replacing this process
	if err := execWrapper(wrapper); err != nil {
		fmt.Fprintf(os.Stderr, "AL LSP Launcher: failed to execute wrapper: %v\n", err)
		os.Exit(1)
	}
}

func getWrapperName() string {
	if runtime.GOOS == "windows" {
		return "al-lsp-wrapper.exe"
	}
	return "al-lsp-wrapper"
}

func findWrapper() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to get home directory: %w", err)
	}

	// Look for wrapper in plugin cache (platform-specific binary name)
	wrapperName := getWrapperName()
	pattern := filepath.Join(home, ".claude", "plugins", "cache",
		"al-lsp-wrappers", "al-language-server-go", "*", "bin", wrapperName)

	matches, err := filepath.Glob(pattern)
	if err != nil {
		return "", fmt.Errorf("failed to search for wrapper: %w", err)
	}

	if len(matches) == 0 {
		return "", fmt.Errorf("wrapper not found at %s", pattern)
	}

	// Sort to get newest version (lexicographic sort works for semver)
	sort.Sort(sort.Reverse(sort.StringSlice(matches)))

	return matches[0], nil
}

func execWrapper(path string) error {
	if runtime.GOOS != "windows" {
		// On Unix, replace this process entirely with syscall.Exec
		return syscall.Exec(path, []string{path}, os.Environ())
	}

	// On Windows, we can't use syscall.Exec, so spawn and wait
	cmd := exec.Command(path)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr

	err := cmd.Run()
	if err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		return err
	}

	os.Exit(0)
	return nil
}
