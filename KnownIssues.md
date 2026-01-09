# Known Issues

## workspaceSymbol Returns Empty Results

**Status:** Claude Code LSP tool bug
**Reported:** https://github.com/anthropics/claude-code/issues

### Problem

The `workspaceSymbol` LSP operation always returns 0 symbols when called through Claude Code's LSP tool.

### Root Cause

Claude Code's LSP tool sends an empty query parameter:

```json
{"query": ""}
```

The `workspaceSymbol` operation requires a search term (e.g., "Customer", "Sales") to find symbols across the workspace. Without a query, no symbols can be matched.

### Technical Details

**What Claude Code sends:**
```
DEBUG params: {'query': ''}
Workspace symbol query: ''
```

**What it should send:**
```
DEBUG params: {'query': 'Customer'}
Workspace symbol query: 'Customer'
```

The LSP tool interface is designed for file+position operations (filePath, line, character), which work correctly for:
- `findReferences` - find usages at a position
- `goToDefinition` - jump to definition at a position
- `documentSymbol` - list symbols in a file
- `hover` - get info at a position

However, `workspaceSymbol` needs a search query string parameter, which isn't exposed in Claude Code's current LSP tool interface.

### Wrapper Mitigations

The AL LSP wrapper includes these mitigations:

1. **Helpful error message** - When query is empty, returns an error explaining the bug and suggesting workarounds

2. **File path extraction** - If Claude Code passes a file path as query (observed in some cases), the wrapper extracts the symbol name:
   - `Table 6175301 CDO File.al` → searches for `"CDO File"`
   - `Codeunit 123 MyCodeunit.al` → searches for `"MyCodeunit"`

3. **Fallback to al/symbolSearch** - Tries AL-specific symbol search if standard `workspace/symbol` returns no results

### Workarounds

Until Claude Code fixes the LSP tool:

1. **Use documentSymbol** - Lists all symbols in a specific file (works correctly)
   ```
   LSP(operation: "documentSymbol", file: "path/to/file.al")
   ```

2. **Use Grep** - Search for symbol names across the workspace
   ```
   Grep(pattern: "procedure.*CustomerName", path: "src/")
   ```

3. **Use findReferences** - Find all usages of a symbol at a known location
   ```
   LSP(operation: "findReferences", file: "...", line: X, character: Y)
   ```

### Testing

The wrapper's test script confirms `workspaceSymbol` works when given a proper query:

```
Test: Query = 'CDO'
  Result: 509 symbols

Test: Query = ''
  Result: Error (as expected)
```

### Version History

- **v1.2.0** - Added `handle_workspace_symbol` with project initialization
- **v1.2.2** - Fixed null result handling
- **v1.2.3** - Added file path to query extraction
- **v1.2.4** - Added helpful error message for empty query
