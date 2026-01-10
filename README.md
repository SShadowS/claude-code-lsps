# AL LSP Wrappers for Claude Code

Claude Code marketplace providing AL Language Server wrappers for Business Central development.

## Available Wrappers

| Wrapper | Runtime | Description |
|---------|---------|-------------|
| `al-language-server-python` | Python 3.10+ | Python wrapper for MS AL Language Server |

*Future: Go-compiled binaries for faster startup and no runtime dependencies*

## Features

- **Hover** - Type information and documentation
- **Go to Definition** - Jump to symbol definitions (tables, codeunits, enums, procedures)
- **Document Symbols** - List all symbols in a file
- **Find References** - Find all references to a symbol
- **Call Hierarchy** - Find incoming and outgoing calls for procedures
- **Multi-project support** - Workspaces with multiple AL apps

## Prerequisites

1. **VS Code** with the [AL Language extension](https://marketplace.visualstudio.com/items?itemName=ms-dynamics-smb.al) installed
2. **Python 3.10+** in your PATH (for the Python wrapper)

The wrapper automatically finds the newest AL extension version in your VS Code extensions folder.

## Installation

### 1. Enable LSP Tool

```powershell
# PowerShell (current session)
$env:ENABLE_LSP_TOOL = "1"
claude

# PowerShell (permanent)
[Environment]::SetEnvironmentVariable("ENABLE_LSP_TOOL", "1", "User")
```

```bash
# Bash
export ENABLE_LSP_TOOL=1
claude
```

### 2. Add Marketplace

```
/plugin marketplace add SShadowS/claude-code-lsps
```

### 3. Install Plugin

1. Type `/plugins`
2. Tab to `Marketplaces`
3. Enter `al-lsp-wrappers` marketplace
4. Select `al-language-server-python` with spacebar
5. Press "i" to install
6. Restart Claude Code

## LSP Operations

Claude can use these LSP operations on AL files:

| Operation | Status | Description |
|-----------|--------|-------------|
| `goToDefinition` | Working | Go to symbol definition |
| `goToImplementation` | Working | Go to implementation |
| `hover` | Working | Get type/documentation info |
| `documentSymbol` | Working | List symbols in file |
| `findReferences` | Working | Find all references |
| `prepareCallHierarchy` | Working | Get call hierarchy item at position |
| `incomingCalls` | Working | Find callers of a procedure |
| `outgoingCalls` | Working | Find calls made by a procedure |
| `workspaceSymbol` | Bug | See [Known Issues](KnownIssues.md) |

## Known Issues

### workspaceSymbol Returns Empty Results

Claude Code's LSP tool has a bug where it doesn't pass the required `query` parameter for `workspaceSymbol`. This causes the operation to always return 0 symbols.

**Workarounds:**
- Use `documentSymbol` to list symbols in a specific file
- Use `Grep` to search for symbol names across the workspace

See [KnownIssues.md](KnownIssues.md) for full details and technical analysis.

## License

MIT
