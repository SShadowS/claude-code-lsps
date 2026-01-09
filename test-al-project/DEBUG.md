# AL Language Server LSP Debugging

## Goal
Get the AL Language Server plugin working with Claude Code's LSP tool for `.al` files.

## Current Status (2025-12-26)
- Plugin is **enabled** and detected by Claude Code
- LSP Manager registers **0 servers** due to race condition
- **Race condition CONFIRMED** - LSP Manager initializes 8ms before plugins load
- Bug is NOT fixed in current Claude Code version

## Race Condition Evidence

From debug log `9c15d0f4-9a78-4da3-937c-bc0396e70211.txt`:

| Timestamp | Event |
|-----------|-------|
| 23:45:46.901Z | `[LSP MANAGER] initializeLspServerManager() called` |
| 23:45:46.906Z | `LSP notification handlers registered successfully for all 0 server(s)` **<-- TOO EARLY** |
| 23:45:46.914Z | `Loading plugin al-language-server-python from source: "./al-language-server-python"` **<-- 8ms LATE** |
| 23:45:46.916Z | `Found 2 plugins (1 enabled, 1 disabled)` |

**Problem:** LSP Manager completes initialization at `.906Z` with 0 servers, but the plugin with `lspServers` config doesn't load until `.914Z` (8ms later).

## Known Issue
GitHub Issue #13952: LSP race condition bug in Claude Code 2.0.69+
- LSP Manager initializes BEFORE plugins finish loading
- Result: 0 servers registered even though plugin is enabled
- Claimed to be patched but **NOT WORKING** as of 2025-12-26

## Configuration Files

### Plugin Cache (active)
```
C:\Users\SShadowS\.claude\plugins\cache\claude-code-lsps\al-language-server-python\1.0.0\
├── plugin.json     (has lspServers: "./.lsp.json")
└── .lsp.json       (AL LSP config using Python wrapper)
```

### Project Settings
```
U:\Git\claude-code-lsps\test-al-project\.claude\settings.local.json
```
Contains:
```json
{
  "enabledPlugins": {
    "al-language-server-python@claude-code-lsps": true
  }
}
```

---

## How to Test When Fix Ships

### Step 1: Get Latest Debug Log
```bash
ls -lt "c:/Users/SShadowS/.claude/debug/" | head -2
```
Then read the newest log file.

### Step 2: Check Timing Order
Search for these lines and compare timestamps:

```bash
grep -E "(LSP MANAGER|Loading plugin al-language-server-python|LSP notification handlers)" <debug-log-file>
```

**BROKEN (current behavior):**
```
23:45:46.901Z [DEBUG] [LSP MANAGER] initializeLspServerManager() called
23:45:46.906Z [DEBUG] LSP notification handlers registered successfully for all 0 server(s)
23:45:46.914Z [DEBUG] Loading plugin al-language-server-python from source: ...
```

**FIXED (expected behavior):**
```
23:45:46.901Z [DEBUG] Loading plugin al-language-server-python from source: ...
23:45:46.905Z [DEBUG] [LSP MANAGER] initializeLspServerManager() called
23:45:46.910Z [DEBUG] LSP notification handlers registered successfully for all 1 server(s)
```

Key difference: Plugins must load BEFORE `LSP notification handlers registered`.

### Step 3: Verify Server Count
Look for this line:
```
LSP notification handlers registered successfully for all X server(s)
```
- `X = 0` = Bug still present
- `X >= 1` = Fix is working

### Step 4: Test LSP Tool
Run in Claude Code:
```
LSP documentSymbol on src/Codeunits/CustomerMgt.Codeunit.al
```

**BROKEN response:**
```
No LSP server available for file type: .al
```

**WORKING response:**
```
[
  { "name": "CustomerMgt", "kind": "Class", ... },
  { "name": "CreateCustomer", "kind": "Method", ... },
  ...
]
```

### Step 5: Test Other LSP Operations
Once documentSymbol works, test:
```
LSP hover on src/Codeunits/CustomerMgt.Codeunit.al line 10 character 15
LSP goToDefinition on src/Tables/Customer.Table.al line 5 character 10
```

---

## Debug Log Location
```
c:\Users\SShadowS\.claude\debug\
```

## AL LSP Binary
The AL Language Server uses the VS Code AL extension binary:
```
C:\Users\SShadowS\.vscode\extensions\ms-dynamics-smb.al-17.0.1998613\bin\win32\Microsoft.Dynamics.Nav.EditorServices.Host.exe
```

## Quick Verification Commands

```bash
# 1. Find latest debug log
LOG=$(ls -t /c/Users/SShadowS/.claude/debug/*.txt | head -1)

# 2. Check if fix is working (should show 1+ servers)
grep "LSP notification handlers registered" "$LOG"

# 3. Check timing order (plugins should load BEFORE LSP registers)
grep -E "(Loading plugin al-language-server-python|LSP notification handlers)" "$LOG"

# 4. Full LSP-related output
grep -E "(LSP|lspServers|al-language-server)" "$LOG" | head -20
```

## If Still Not Working After Fix Ships
1. Completely exit Claude Code (not just close terminal)
2. Delete the plugin cache and let it reinstall:
   ```bash
   rm -rf "c:/Users/SShadowS/.claude/plugins/cache/claude-code-lsps/al-language-server-python"
   ```
3. Restart Claude Code in this project directory
4. Re-run the verification steps above
