//go:build !windows

package wrapper

import "os"

// addProcessToJob is a no-op on non-Windows platforms
// On Unix-like systems, child processes are typically killed when the parent
// is killed, or you can use process groups
func addProcessToJob(process *os.Process) {
	// No-op on non-Windows platforms
}
