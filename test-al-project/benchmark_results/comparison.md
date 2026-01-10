# Call Hierarchy Benchmark Comparison

Generated: 2026-01-10T22:14:56.427366

## Summary

| Label | Init (ms) | Files | Timestamp |
|-------|-----------|-------|----------|
| baseline | 3009 | 17547 | 2026-01-10T21:52:28 |
| optimized_final | 3008 | 17547 | 2026-01-10T22:14:52 |
| optimized_v1 | 3106 | 17547 | 2026-01-10T22:00:05 |
| thread_local_parser | 3109 | 17547 | 2026-01-10T22:06:54 |

## Detailed Results


### baseline

| File | Operation | Avg (ms) | Min | Max |
|------|-----------|----------|-----|-----|
| ManualSetupManagement.Codeunit | prepareCallHierarchy | 54177.7 | 27.6 | 270766.2 |
| SalesPostPrepayments.Codeunit. | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
| CaptionClassImpl.Codeunit.al | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
| DocumentErrorsMgt.Codeunit.al | prepareCallHierarchy | 0.1 | 0.1 | 0.1 |

### optimized_final

| File | Operation | Avg (ms) | Min | Max |
|------|-----------|----------|-----|-----|
| ManualSetupManagement.Codeunit | prepareCallHierarchy | 178.5 | 0.1 | 891.9 |
| SalesPostPrepayments.Codeunit. | prepareCallHierarchy | 0.1 | 0.1 | 0.1 |
| CaptionClassImpl.Codeunit.al | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
| DocumentErrorsMgt.Codeunit.al | prepareCallHierarchy | 0.1 | 0.1 | 0.1 |

### optimized_v1

| File | Operation | Avg (ms) | Min | Max |
|------|-----------|----------|-----|-----|
| ManualSetupManagement.Codeunit | prepareCallHierarchy | 54112.9 | 0.0 | 270564.4 |
| SalesPostPrepayments.Codeunit. | prepareCallHierarchy | 0.1 | 0.1 | 0.2 |
| CaptionClassImpl.Codeunit.al | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
| DocumentErrorsMgt.Codeunit.al | prepareCallHierarchy | 0.1 | 0.1 | 0.1 |

### thread_local_parser

| File | Operation | Avg (ms) | Min | Max |
|------|-----------|----------|-----|-----|
| ManualSetupManagement.Codeunit | prepareCallHierarchy | 25078.3 | 0.1 | 125390.8 |
| SalesPostPrepayments.Codeunit. | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
| CaptionClassImpl.Codeunit.al | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
| DocumentErrorsMgt.Codeunit.al | prepareCallHierarchy | 0.1 | 0.0 | 0.1 |
