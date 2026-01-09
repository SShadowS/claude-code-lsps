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

- `goToDefinition` - Go to symbol definition
- `goToImplementation` - Go to implementation
- `hover` - Get type/documentation info
- `documentSymbol` - List symbols in file
- `findReferences` - Find all references
- `workspaceSymbol` - Search symbols across workspace
- `prepareCallHierarchy` - Get call hierarchy
- `incomingCalls` - Find callers
- `outgoingCalls` - Find callees

## License

MIT
