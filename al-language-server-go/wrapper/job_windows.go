//go:build windows

package wrapper

import (
	"os"
	"syscall"
	"unsafe"
)

var (
	kernel32                  = syscall.NewLazyDLL("kernel32.dll")
	procCreateJobObject       = kernel32.NewProc("CreateJobObjectW")
	procSetInformationJobObj  = kernel32.NewProc("SetInformationJobObject")
	procAssignProcessToJobObj = kernel32.NewProc("AssignProcessToJobObject")
	procOpenProcess           = kernel32.NewProc("OpenProcess")
	procCloseHandle           = kernel32.NewProc("CloseHandle")
)

const (
	jobObjectExtendedLimitInformationClass = 9
	jobObjectLimitKillOnJobClose           = 0x2000
	processAllAccess                       = 0x1F0FFF
)

// JOBOBJECT_BASIC_LIMIT_INFORMATION structure
type jobObjectBasicLimitInformation struct {
	PerProcessUserTimeLimit int64
	PerJobUserTimeLimit     int64
	LimitFlags              uint32
	MinimumWorkingSetSize   uintptr
	MaximumWorkingSetSize   uintptr
	ActiveProcessLimit      uint32
	Affinity                uintptr
	PriorityClass           uint32
	SchedulingClass         uint32
}

// IO_COUNTERS structure
type ioCounters struct {
	ReadOperationCount  uint64
	WriteOperationCount uint64
	OtherOperationCount uint64
	ReadTransferCount   uint64
	WriteTransferCount  uint64
	OtherTransferCount  uint64
}

// JOBOBJECT_EXTENDED_LIMIT_INFORMATION structure
type jobObjectExtendedLimitInformation struct {
	BasicLimitInformation jobObjectBasicLimitInformation
	IoInfo                ioCounters
	ProcessMemoryLimit    uintptr
	JobMemoryLimit        uintptr
	PeakProcessMemoryUsed uintptr
	PeakJobMemoryUsed     uintptr
}

// jobHandle holds the Windows Job Object handle
var jobHandle syscall.Handle

// initJobObject creates a Windows Job Object that terminates all child processes
// when the parent process exits
func initJobObject() {
	handle, _, _ := procCreateJobObject.Call(0, 0)
	if handle == 0 {
		return
	}
	jobHandle = syscall.Handle(handle)

	// Set the job to terminate all processes when the handle is closed
	info := jobObjectExtendedLimitInformation{}
	info.BasicLimitInformation.LimitFlags = jobObjectLimitKillOnJobClose

	procSetInformationJobObj.Call(
		uintptr(jobHandle),
		jobObjectExtendedLimitInformationClass,
		uintptr(unsafe.Pointer(&info)),
		uintptr(unsafe.Sizeof(info)),
	)
}

// addProcessToJob adds a process to the Windows Job Object
func addProcessToJob(process *os.Process) {
	if jobHandle == 0 || process == nil {
		return
	}

	// Get process handle
	handle, _, _ := procOpenProcess.Call(processAllAccess, 0, uintptr(process.Pid))
	if handle == 0 {
		return
	}
	defer procCloseHandle.Call(handle)

	// Add to job
	procAssignProcessToJobObj.Call(uintptr(jobHandle), handle)
}

func init() {
	initJobObject()
}
